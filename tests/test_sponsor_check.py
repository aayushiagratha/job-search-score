import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sponsor_check as sc


def write_register(path, rows):
    """rows: list of (organisation_name, route, rating) tuples."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Organisation Name", "Route", "Type & Rating"])
        w.writeheader()
        for org, route, rating in rows:
            w.writerow({"Organisation Name": org, "Route": route, "Type & Rating": rating})


@pytest.fixture
def register(tmp_path, monkeypatch):
    """Point sponsor_check at a throwaway register CSV instead of the real cache/network."""
    def _make(rows):
        cache = tmp_path / "sponsor_register.csv"
        write_register(cache, rows)
        monkeypatch.setattr(sc, "CACHE", str(cache))
        return cache
    return _make


# --- norm() ---

def test_norm_strips_suffix_and_punctuation():
    assert sc.norm("Acme Widgets Ltd.") == "acme widgets"


def test_norm_strips_parenthetical():
    assert sc.norm("Acme (UK) Widgets Limited") == "acme widgets"


def test_norm_empty_and_none():
    assert sc.norm("") == ""
    assert sc.norm(None) == ""


# --- jd_forbids_sponsorship() ---

@pytest.mark.parametrize("phrase", [
    "This role offers no visa sponsorship.",
    "Sorry, we do not sponsor work visas.",
    "Applicants must already have the right to work in the UK.",
    "This role is offered without sponsorship.",
])
def test_jd_forbids_sponsorship_catches_negative_phrases(phrase):
    assert sc.jd_forbids_sponsorship(phrase) is not None


def test_jd_forbids_sponsorship_clean_text():
    assert sc.jd_forbids_sponsorship("We welcome applications from all candidates.") is None


# --- check(): job-level override ---

def test_check_blocked_by_jd_overrides_everything(register):
    register([("Acme Widgets Ltd", "Skilled Worker", "A rating")])
    assert sc.check("Acme Widgets", jd_text="We do not sponsor visas.") is False


# --- check(): unverified (no register match) ---

def test_check_unverified_when_not_on_register(register):
    register([("Some Other Company Ltd", "Skilled Worker", "A rating")])
    assert sc.check("Totally Different Name") is None


# --- check(): Skilled Worker path ---

def test_check_passes_for_a_rated_skilled_worker(register):
    register([("Acme Widgets Ltd", "Skilled Worker", "A rating")])
    assert sc.check("Acme Widgets") is True


def test_check_fails_for_b_rated_sponsor(register):
    register([("Acme Widgets Ltd", "Skilled Worker", "B rating")])
    assert sc.check("Acme Widgets") is False


def test_check_fails_for_trap_route_only(register):
    register([("Acme Widgets Ltd", "Global Business Mobility", "A rating")])
    assert sc.check("Acme Widgets") is False


def test_check_fails_when_no_valid_route_at_all(register):
    register([("Acme Widgets Ltd", "Temporary Worker", "A rating")])
    assert sc.check("Acme Widgets") is False


# --- check(): salary floors (Skilled Worker) ---

def test_check_fails_below_new_entrant_floor(register):
    register([("Acme Widgets Ltd", "Skilled Worker", "A rating")])
    assert sc.check("Acme Widgets", salary=30_000) is False


def test_check_passes_at_new_entrant_band(register):
    register([("Acme Widgets Ltd", "Skilled Worker", "A rating")])
    assert sc.check("Acme Widgets", salary=35_000) is True


def test_check_passes_at_general_band(register):
    register([("Acme Widgets Ltd", "Skilled Worker", "A rating")])
    assert sc.check("Acme Widgets", salary=45_000) is True


def test_check_passes_with_no_salary_given(register):
    register([("Acme Widgets Ltd", "Skilled Worker", "A rating")])
    assert sc.check("Acme Widgets") is True


# --- check(): Scale-up route, opt-in behaviour ---

def test_scaleup_only_employer_fails_by_default(register):
    register([("Acme Widgets Ltd", "Scale-up", "A rating")])
    assert sc.check("Acme Widgets") is False


def test_scaleup_only_employer_passes_when_opted_in(register):
    register([("Acme Widgets Ltd", "Scale-up", "A rating")])
    assert sc.check("Acme Widgets", salary=40_000, include_scaleup=True) is True


def test_scaleup_salary_floor_is_independent_of_skilled_worker_floor(register):
    register([("Acme Widgets Ltd", "Scale-up", "A rating")])
    # Below the Scale-up floor (39,100) but above the Skilled Worker new-entrant
    # floor (33,400) — must still fail, the two floors are not interchangeable.
    assert sc.check("Acme Widgets", salary=35_000, include_scaleup=True) is False


def test_dual_route_employer_prefers_skilled_worker(register):
    register([
        ("Acme Widgets Ltd", "Scale-up", "A rating"),
        ("Acme Widgets Ltd", "Skilled Worker", "A rating"),
    ])
    # With scale-up opted in, an employer holding both routes should still be
    # evaluated as Skilled Worker (the stronger status), so the Skilled Worker
    # salary floor applies, not the Scale-up one.
    assert sc.check("Acme Widgets", salary=35_000, include_scaleup=True) is True


# --- load(): trading-name indexing ---

def test_trading_name_is_indexed_separately(register):
    register([("Acme Holdings Ltd T/A Widget Co", "Skilled Worker", "A rating")])
    assert sc.check("Widget Co") is True
    assert sc.check("Acme Holdings") is True
