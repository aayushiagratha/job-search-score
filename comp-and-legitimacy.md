# Comp Reliability & Posting Legitimacy

Two extra checks that run inside Step 4, per verified survivor. Adapted from
career-ops (github.com/santifer/career-ops, `modes/oferta.md`, MIT).

**Research budget: 5 WebSearch queries total across both checks, per role.** Prefer
queries that answer more than one question. When the cap is hit, stop and mark
missing data as unavailable — do not keep digging. This is a scoring pass, not
company research.

---

## Check 1 — Compensation reliability

The advertised number is not the offer. Before treating a salary as real, classify
the employer, because published ranges are not equally trustworthy across company types.

**First: is there an advertised figure at all?**

No figure → write exactly two lines and move on:
- **Company type:** {category or Unknown} — {one evidence phrase}
- **Comp reliability:** {tier} — no advertised figure

Figure exists → do the full split below.

**Company type → how much to trust the number:**

| Company type | Reliability | Signals |
|---|---|---|
| Public / mature tech | High–Med | Structured levels, large eng org |
| Growth-stage / VC-backed | Medium | Funded, may mix base + equity + bonus |
| Early-stage startup | Med–Low | Small team, vague scope, equity-heavy |
| Enterprise / corporate | Medium | Formal HR, stable base, discretionary bonus |
| Agency / consultancy | Med–Low | Client allocation, billability pressure |
| SMB / service business | Low | Broad role, informal HR, "competitive salary" |
| Sales / commission-heavy | Low unless base explicit | OTE, uncapped, target-based |
| Recruiter / staffing listing | Low–Med | Range may be the client's budget, not the offer |
| Public sector / academic / charity | Med–High | Published bands, lower market rate |

Uncertain → mark `Unknown` and default reliability to **Low** until evidence improves it.

If the brand differs from the actual hiring entity, classify the **hiring entity**
(this is the same trap as the agency pattern in Step 3 — an agency listing's salary
range is the client's budget, not a contracted offer).

**Split the advertised figure into:**
- **Advertised range** — verbatim from the JD, quoted, never blended with research
- **Likely guaranteed base** — conservative fixed-contract estimate
- **Variable / conditional** — bonus, commission, OTE, sign-on, KPI-linked
- **Expected stable cash** — what actually recurs, pre-tax, excluding benefits
- **Non-cash** — equity, pension, insurance, L&D budget, equipment

**Reliability tier:**

| Tier | Meaning |
|---|---|
| High | Stated as base, or backed by consistent public bands |
| Medium | Plausible range, components not separated |
| Low | Number likely bundles variable / "up to" / commission |
| Unknown | No usable data |

**Low-reliability phrases** (treat the number as soft unless base is separated):
"competitive salary", "total package", "up to", "OTE", "uncapped", "including
bonus", "base + commission", "performance bonus included", or an unusually wide range.

When the number looks inflated, say it plainly:
`Advertised £45k may be £35k base + commission — confirm contract base before treating this as a £45k role.`

**Questions to put to the recruiter** (3–5, tailored — only when a figure exists):
- What is the fixed base written in the contract?
- Does the range include bonus, commission, or allowances?
- Is salary discounted during probation?
- Which components are guaranteed vs. discretionary?
- If equity is mentioned: vesting schedule and realistic expected value?

**Employment-status check** (UK example — adapt the terms to your jurisdiction). This matters
a lot if your right to work assumes *employee* status:
Flag only when the JD has explicit contractor wording ("self-employed", "umbrella
company", "inside/outside IR35", asks the candidate’s to invoice rather than be employed) **AND**
at least one corroborating omission (no benefits, no holiday/PTO, no PAYE or statutory
deductions mentioned). "Contract position" alone is NOT enough — plenty of legitimate
fixed-term *employee* roles use that phrase.

If both present:
> ⚠️ **Employment status:** This posting uses contractor/self-employed language — e.g. "{phrase}".
> Some visas assume employee status; confirm PAYE/employee status with the employer before proceeding.

Descriptive, never prescriptive. Never tell the candidate to refuse a role.

---

## Check 2 — Posting legitimacy (is this opening real?)

Is this a live opening, or a pipeline-filler / ghost post that burns an application?

**Ethical framing: present observations, not accusations.** Every signal has an innocent
explanation. She decides how to weigh them.

**Signals, in order:**

1. **Freshness** — from the LinkedIn listing: posted date / "X days ago", applicant count,
   whether Apply is live or redirects to a generic careers page.
2. **Description quality** — does it name specific tools and team structure? Are the
   requirements internally consistent (entry-level title + 5 years required = contradiction)?
   Is there a clear 6–12 month scope? What share is boilerplate vs. role-specific?
3. **Company hiring signals** — within the query budget: `"{company}" layoffs 2026`,
   `"{company}" hiring freeze`. If layoffs found, are they in *this* department?
4. **Role market context** (no queries) — is this a role that normally fills in 4–6 weeks?
   Does it make sense for the company's actual business?
5. **Repost check** — if this company + a near-identical title showed up in an earlier
   search of hers, note how many times and over what span.

**Assessment — exactly one of three:**
- **High Confidence** — multiple signals point to a real, active opening
- **Proceed with Caution** — mixed signals worth naming
- **Suspicious** — multiple ghost-job indicators; investigate before investing time

Output a small signals table: each signal, what was found, weight (Positive / Neutral / Concerning).

**Edge cases — do NOT read these as ghost signals:**
- Public sector / academic: 60–90 day timelines are normal.
- "Ongoing" / "rolling" postings: a pipeline role, not a ghost job.
- Senior / niche roles: legitimately stay open for months.
- Early-stage startups: vague JD often means the role is genuinely undefined — weight vagueness less.
- **No date available → default to "Proceed with Caution", never "Suspicious".** Absence of
  evidence is not evidence.
- Recruiter reached out directly: active recruiter contact is itself a *positive* signal.

---

## Optional — AI-buzzword vs. reality mismatch

Relevant to the candidate’s target roles (AI/marketing). Some JDs describe the company the org
*wants to be*: heavy "AI transformation / enablement / innovation" language over
infrastructure nowhere near ready for it. The role turns out to be spreadsheet cleanup
first, AI maybe later.

**Only flag when 2+ of these three hold:**
- Buzzword density outruns the role's actual scope or seniority (a mid-level IC expected
  to "drive AI transformation across the organisation")
- A team of ~5 or fewer expected to own transformation outcomes for a large org
- Legacy-heavy industry where basic digitisation is likely still incomplete

If flagged:
> ⚠️ **Buzzword/infrastructure mismatch:** Heavy AI/transformation language ("{phrases}")
> alongside {signals seen}. Day-to-day may be foundational cleanup before any AI work.
> Probe directly in interview: "What are the top 3 things this role needs to fix right now?"

This does NOT change the legitimacy tier above — a posting can be entirely real and still
oversell its AI maturity. Report it separately.
