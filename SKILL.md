---
name: job-search-score
description: >
  Search LinkedIn Jobs without logging in, verify every listing's real company identity and
  agency status (never trust the card text), check visa sponsorship against the official UK
  register, rank by fit x sponsorship x competition, and — only after you confirm — build
  tailored application documents in your own CV format. Triggers include "job search",
  "find me jobs", "score this role", "ATS analysis for X".
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# Job Search & Score

Most job-search tooling title-matches a search and ranks by vibes. That produces three specific
failures, and every step here exists to prevent one of them:

1. **Wrong company.** A company name collides with a better-known one, and you assume the wrong
   sector, size, or business entirely. Read what the job description actually says the company does.
2. **Agency posting as employer.** The "company" on the card is a recruitment agency, and the
   description is about an unnamed client. It looks like a direct listing and isn't.
3. **A perfect-fit role you can never win.** 200 applicants, or an employer who legally cannot
   sponsor you. Fit alone is not a ranking.

## Setup

Copy `config.example.json` to `config.json` and fill it in: your CV path, your verified bullet
bank, your CV template, target salary band, hard disqualifiers, and (if relevant) your visa
situation. Everything below reads from it. **Nothing in this skill is hardcoded to one person.**

## Step 0: Ground truth on the candidate

Read the CV named in `config.json`. If several CVs exist, ask which is authoritative — do not guess.

**Only use numbers you can trace to a real source.** A metric that isn't in the verified bullet bank
or a confirmed CV does not go into a document. Ever. If a file's numbers can't be verified, don't
use that file.

Load the hard constraints from config: salary band, target sectors, location, work authorisation,
and anything that is an automatic no.

## Step 1: Search

Use the **unauthenticated `jobs-guest` endpoints** — see `linkedin-endpoints.md`. Plain HTTP, no
login, no browser. Capture job ID, title, company, location, posted date.

**Run two passes per query.** One with the experience-level filter (`f_E`), one without. LinkedIn
leaves the experience field untagged on many postings — especially at startups — and those vanish
from a filtered search entirely. Dedupe by job ID.

The guest search has **no radius parameter**. Run one query per location string rather than trying
to widen a single query.

## Step 2: Pre-filter (free — no page loads)

Drop from the card text alone: seniority above target, explicit recruitment agencies, obvious
sector mismatches, internships (unless wanted).

**If a description can't be fetched or parsed, keep it and flag it for manual review.** A failed
fetch is missing information, not a disqualification. A silent drop is indistinguishable from a
role that never existed.

## Step 3: Verify — the step everyone skips

Fetch the full description for every survivor via the guest detail endpoint. Then:

- **Read the "About Us" section.** Never infer company identity, sector, or size from the name.
- **Check for the agency pattern.** If the poster is a recruitment or staffing firm and the
  description is about a *different, unnamed* company, that's an agency-for-unnamed-client listing.
  Exclude it (or flag it, per config) even though the card looked direct.
- **Pull the hard facts:** explicit years-of-experience requirement, seniority / employment type /
  function / industry (the job-criteria block), stated salary.
- **Pull the applicant count.** It IS in the guest response: `num-applicants__caption`, plus
  `posted-time-ago__text`. Report both, and compute the rate (applicants ÷ days live).

**Employee count and the hiring-trend panel are auth-gated.** The guest endpoint does not return
them. If company size is a hard filter, check the company's own site — but only for candidates that
survive every other test.

### Visa sponsorship gate (UK — skip if `config.visa` is null)

If the candidate needs sponsorship now or in future, this gate runs **before** fit matters.

- Download the official register: gov.uk → *Register of licensed sponsors: workers* (CSV).
- Check for the **Skilled Worker** route **specifically**. Other routes are traps:
  **Global Business Mobility** only covers transfers of existing overseas staff, cannot be used to
  hire someone locally, and does not lead to settlement.
- **Match on exact normalised legal-entity names only.** Fuzzy or substring matching produces
  garbage — it will happily match a supermarket to an unrelated consultancy with a similar name.
  The register lists *legal entities*; job boards show *brand names*. A miss means "verify
  manually", not "cannot sponsor".
- **Check the salary too.** A licensed employer offering below the visa's salary floor still cannot
  sponsor. Both conditions must hold. Put the current thresholds in config — they change.

## Step 4: Score against the real CV

For each verified survivor:

- Estimated match % (say it's an approximation)
- Verdict: **Apply / Borderline / Drop**
- Keyword gap table: Missing / Matching / Weakly demonstrated
- Specific reasons they'd be shortlisted — cite JD lines and CV lines
- Specific reasons they'd be rejected — cite JD lines and real gaps
- **Comp reliability + posting legitimacy** — run both checks in `comp-and-legitimacy.md`.
  Advertised salary is not the offer, and not every posting is a live opening.

**Keyword matching: never bound terms with `\b`.** It makes `c++`, `c#`, `.net`, `node.js` and
`ci/cd` match nothing — silently filing real skills under "Missing". Use lookarounds bounded on
alphanumerics instead.

**Hard disqualifiers** (drop without a full score) come from config. Typical: agency-for-unnamed-
client, a years-of-experience bar well above the candidate, a role that is sales wearing a
different title, wrong sector, unsponsorable when sponsorship is required.

## Step 4b: Rank on three axes, not one

**fit × sponsorship × (low) competition.**

A role can match perfectly, hold a sponsor licence, and still be hopeless at 170 applicants.
Counter-intuitively, the *least* contested roles usually have **friction**: an unglamorous domain, a
relocation clause, multi-hour tests, a boring title. That friction is the moat — most people won't
push through it. Surface it and say plainly when a strong-fit role is drowning.

Frictionless roles (no experience bar, published salary, desirable city) attract enormous volume
fast. Check the applicant rate before recommending one.

## Step 5: Present in chat, then stop

Post the full analysis in chat. **Never as a document.** Build nothing until the candidate
explicitly picks a role. This step exists so nobody burns an hour writing documents for a job they
don't want.

## Step 6: Build documents — only on confirmation

CV, cover letter, and (optionally) a value-proposition brief, as `.docx`.

### Use the generator — never invent a format

`python3 build_cv.py <content.json> <out.docx>`

It **clones the CV template named in config** and rewrites its content, so output matches the
candidate's existing format by construction rather than by imitation. Schema is in the script's
docstring: `body`, `paras`, `bullets`, `entries` (org / role / dates / meta / bullets),
`table` (cols / rows), `skills`. `**bold**` works inline.

**Never convert Markdown with `textutil -convert docx file.md`.** `textutil` does not render
Markdown — it treats it as plain text, so `#`, `**bold**` and table pipes land in the document as
literal characters. Use HTML as the intermediate, or use the generator.

**Always open one converted file and read it before saying it's done.** A conversion that silently
produces garbage is worse than one that errors.

### Bullets: X-Y-Z, from the verified bank only

Every bullet: *"Accomplished [X], as measured by [Y], by doing [Z]."* Action verb, real metric,
concrete method. Draw only from the bullet bank in config. **Never invent a metric.**

### Keyword coverage lives in the SKILLS section

If the CV format has no "core competencies" block, load each JD's real vocabulary into the SKILLS
lines instead. That is what moves an ATS score without bolting a foreign block onto a good CV.

### Per document

- **CV** — reorder and reweight real, verified experience to match this JD's language. Never invent
  a bullet. Order by *relevance*, not strict reverse chronology, when the strongest experience isn't
  the most recent.
- **Cover letter** — specific to the company. Name real details from the description; it proves you
  read it. **Name the candidate's real gaps** rather than hoping the employer misses them.
- **Value prop brief** — why this company fits, what the candidate brings that they're missing,
  a 90-day plan against the JD's actual stated responsibilities, and any traps buried in the posting
  (relocation clauses, unpaid tests, apply-here-only rules).

Save to a dated folder, named `<Company> - <Role Title> - CV.docx`.

## Step 7: Outreach

Hiring-manager email and connection note, **in chat as plain text, never a document**. Personalise
with real specifics from the research. Only worth doing at small companies where a note actually
reaches a human.

## Step 8: Re-score

Re-run the keyword comparison against the **finished** CV and report whether it actually improved.
**Do not assume the rewrite worked.** If it got worse, say so and fix it.

## Notes

- If a batch of 10+ needs full verification, delegate to a subagent with the job IDs and profile
  facts baked in — it keeps raw HTML noise out of the main conversation.
- If the candidate says a scoring pass wasn't rigorous enough, that's a signal to **re-verify
  company identity**, not to re-read the same card text harder.
- The job title on a job board is not always the employer's real requisition title. If the apply
  link goes to an ATS (Workday, Greenhouse, Lever), check the title there — it can differ, and the
  seniority tag on the board is often the board's guess, not the employer's.
