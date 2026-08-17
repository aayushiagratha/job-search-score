import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import voice_check as vc


def test_clean_text_has_no_findings(capsys):
    good = "I ran demand campaigns that tripled qualified leads. I name my gaps plainly."
    assert vc.check(good, "clean") == 0


def test_slop_phrase_is_flagged():
    assert vc.check("I am passionate about this role.", "t") >= 1


def test_ai_sentence_shape_is_flagged():
    assert vc.check("It's not just marketing, but a real strategy shift.", "t") >= 1


def test_double_comma_is_flagged():
    assert vc.check("I led campaigns,, and grew revenue.", "t") >= 1


def test_high_em_dash_density_is_flagged():
    text = "word " * 60 + "—" * 2 + " more words here to pad it out a bit"
    assert vc.check(text, "t") >= 1


def test_link_containing_colon_is_not_flagged_as_collision():
    # A URL's "https:" colon should not trip the double-colon collision check.
    clean = "See https://example.com/path for the case study details and results."
    assert vc.check(clean, "t") == 0


def test_demo_self_check_passes():
    # voice_check.py ships its own assert-based self-check; keep it green under pytest too.
    vc.demo()
