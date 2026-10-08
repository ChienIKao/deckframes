import json
from pathlib import Path

from deckframes.check import check
from deckframes.cli import main
from deckframes.frame_import import import_frame
from deckframes.markdown import parse_markdown

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "demo.md"

FRAME = """---
name: test
colors:
  paper: "#F7F3EA"
  ink: "#151515"
  tomato: "#E4572E"
  teal: "#17BEBB"
  sun: "#FFC914"
borders: { primary: "4px solid black" }
shadows: { default: "8px 8px 0 black" }
typography:
  body:     { fontFamily: "Inter", cqw: 1.0 }
  headline:{ fontFamily: "Playfair Display", cqw: 5.0 }
---
"""


def test_hierarchy():
    doc = parse_markdown(DEMO.read_text(encoding="utf-8"))
    chapters = [s for s in doc.sections if s.title]
    assert len(chapters) == 4
    assert chapters[0].subtitle == "Introduction"
    assert chapters[0].subsections[0].slides[0].title == "消費習慣的轉變"
    kinds = {b.kind for s in chapters[0].subsections[0].slides for b in s.blocks}
    assert {"component", "source", "bullets"} <= kinds


def test_build_and_check(tmp_path):
    out = tmp_path / "demo.pptx"
    main(["build", str(DEMO), "-o", str(out)])
    report = check(out)
    assert report["slides"] >= 18
    assert report["ok"], json.dumps(report["pages"], ensure_ascii=False)[:500]


def test_canvas_master_is_widescreen(tmp_path):
    from pptx import Presentation
    out = tmp_path / "demo.pptx"
    main(["build", str(DEMO), "-o", str(out)])
    prs = Presentation(str(out))
    title = prs.slide_master.placeholders[0]
    # default python-pptx master is 4:3; its placeholders must be stretched to the 16:9 slide
    assert title.left + title.width > prs.slide_width * 0.9


def test_template_engine(tmp_path):
    out = tmp_path / "plain.pptx"
    main(["build", str(DEMO), "-o", str(out), "--theme", "default"])
    assert check(out)["slides"] > 10


def test_frame_import(tmp_path):
    f = tmp_path / "FRAME.md"
    f.write_text(FRAME, encoding="utf-8")
    theme, _ = import_frame(f, "t")
    c = theme["colors"]
    assert c["ground"] == "F7F3EA" and c["text"] == "151515"
    assert set(c["palette"]) == {"E4572E", "17BEBB", "FFC914"}
    assert theme["decorations"] and theme["stroke"]["shadow"] == 4
    assert theme["fonts"]["display"] == "Georgia"
    tfile = tmp_path / "t.json"
    tfile.write_text(json.dumps(theme), encoding="utf-8")
    out = tmp_path / "t.pptx"
    main(["build", str(DEMO), "-o", str(out), "--theme", str(tfile)])
    assert check(out)["ok"]


def test_project_flow(tmp_path, monkeypatch):
    proj = tmp_path / "p"
    main(["init", str(proj), "--from", str(DEMO)])
    assert (proj / "deck.json").exists() and (proj / "AGENTS.md").exists()
    monkeypatch.chdir(proj)
    main(["build"])
    state = json.loads((proj / "deck.json").read_text(encoding="utf-8"))
    assert state["status"]["built"]
    assert (proj / state["output"]).exists()


def test_themes_new(tmp_path):
    from deckframes.themes import new_theme
    path = new_theme("my-lab", dest=tmp_path / "my-lab.json")
    theme = json.loads(path.read_text(encoding="utf-8"))
    assert theme["name"] == "my-lab" and theme["based_on"] == "blockframe" and theme["engine"] == "canvas"
    theme["colors"]["palette"] = ["1B998B", "ED217C", "FFFD82"]
    path.write_text(json.dumps(theme), encoding="utf-8")
    out = tmp_path / "t.pptx"
    main(["build", str(DEMO), "-o", str(out), "--theme", str(path)])
    assert check(out)["ok"]


def test_item_colon_and_workflow_alias(tmp_path):
    from deckframes.markdown import make_item
    assert make_item("空間老舊： | 座位不足")["title"] == "空間老舊"
    assert make_item("比例：3:1")["title"] == "比例：3:1"
    main(["init", str(tmp_path / "w"), "--workflow", "general"])
    state = json.loads((tmp_path / "w" / "deck.json").read_text(encoding="utf-8"))
    assert state["workflow"] == "deckframes-general"


def test_emoji_rejected(tmp_path):
    import pytest
    from deckframes.markdown import find_emoji
    assert [c for _, _, c in find_emoji("成果 \U0001F389 完成 \u2705 ok")] == ["\U0001F389", "\u2705"]
    assert find_emoji("✓ ✗ ○ × → ★ ■ – 3×") == []          # typographic symbols stay allowed
    assert [c for _, _, c in find_emoji("警告 \u26A0\uFE0F")] == ["⚠"]  # text symbol + VS16 = emoji
    deck = tmp_path / "e.md"
    deck.write_text("# 標題\n\n## 章 | Ch\n\n### 節\n\n- 重點 \U0001F680\n", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        main(["build", str(deck), "-o", str(tmp_path / "e.pptx")])
    assert e.value.code == 2 and not (tmp_path / "e.pptx").exists()


def test_check_flags_emoji_in_pptx(tmp_path):
    from pptx import Presentation
    from pptx.util import Inches
    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1)).text_frame.text = "Launch \U0001F680"
    out = tmp_path / "x.pptx"
    prs.save(out)
    issues = check(out)["pages"][0]["issues"]
    assert any(i["type"] == "emoji" for i in issues)


def test_icon_refs():
    from deckframes.icons import parse_ref
    assert parse_ref("users") == ("fa", None, "users")
    assert parse_ref("fa-solid fa-users") == ("fa", "solid", "users")
    assert parse_ref("regular:clock") == ("fa", "regular", "clock")
    assert parse_ref("brands:github") == ("fa", "brands", "github")
    assert parse_ref("assets/logo.svg") == ("file", "assets/logo.svg")
    assert parse_ref("?")[0] == "text" and parse_ref("AI")[0] == "text"


def test_svg_embedded_as_vector(tmp_path):
    import zipfile
    out = tmp_path / "d.pptx"
    main(["build", str(DEMO), "-o", str(out)])
    z = zipfile.ZipFile(out)
    assert any(n.endswith(".svg") for n in z.namelist())
    assert "image/svg+xml" in z.read("[Content_Types].xml").decode()


def _image_layout(tmp_path, size, body, title="#### 截圖 | 一句話說明這張圖"):
    from PIL import Image
    from deckframes.engines.canvas import Canvas
    from deckframes.markdown import parse_markdown
    from deckframes.themes import resolve_theme
    Image.new("RGB", size, "white").save(tmp_path / "img.png")
    doc = parse_markdown(f"# T\n\n## 章 | Ch\n\n### 節\n\n{title}\n\n{body}\n")
    theme, _ = resolve_theme("blockframe")
    c = Canvas(theme, doc.meta, tmp_path)
    c.chapters = [s for s in doc.sections if s.title]
    sl = doc.sections[0].subsections[0].slides[0]
    from deckframes.engines.canvas import Page
    pg = Page("content", title=sl.title, subtitle=sl.subtitle, chapter=0, sub=0, blocks=sl.blocks)
    text, vis, callouts, sources = c.split_blocks(pg.blocks)
    return c.layout(pg, c.text_paras(text), vis, callouts, bool(sources))


def test_portrait_image_becomes_showcase(tmp_path):
    lay = _image_layout(tmp_path, (650, 1080), "![](img.png)")
    assert lay["mode"] == "showcase"
    assert lay["visual"][3] > 5.0                      # image column spans (almost) the full height


def test_text_and_image_split_follows_aspect(tmp_path):
    wide = _image_layout(tmp_path, (1754, 1241), "- 一點\n- 兩點\n\n![](img.png)")
    tall = _image_layout(tmp_path, (650, 1080), "- 一點\n- 兩點\n\n![](img.png)")
    assert wide["mode"] == tall["mode"] == "split"
    assert wide["visual"][2] > tall["visual"][2]       # landscape image gets the wider column
    left = _image_layout(tmp_path, (1754, 1241), '- 一點\n\n![](img.png "left")')
    assert left["visual"][0] < left["text"][0]         # "left" puts the image first


COMPONENTS = ROOT / "examples" / "components.md"


def test_new_components_parse():
    doc = parse_markdown(COMPONENTS.read_text(encoding="utf-8"))
    from deckframes.lint import content_slides, slide_pattern

    used = {slide_pattern(sl.blocks) for sl in content_slides(doc)}
    assert {"lanes", "diagram", "mapping", "stack", "matrix", "funnel", "pyramid", "cycle", "progress"} <= used


def test_components_render_on_many_themes(tmp_path):
    for theme in ["academic", "claymorphism", "cybercore", "glassmorphism", "swiss", "victorian", "pixel-art"]:
        out = tmp_path / f"{theme}.pptx"
        try:
            main(["build", str(COMPONENTS), "--theme", theme, "-o", str(out)])
        except SystemExit as e:
            assert not e.code
        report = check(out)
        assert report["ok"], (theme, report["issues"][:3])


def test_builtin_themes_have_distinct_styles():
    from deckframes.themes import list_themes

    themes = [json.loads(Path(t["path"]).read_text(encoding="utf-8")) for t in list_themes()
              if t["engine"] == "canvas" and t["source"] == "builtin"]
    assert len(themes) >= 20
    sigs = {(t["style"]["surface"], t["style"].get("cover"), t["style"].get("nav")) for t in themes if "style" in t}
    assert len(sigs) >= 12


def test_monotony_warning():
    from deckframes.lint import variety

    slides = "\n".join(f"### Slide {i}\n\n- a\n- b\n" for i in range(6))
    doc = parse_markdown(f"# Deck\n\n## Part\n\n{slides}")
    warns = variety(doc)
    assert any("consecutive" in w for w in warns)
    assert any("6/6" in w for w in warns)
