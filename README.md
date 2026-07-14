# job-search-score

An agent skill for **Claude Code** that runs a job search the way a careful person would: it
verifies before it recommends, checks whether an employer can legally hire you, ranks by how
*winnable* a role is rather than how well it matches, and writes application documents in **your
own CV format** rather than a template it invented.

It is built to reject roles, not to spray applications.

---

## Why this exists

Naive job tooling title-matches a search and ranks by vibes. That produces three specific failures:

**1. Wrong company.** A company name collides with a better-known one and you assume the wrong
sector, size, or business entirely. The fix: read what the job description actually says the company
does — never infer identity from a name on a card.

**2. Agency listings that look like direct ones.** The "company" is a recruitment agency and the
description is about an unnamed client. It reads like an employer posting and isn't. Its advertised
salary is the client's *budget*, not a contracted offer.

**3. A perfect-fit role you can never win.** 200 applicants, or an employer who legally cannot
sponsor your visa. **Fit alone is not a ranking.**

---

## What's actually in here

| File | What it does |
|---|---|
| `SKILL.md` | The procedure. Eight steps, in English. This is the brain. |
| `linkedin-endpoints.md` | LinkedIn's public, unauthenticated job endpoints — params, pacing, selectors. |
| `comp-and-legitimacy.md` | Two judgment checks: is the salary real, and is the posting real. |
| `build_cv.py` | Generates `.docx` files by **cloning your existing CV's formatting**. |
| `config.example.json` | Everything personal lives here. Nothing is hardcoded. |

---

## Three ideas worth stealing even if you don't use this

### 1. The visa sponsorship gate (UK)

If you need sponsorship, this runs **before fit matters**. Cross-reference every employer against
the UK government's [Register of licensed sponsors](https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers)
(a public CSV) and check for the **Skilled Worker** route *specifically*.

**The trap:** other routes look like a licence and aren't. **Global Business Mobility** only covers
transferring existing overseas staff into the UK — it cannot be used to hire you locally, and it
does not lead to settlement. A company can appear on the register and still be a dead end.

**The second trap:** a licensed employer paying below the visa's salary floor still cannot sponsor
you. Both conditions must hold.

**And a warning:** match on **exact normalised legal-entity names only**. The register lists legal
entities; job boards show brand names. Substring matching produces nonsense — it will cheerfully
match a supermarket to an unrelated consultancy with a similar name. A miss means *verify manually*,
not *cannot sponsor*.

### 2. Rank on fit × sponsorship × (low) competition

A role can match you perfectly, hold a sponsor licence, and still be hopeless at 170 applicants.
Applicant count **is** exposed in LinkedIn's public response (`num-applicants__caption`) — most tools
ignore it.

The counter-intuitive part: the **least contested roles are the ones with friction**. An unglamorous
domain. A relocation clause. Multi-hour tests. A boring title. That friction is the moat, because
most people won't push through it — and a frictionless role (no experience bar, published salary,
desirable city) can take 100+ applicants in a day.

### 3. Clone your CV's format; never design one

`build_cv.py` opens your existing `.docx`, keeps its fonts, colours, borders, tab stops and page
setup, and swaps in new content. The output matches your CV **by construction**, not by imitation.

Two things this saves you from:

- `textutil -convert docx file.md` **does not render Markdown.** It dumps literal `#` and `**` into
  the document. If you've ever had a CV come out looking like a draft, that's why.
- Every bullet comes from a **verified bullet bank** in X-Y-Z form (*accomplished X, as measured by
  Y, by doing Z*). Never invent a metric. If it isn't in the bank, it doesn't go in.

---

## Setup

Requires [Claude Code](https://claude.com/claude-code), Python 3, and macOS or Linux.

```bash
git clone https://github.com/aayushiagratha/job-search-score.git
mkdir -p ~/.claude/skills
cp -r job-search-score ~/.claude/skills/

cd ~/.claude/skills/job-search-score
cp config.example.json config.json   # then edit it
```

Fill in `config.json`: your CV, your verified bullet bank, your CV template, target titles and
locations, salary band, hard disqualifiers, and — if you need one — your visa situation.

Then, in Claude Code:

```
find me product marketing jobs in London posted this week
```

It will search, verify, check sponsorship, rank, and **stop** — presenting everything in chat and
building nothing until you pick a role. That pause is deliberate.

### Generating documents directly

```bash
CV_TEMPLATE=~/Documents/my-cv.docx python3 build_cv.py content.json out.docx
```

The JSON schema is documented in the script's docstring.

---

## ⚠️ Terms of service

This uses LinkedIn's **public, unauthenticated** `jobs-guest` endpoints. No login, no cookies, no
account credentials — so there is no account to ban. **But automated access is against LinkedIn's
Terms of Service**, and they can rate-limit or block by IP.

Use it at human volumes for your own job search. The pacing and backoff in `linkedin-endpoints.md`
exist for that reason — respect them. This is a considered-search tool, not a scraper, which is also
the entire point of it.

**Do not** point it at an authenticated session. Automating a logged-in LinkedIn account is the thing
that actually gets accounts restricted, and it would put at risk the exact account your job search
depends on.

---

## Credits

The LinkedIn guest-endpoint approach, the two-pass experience filter, and the pacing/backoff pattern
were learned from:

- [career-ops](https://github.com/santifer/career-ops) (MIT) — the compensation-reliability and
  posting-legitimacy checks in `comp-and-legitimacy.md` are adapted from its evaluation prompts.
- [ai-job-search](https://github.com/MadsLorentzen/ai-job-search) — source of the `jobs-guest`
  endpoint documentation.
- [linkedin-job-scanner](https://github.com/ishal1410/linkedin-job-scanner) (MIT) — the `f_E`
  two-pass strategy (untagged postings vanish under a filtered search), the pacing constants, and
  the reminder that `\b` word boundaries silently break `c++`, `c#`, `.net` and `node.js` in keyword
  matching.

The sponsorship gate, the competition-as-a-ranking-axis idea, and the clone-your-own-format
document generator are original to this skill.

## Licence

MIT.
