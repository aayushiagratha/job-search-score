#!/usr/bin/env python3
"""Check whether a UK employer can actually sponsor you.

Being *on* the sponsor register is not enough. Four things must all hold:

  1. The employer is on the register.
  2. They hold the **Skilled Worker** route. (Global Business Mobility only covers
     transferring existing overseas staff — it cannot be used to hire you locally,
     and it does not lead to settlement.)
  3. Their rating is **A**, not B. A B-rated sponsor cannot issue new Certificates
     of Sponsorship, so a licence they can't use is no licence at all.
  4. The salary clears the visa's floor. A licensed A-rated employer paying below
     the threshold still cannot sponsor you.

Plus one job-level check that overrides everything: if the job description says
"no sponsorship", the register is irrelevant.

The B-rating gate, T/A trading-name matching, and the negative-phrase override are
adapted from Sponsor-Radar (https://github.com/adilh333/Sponsor-Radar), which handles
the register more rigorously than this did originally.

Usage:
    python3 sponsor_check.py "Company Name" [--salary 35000] [--jd path/to/jd.txt]
    python3 sponsor_check.py --refresh          # re-download the register

A licence means an employer *can* sponsor. It never guarantees they *will* sponsor a
specific role. Always confirm with the employer.
"""
import csv, os, re, sys, difflib, urllib.request

CACHE = os.path.expanduser("~/.cache/sponsor_register.csv")
PUBLICATION_PAGE = ("https://www.gov.uk/government/publications/"
                    "register-of-licensed-sponsors-workers")

# Route that actually lets a UK employer hire you from inside the country.
VALID_ROUTE = "Skilled Worker"
# Routes that look like a licence and are not (for this purpose).
TRAP_ROUTES = ("Global Business Mobility", "Temporary Worker", "Creative Worker")

# UK Skilled Worker salary floors — CHECK THESE, THEY CHANGE.
# https://www.gov.uk/skilled-worker-visa/your-job
SALARY_FLOOR_NEW_ENTRANT = 33_400   # new entrant (incl. switching from Graduate visa)
SALARY_FLOOR_GENERAL     = 41_700   # general threshold

# A job description saying this beats anything the register says.
NEGATIVE_PHRASES = [
    r"no visa sponsorship", r"cannot (?:offer|provide) sponsorship",
    r"unable to (?:offer|provide) sponsorship", r"not able to sponsor",
    r"do(?:es)? not sponsor", r"sponsorship is not (?:available|offered|provided)",
    r"we are unable to sponsor", r"without (?:the need for )?sponsorship",
    r"must (?:already )?have (?:the )?right to work",
    r"no sponsorship (?:is )?(?:available|offered|provided)",
]

SUFFIXES = r"\b(limited|ltd|plc|llp|inc|llc|corp|corporation|company|holdings|group|uk|gb|the)\b"


def refresh():
    """The CSV URL changes with each publication, so scrape the page for it."""
    page = urllib.request.urlopen(PUBLICATION_PAGE, timeout=30).read().decode("utf-8", "ignore")
    m = re.search(r'https://assets\.publishing\.service\.gov\.uk/[^"]+\.csv', page)
    if not m:
        sys.exit("Could not find the register CSV link on the gov.uk page.")
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    urllib.request.urlretrieve(m.group(0), CACHE)
    print(f"Register downloaded: {CACHE}")


def norm(s):
    s = re.sub(r"\(.*?\)", " ", (s or "").lower())
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(SUFFIXES, " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load():
    """Return {normalised_name: [(legal_name, route, rating), ...]}.

    Registers list legal entities; job boards show brands. Many rows carry a
    trading name ("X LTD T/A Brand") — index BOTH, or you miss the brand you know.
    """
    if not os.path.exists(CACHE):
        refresh()
    idx = {}
    with open(CACHE, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            legal = row["Organisation Name"]
            route = row["Route"].strip()
            rating = row.get("Type & Rating", "")
            names = [legal]
            ta = re.split(r"\bt/?a\b", legal, flags=re.I)
            if len(ta) > 1:                       # index the trading name too
                names += [ta[0], ta[1]]
            for n in names:
                k = norm(n)
                if len(k) >= 3:
                    idx.setdefault(k, []).append((legal, route, rating))
    return idx


def jd_forbids_sponsorship(text):
    t = re.sub(r"\s+", " ", text.lower())
    for p in NEGATIVE_PHRASES:
        m = re.search(p, t)
        if m:
            i = max(0, m.start() - 60)
            return t[i:m.end() + 60].strip()
    return None


def check(company, salary=None, jd_text=None):
    print(f"\n{'='*72}\nEMPLOYER: {company}\n{'='*72}")

    # Job-level override: a JD that rules out sponsorship beats the register.
    if jd_text:
        hit = jd_forbids_sponsorship(jd_text)
        if hit:
            print(f"  ❌ BLOCKED BY THE JOB DESCRIPTION")
            print(f"     \"...{hit}...\"")
            print("     The register is irrelevant. This role will not be sponsored.")
            return False

    idx = load()
    key = norm(company)
    rows = idx.get(key)

    if not rows:
        # ONLY an exact normalised match counts as verification.
        #
        # Everything else is PROPOSED, never asserted. This is the hard-won lesson from
        # Sponsor-Radar, and every shortcut around it produces confident lies:
        #   - substring:  "Tesco" -> "ATESCO CONSULTANCY LTD"
        #   - trigram:    "Encord" -> "Encortec Limited"
        #   - prefix:     "IRIS Software Group" -> "iRiS Software Systems Ltd"  (different firm)
        #   - prefix:     "Tesco" -> "Tesco Personal Finance plc"               (different entity)
        # A false "they can sponsor you" costs someone years. Missing a match costs an email.
        cands = [(1.0, k) for k in idx if k.startswith(key + " ")] if len(key) >= 4 else []
        cands += [(difflib.SequenceMatcher(None, key, k).ratio(), k)
                  for k in difflib.get_close_matches(key, idx.keys(), n=4, cutoff=0.86)]
        seen, near = set(), []
        for s, k in sorted(cands, reverse=True):
            if k not in seen:
                seen.add(k); near.append((s, k))

        print("  ⚠️  NOT VERIFIED — no exact match on the register under this name.")
        print("     This does NOT mean they cannot sponsor. The register lists legal")
        print("     entities; job boards show brands. It means YOU MUST ASK THEM:")
        print('       "Which legal entity holds the contract, and does it hold a')
        print('        Skilled Worker sponsor licence?"')
        if near:
            print("\n     Possible entities — SUGGESTIONS ONLY, NOT VERIFICATION:")
            for s, k in near[:4]:
                for legal, route, rating in idx[k][:1]:
                    ok = "SW" if route == VALID_ROUTE else "--"
                    print(f"       [{ok}] {s:.2f}  {legal}  |  {route}  |  {rating}")
            print("\n     A high score means NOTHING. 'iRiS Software Systems Ltd' is a")
            print("     perfect prefix of 'IRIS Software Group' and is a different company.")
        return None

    routes = {r: (l, rt) for l, r, rt in rows}
    print(f"  Found on register as: {rows[0][0]}")
    for _, route, rating in rows:
        mark = "✅" if route == VALID_ROUTE else "⚠️ "
        print(f"    {mark} {route:<52} {rating}")

    if VALID_ROUTE not in routes:
        traps = [r for r in routes if r.startswith(TRAP_ROUTES)]
        print(f"\n  ❌ NO SKILLED WORKER LICENCE.")
        if traps:
            print(f"     They hold {traps[0]} — which only covers transferring existing")
            print(f"     overseas staff into the UK. It cannot be used to hire you locally,")
            print(f"     and it does not lead to settlement. This is a dead end.")
        return False

    rating = routes[VALID_ROUTE][1]
    if re.search(r"\bB\s*[-(]?\s*rating|\(B rating\)", rating, re.I):
        print(f"\n  ❌ B-RATED SPONSOR ({rating}).")
        print("     A B-rated sponsor cannot issue NEW Certificates of Sponsorship until")
        print("     they return to an A rating. A licence they can't use is no licence.")
        return False

    print(f"\n  ✅ Skilled Worker licence, {rating}")

    if salary is not None:
        if salary < SALARY_FLOOR_NEW_ENTRANT:
            print(f"  ❌ SALARY TOO LOW: £{salary:,} is below the £{SALARY_FLOOR_NEW_ENTRANT:,} "
                  f"new-entrant floor.")
            print("     A licensed employer below the threshold still cannot sponsor you.")
            return False
        band = "new-entrant" if salary < SALARY_FLOOR_GENERAL else "general"
        print(f"  ✅ Salary £{salary:,} clears the {band} floor.")
    else:
        print(f"  ⚠️  No salary given. Must clear £{SALARY_FLOOR_NEW_ENTRANT:,} (new entrant) "
              f"or £{SALARY_FLOOR_GENERAL:,} (general).")

    print("\n  → CAN sponsor. Does not mean they WILL sponsor this role. Ask them.")
    return True


if __name__ == "__main__":
    if "--refresh" in sys.argv:
        refresh(); sys.exit(0)
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    args = sys.argv[1:]
    company = args[0]
    salary = None
    jd = None
    if "--salary" in args:
        salary = int(args[args.index("--salary") + 1])
    if "--jd" in args:
        jd = open(args[args.index("--jd") + 1], encoding="utf-8", errors="ignore").read()
    check(company, salary, jd)
