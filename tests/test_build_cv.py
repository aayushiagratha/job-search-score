import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_cv as bc


# --- pure XML-fragment helpers ---

def test_run_escapes_special_characters():
    xml = bc.run("A & B <C>", 9)
    assert "&amp;" in xml
    assert "&lt;C&gt;" in xml


def test_inline_runs_splits_bold_markdown():
    runs = bc.inline_runs("Grew **revenue** by 3x")
    joined = "".join(runs)
    assert "Grew " in joined
    assert "revenue" in joined
    assert '<w:b/>' in joined  # the bold segment carries a bold run property


def test_inline_runs_no_bold_returns_single_run():
    assert len(bc.inline_runs("plain text")) == 1


def test_bullet_wraps_in_list_paragraph_with_numid():
    xml = bc.bullet("Did a thing", numid=3)
    assert 'w:numId w:val="3"' in xml
    assert "Did a thing" in xml


def test_table_header_row_and_dimensions():
    xml = bc.table(["Skill", "Level"], [["Python", "Strong"]])
    assert xml.count("<w:tr>") == 2  # header + one data row
    assert "Skill" in xml and "Python" in xml


# --- build(): end-to-end against a synthetic template, no real CV needed ---

@pytest.fixture
def fake_template(tmp_path):
    """A minimal .docx with just enough structure for build() to work with."""
    path = tmp_path / "template.docx"
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body>'
        '<w:p><w:pPr><w:numPr><w:numId w:val="1"/></w:numPr></w:pPr></w:p>'
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr>'
        '</w:body></w:document>'
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", document_xml)
        z.writestr("[Content_Types].xml", "<Types/>")
    return path


def test_build_writes_valid_docx_with_expected_content(tmp_path, fake_template):
    content = {
        "name": "Jordan Doe",
        "contact": ["London, UK", "jordan@example.com"],
        "sections": [
            {"heading": "PROFILE", "body": "Product marketer who builds AI systems."},
            {"heading": "SKILLS", "skills": [["AI", "LangGraph • n8n"]]},
            {"heading": "EXPERIENCE", "entries": [
                {"org": "Acme", "role": "AI Engineer", "bullets": ["Shipped a thing."]},
            ]},
        ],
    }
    out_path = tmp_path / "out.docx"

    result = bc.build(content, template=fake_template, out=str(out_path))

    assert result == str(out_path)
    assert out_path.exists()
    with zipfile.ZipFile(out_path) as z:
        doc = z.read("word/document.xml").decode("utf-8")
    assert "Jordan Doe" in doc
    assert "Product marketer" in doc
    assert "LangGraph" in doc
    # numbering id carried over from the template, not hardcoded elsewhere
    assert 'w:numId w:val="1"' in doc


def test_build_exits_when_template_missing(tmp_path):
    missing = tmp_path / "does-not-exist.docx"
    with pytest.raises(SystemExit):
        bc.build({"name": "X", "contact": [], "sections": []}, template=missing, out=str(tmp_path / "o.docx"))
