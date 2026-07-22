#!/usr/bin/env python3
"""voice_check — flag AI-slop tells in a CV or cover letter.

Reports; does not auto-fix. (Same principle as the career-ops "report the page
count as a fact, don't tune it" house rule: the linter surfaces, a human decides.)

Catches the mechanical tells — the objective stuff a regex can judge:
  - em-dash density (the #1 "written by AI" signal in prose)
  - banned slop phrases ("leverage", "passionate about", "seamlessly", ...)
  - AI sentence shapes ("not just X but Y", "isn't about X, it's about Y")
  - punctuation collisions (double colon / double comma — bugs we've shipped)

What it CANNOT judge is voice — whether it sounds like *you*. That's the
`voice-dna.md` pass in SKILL.md, run after this comes back clean.

Usage:  python3 voice_check.py <file.docx | file.md | file.txt>
"""
import re, subprocess, sys, os

BANNED = [  # near-always slop in a CV / cover letter
    "leverage", "spearhead", "passionate about", "results-driven", "results-oriented",
    "dynamic", "synergy", "fast-paced world", "excited to", "deep dive", "wheelhouse",
    "move the needle", "circle back", "boasts", "boasting", "seamlessly", "robust",
    "cutting-edge", "game-changer", "game changer", "tapestry", "testament to",
    "underscore", "delve", "elevate", "empower", "unlock", "embark", "plethora",
    "myriad", "treasure trove", "pivotal", "meticulous", "bustling", "foster",
    "garner", "poised to", "honed", "adept", "in the realm of", "in today's",
    "ever-evolving", "ever-changing", "landscape of", "navigate the complexities",
    "proven track record", "hit the ground running", "think outside the box",
    "self-starter", "detail-oriented", "team player", "go-getter", "value add",
]

SHAPES = [  # AI-favourite sentence constructions
    (r"\bnot just\b[^.]{0,60}\bbut\b", "'not just X but Y' construction"),
    (r"\bisn'?t (just )?about\b[^.]{0,50}\bit'?s about\b", "'isn't about X, it's about Y'"),
    (r"—\s*(which is|the same|exactly|precisely|the very)\b", "em-dash appositive aside (AI tell)"),
    (r"\b(that|this) is (a )?testament\b", "'is a testament to'"),
]

COLLISIONS = [
    (r":[^:\n]{1,60}:", "possible double-colon in one clause (check it's not a link)"),
    (r",\s*,", "double comma"),
    (r"\.\s*\.", "double period (not an ellipsis)"),
    (r"\s{2,}\S", "double space"),
]


def read(path):
    if path.endswith(".docx"):
        return subprocess.run(["textutil", "-convert", "txt", "-stdout", path],
                              capture_output=True, text=True).stdout
    return open(path, encoding="utf-8", errors="ignore").read()


def check(text, name=""):
    words = len(re.findall(r"\S+", text))
    dashes = text.count("—")
    density = dashes / words * 100 if words else 0
    findings = []

    # em-dash density: >1 per ~65 words reads as AI in prose. Structural role
    # lines use them legitimately, so this is a "look here", not a hard fail.
    if density > 1.5:
        findings.append(("HIGH", f"em-dash density {density:.1f}/100 words "
                         f"({dashes} dashes, {words} words) — AI-ish. ~1 per 65 words is the ceiling."))
    low = text.lower()
    for p in BANNED:
        for m in re.finditer(r"(?<![a-z])" + re.escape(p) + r"(?![a-z])", low):
            ctx = text[max(0, m.start()-25):m.end()+25].replace("\n", " ")
            findings.append(("SLOP", f'"{p}"  …{ctx.strip()}…'))
    for pat, label in SHAPES:
        for m in re.finditer(pat, low):
            ctx = text[max(0, m.start()-20):m.end()+20].replace("\n", " ")
            findings.append(("SHAPE", f"{label}  …{ctx.strip()}…"))
    for pat, label in COLLISIONS:
        for m in re.finditer(pat, text):
            near = text[max(0, m.start()-8):m.end()+8]
            if "http" in near or "•" in near:   # links and •-separated contact lines are fine
                continue
            findings.append(("PUNCT", f"{label}: …{text[max(0,m.start()-15):m.end()+15].strip()}…"))

    print(f"\n=== {name or 'document'} — {words} words, {dashes} em-dashes ({density:.1f}/100) ===")
    if not findings:
        print("  clean — no mechanical tells. Now run the voice-dna judgment pass.")
        return 0
    for tag, msg in findings:
        print(f"  [{tag}] {msg}")
    print(f"\n  {len(findings)} flag(s). These are for review, not auto-deletion — a "
          "real word in context beats a false positive.")
    return len(findings)


def demo():
    bad = ("I am passionate about leveraging cutting-edge tools — which is exactly "
           "what moves the needle. It's not just marketing, but a testament to synergy.")
    n = check(bad, "self-check")
    assert n >= 4, f"linter under-catching: only {n}"
    good = "I ran demand campaigns that tripled qualified leads. I name my gaps plainly."
    assert check(good, "self-check-clean") == 0
    print("\n✅ self-check passed")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        demo()
    else:
        f = sys.argv[1]
        sys.exit(1 if check(read(f), os.path.basename(f)) else 0)
