import pytest

from deckframes.check import check
from deckframes.engines.canvas import Canvas
from deckframes.layout import degrade
from deckframes.markdown import Block, parse_component
from deckframes.themes import resolve_theme


def render_lanes(tmp_path, body, info="", theme="academic"):
    tokens, _ = resolve_theme(theme)
    canvas = Canvas(tokens, {}, tmp_path)
    slide = canvas.new_slide()
    canvas.comp_lanes(slide, parse_component("lanes", info, body), .5, 1, 12, 4.5)
    return canvas, slide


def named(slide, prefix):
    return [shape for shape in slide.shapes if shape.name.startswith(prefix)]


def overlaps(a, b):
    return (a.left < b.left + b.width - 2 and b.left < a.left + a.width - 2
            and a.top < b.top + b.height - 2 and b.top < a.top + a.height - 2)


@pytest.mark.parametrize("theme", ["academic", "aws", "blockframe"])
def test_dense_lanes_keep_items_and_notes_inside_bands(tmp_path, theme):
    body = "\n".join(f"- 2024 | Method-{i} | lane: Dense | note: Workshop-{i}" for i in range(8))
    body += "\n- 2023 | Early | lane: Sparse | note: Venue"
    canvas, slide = render_lanes(tmp_path, body, theme=theme)
    bands = named(slide, "lanes:band:")
    entries = named(slide, "lanes:item:") + named(slide, "lanes:note:")
    assert len(entries) == 18
    assert bands[0].height > bands[1].height
    for entry in entries:
        assert any(b.left <= entry.left and entry.left + entry.width <= b.left + b.width
                   and b.top <= entry.top and entry.top + entry.height <= b.top + b.height for b in bands)
    assert not any(overlaps(a, b) for i, a in enumerate(entries) for b in entries[i + 1:])
    out = tmp_path / f"{theme}.pptx"
    canvas.prs.save(out)
    assert check(out)["ok"]
    assert all(shape.shape_type != 13 for shape in slide.shapes)


def test_note_width_is_included_in_collision_detection(tmp_path):
    _, slide = render_lanes(tmp_path,
        "- 2024 | A | lane: Models | note: A much longer conference name\n"
        "- 2025 | B | lane: Models | note: Another long conference name", "2020-2030")
    a, b = named(slide, "lanes:item:")
    na, nb = named(slide, "lanes:note:")
    assert a.top != b.top
    assert a.width >= na.width and b.width >= nb.width
    assert not overlaps(na, nb)


def test_explicit_ticks_fold_older_years_and_focus_an_item(tmp_path):
    canvas, slide = render_lanes(tmp_path,
        "- 2012 | Old | lane: Models | note: 2012\n"
        "- 2022 | Other | lane: Models\n"
        "- 2025 | Proposed | lane: Models | note: This work",
        "ticks=2018,2022,2023,2024,2025 focus=Proposed")
    labels = {shape.text: shape for shape in slide.shapes if shape.has_text_frame}
    assert "≤2018" in labels
    assert "2019" not in labels and "2020" not in labels
    centers = [labels[str(year)].left + labels[str(year)].width // 2 for year in [2022, 2023, 2024]]
    assert abs((centers[1] - centers[0]) - (centers[2] - centers[1])) <= 2
    proposed = named(slide, "lanes:item:Proposed")[0]
    other = named(slide, "lanes:item:Other")[0]
    assert proposed.fill.fore_color.rgb != other.fill.fore_color.rgb
    assert str(proposed.line.color.rgb) == canvas.tones["positive"]
    assert proposed.text_frame.paragraphs[0].runs[0].font.color.rgb is not None


def test_lanes_pack_deterministically(tmp_path):
    body = "\n".join(f"- 2024 | M{i} | lane: Models | note: Venue" for i in range(6))
    _, first = render_lanes(tmp_path, body)
    _, second = render_lanes(tmp_path, body)
    def geometry(slide):
        return [(s.name, s.left, s.top, s.width, s.height) for s in slide.shapes]
    assert geometry(first) == geometry(second)


def test_invalid_ticks_fall_back_to_dated_items(tmp_path):
    canvas, slide = render_lanes(tmp_path, "- 2024 | A | lane: Models", "ticks=2025,2024")
    assert named(slide, "lanes:item:A")
    assert any("ticks" in warning for warning in canvas.warnings)
    empty, _ = render_lanes(tmp_path, "- unknown | A | lane: Models")
    assert any("year range" in warning for warning in empty.warnings)


def test_template_lanes_preserve_classification_and_venue():
    block = Block("component", parse_component("lanes", "2020-2025",
        "- 2024 | Example | lane: Family | note: Workshop"))
    result = degrade([block])
    assert result[0].kind == "table"
    assert result[0].data["rows"] == [["Year", "Lane", "Method", "Note"],
                                       ["2024", "Family", "Example", "Workshop"]]
