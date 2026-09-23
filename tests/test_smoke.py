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
