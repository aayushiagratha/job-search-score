# LinkedIn jobs-guest Endpoints

Public, unauthenticated endpoints. No login, no browser. Use these for Step 1 (search)
and the JD-reading half of Step 3 (verify). Source: github.com/MadsLorentzen/ai-job-search.

> **Personal use only.** Automated access is against LinkedIn's ToS. Keep volume low,
> don't parallelise hard, back off on 429/5xx. This is a considered-search tool, not a
> bulk scraper — which is also the whole point of this skill.

Verified working 2026-07-14 (both endpoints 200, selectors present).

## 1. Search — returns a page of 10 job cards

```
GET https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search
```

| Param | Meaning | Example |
|---|---|---|
| `keywords` | Free-text query | `product marketing` |
| `location` | Place string | `London, England, United Kingdom` |
| `f_TPR` | Posted within (seconds) | `r86400` (24h) · `r604800` (7d) · `r2592000` (30d) |
| `f_WT` | Workplace type | `1` on-site · `2` remote · `3` hybrid |
| `f_E` | Experience level | `1` intern · `2` entry · `3` associate · `4` mid-senior · `5` director |
| `start` | Pagination offset, 10 per page | `0`, `10`, `20`, … |

```bash
curl -s -A "Mozilla/5.0" \
  "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=product%20marketing&location=London%2C%20England%2C%20United%20Kingdom&f_TPR=r604800&f_E=2,3&start=0" \
  | grep -o 'jobPosting:[0-9]*' | sort -u
```

**Run two passes per query, not one.** `f_E=2,3` (entry/associate) matches the candidate’s level — but
LinkedIn leaves the experience field **untagged** on a lot of postings, especially at
startups, and those vanish from an `f_E`-filtered search entirely. So run:

1. one pass **with** `f_E=2,3`
2. one pass **with no `f_E` at all**, and dedupe by job ID

Pass 2 catches the untagged roles. Tag them so Step 4 knows the level wasn't
server-confirmed and has to be read off the JD.

### Pacing — LinkedIn 429s if you go fast

| Between | Wait |
|---|---|
| search pages | ~900ms |
| JD detail fetches | ~350ms |

On a 429: back off exponentially with jitter (2s, 4s, 8s + random) and retry up to 3
times before giving up on that page. Don't hammer. Set a ~12s per-request timeout so one
dead connection can't hang the whole run.

### Freshness gotcha — do NOT re-filter by the card's date

`f_TPR` already enforces freshness **server-side, on real timestamps**. The `datetime`
field on each card is **date-only**. If you re-filter client-side on it with a sub-day
cutoff (e.g. "past 24h"), you will wrongly drop yesterday-dated jobs that are still
inside the window. Trust `f_TPR` and don't second-guess it.

### Search-card selectors (the list page)

| Field | Selector |
|---|---|
| Job ID | `data-entity-urn="urn:li:jobPosting:<id>"`, or the trailing digits of the `/jobs/view/…-<id>` href |
| Title | `base-search-card__title` |
| Company | `hidden-nested-link` |
| Location | `job-search-card__location` |
| Posted date | `datetime="…"` |

An empty page (zero cards) means end of results — stop paginating.

Returns HTML, one `<li>` per posting. Each card carries
`data-entity-urn="urn:li:jobPosting:<id>"` — that ID is the key for the detail call.
Card text also has title, company, location, posted-date.

**Radius:** the guest search has no radius param. Run separate `location` values
(e.g. London, plus the specific commuter towns they cares about) rather than trying
to widen one query.

## 2. Detail — full JD for one posting

```
GET https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/<jobId>
```

```bash
curl -s -A "Mozilla/5.0" "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4362575634"
```

Selectors that matter:

| Field | Selector |
|---|---|
| Title | `top-card-layout__title` |
| Company | `topcard__org-name-link` |
| Location | `topcard__flavor--bullet` |
| **Full JD text (incl. About Us)** | `show-more-less-html__markup` |
| Seniority / employment type / function / industry | `description__job-criteria-text` (4 items) |

The full description is what Step 3's agency-detection and company-identity checks read.
It's all here — no browser needed for that part.

## What these endpoints canNOT give you

**Employee count and the hiring-trend panel are behind auth.** Step 3's company-size cap
still needs the browser (or the company's LinkedIn page / website). So:

- **Step 1 search** → curl, always.
- **Step 3 JD read + agency detection + About Us** → curl, always.
- **Step 3 company size / hiring trend** → browser, and only for candidates that survive
  everything else. That's a handful of page-opens per run instead of dozens.

Applicant count and seniority breakdown are also usually absent from the guest view —
treat them as optional signals, not required ones.
