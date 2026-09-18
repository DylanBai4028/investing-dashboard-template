# Cross-border tax research — worked example

**What this is.** This document is a worked example of how to research a real
cross-border tax question using this template's own dashboard — the mechanisms,
sourcing discipline, and scenario-modeling approach are real; the specific facts
below belong to an **illustrative persona**, not a real person, so this can ship
publicly. It explains tax *mechanisms* and models *illustrative scenarios* using this
template's sample portfolio numbers. It is not tax advice, not a substitute for
advice from a registered tax agent or cross-border tax accountant, and nothing here
should be relied on for an actual filing or decision with real dollars attached.
Every factual claim below is cited to a source — where a claim couldn't be verified
against a primary source directly (see the access note under Sourcing), that's said
explicitly rather than glossed over. **To adapt this to your own situation**: replace
the illustrative persona's facts in Section 1 with your own, and re-run Section 6's
table against your own dashboard's real numbers — the mechanisms and sourcing
approach carry over unchanged.

**The illustrative persona used throughout**: a New Zealand citizen who moved to
Sydney, Australia, in March 2021 on a Special Category Visa (subclass 444), still
living and working there, holding the sample portfolio this template generates
(`scripts/generate_sample_data.py`) — no real person's facts or holdings.

---

## 1. Are you already exempt from AU CGT on your shares and crypto? (Temporary resident status)

This is worth checking *first*, before anything else in this document — it reframes
everything after it. If the answer is yes, the live question changes from "what would
moving to NZ cost in CGT" to "what would cost CGT, and moving to NZ isn't currently it."

### The mechanism

Australian tax law has two separate ideas that get conflated a lot: whether you're an
Australian tax resident *at all* (the ordinary residency tests — resides test,
domicile test, 183-day test), and whether, on top of being a resident, you also
qualify for concessional **"temporary resident"** treatment. They're independent
questions. You can be an Australian tax resident under the ordinary tests (as the
illustrative persona is, having lived in Sydney since March 2021) and *separately*
qualify as a temporary resident for CGT/income purposes if you meet a specific
visa-and-social-security test.

**The temporary resident test** (ITAA 1997 s995-1(1)) requires all of:
- you hold a temporary visa granted under the Migration Act 1958, **and**
- you are not an "Australian resident" within the meaning of the *Social Security
  Act 1991*, **and**
- your spouse (if any) is not an Australian resident within that same meaning.

**Special Category Visa (subclass 444) and the protected/non-protected split.** New
Zealand citizens arriving in Australia are issued an SCV 444 on entry — it's a
temporary visa, satisfying the first limb automatically. Whether the second limb is
satisfied turns on a further split: NZ citizens who arrived **before 26 February
2001** are "protected" SCV holders and are treated as Australian residents under the
Social Security Act — they do *not* qualify as temporary residents for tax purposes.
NZ citizens who arrived **after** that date (our illustrative persona — March 2021)
are "non-protected," and generally *are* not Australian residents under the Social
Security Act, meaning they satisfy the second limb and qualify as temporary residents
— **unless** their spouse or de facto partner is an Australian citizen, permanent
resident, or protected SCV holder, which fails the third limb regardless of the
person's own visa.

**The illustrative persona's facts (for this worked example)**: non-protected SCV 444
(arrived March 2021, after the 2001 cutoff); no spouse or de facto partner who is an
Australian citizen, PR, or protected SCV holder; no current plan to apply for AU PR
or citizenship. On these facts, and on the sources found, **this persona currently
qualifies as a temporary resident for Australian tax purposes** — subject to the
sourcing caveat below, and subject to this changing the moment any of those three
facts change (a relationship with an AU citizen/PR, or a grant of AU PR/citizenship,
would end it).

### What temporary resident status actually does

- **Most capital gains are disregarded**, except gains on "taxable Australian
  property" (TAP) — broadly, direct interests in Australian real property and
  similar. Ordinary shares, ETFs, and crypto are not TAP (a large shareholding in a
  land-rich company can be an exception; nothing in the sample portfolio is close to
  that scale). This applies regardless of *where* the shares are listed — the
  illustrative holdings are US-listed securities either way, so this isn't live here,
  but it's worth being precise: it's TAP-vs-not that matters, not
  Australian-vs-foreign.
- **The 50% CGT discount is not available** to temporary residents — moot in
  practice if the gain is disregarded entirely anyway, but relevant for any TAP gain.
- **CGT event I1 (the deemed-disposal-on-departure rule, see Section 2) does not
  apply** to someone who is a temporary resident (and *only* a temporary resident —
  see the sourcing caveat) immediately before ceasing residency. The stated rationale
  across sources: the whole point of event I1 is to stop someone avoiding tax on a
  gain that *would have been* taxable in Australia by leaving before selling — but a
  temporary resident's non-TAP gains were never taxable in Australia to begin with,
  so there's nothing for event I1 to protect.
- **Practical reading for the sample portfolio**: Meridian (US-listed ETFs/shares),
  Northbridge (US-listed shares), and Crypto are all non-TAP. On the sources found,
  gains on all three are currently outside the Australian CGT net, and would very
  likely stay that way through a move to NZ made while temporary-resident status
  still holds. Kowhai and SouthernCross are superannuation-style interests, not
  ordinary CGT assets, and get their own separate treatment — covered in Section 3,
  not assumed to follow the same rule as the share/crypto holdings.

### What would end this

Any of: gaining an Australian-citizen or PR spouse/de facto partner, being granted AU
permanent residency, or becoming an Australian citizen. If any of these happens, this
section's conclusion no longer holds and the CGT event I1 analysis in Section 3
becomes the live question again — worth re-reading this document at that point, not
just once, and re-checking the facts against your own real situation, not the
illustrative persona's.

### Sourcing note (read before relying on this section)

ato.gov.au and austlii.edu.au both blocked direct automated access during this
research (HTTP 403 on every attempt) — the conclusions above are built from several
independent professional tax-advisory sources that all agree with each other and cite
the same legislative provisions (ITAA 1997 ss 104-160, 104-165, 768-915, 995-1(1)),
not from reading the primary legislation or ATO guidance directly. That's a real gap,
not a technicality — before this is ever relied on, the primary sources (ato.gov.au's
"Foreign and temporary residents" page, and the actual text of the sections cited)
should be checked directly. This section is the strongest candidate in this whole
document for "get this checked by a professional first," given how much weight it
carries.

Sources consulted:
- [Mosaic Tax Legal — "Permanently temporary: the curious case of NZ citizens living in Australia"](https://mosaictaxlegal.com.au/permanently-temporary-the-curious-case-of-nz-citizens-living-in-australia/)
- [Webb Martin Consulting — "Temporary Residents – CGT Trust Trap!"](https://webbmartinconsulting.com.au/tax-news/temporary-residents-cgt-trust-trap/)
- [Bristax — "CGT event I1"](https://bristax.com.au/cgt-articles/cgt-event-i1/)
- [Baron Accounting — "Ceasing to be an Australian Resident: CGT Event I1"](https://www.baronaccounting.com/post/individual-or-company-stops-being-an-australian-resident-cgt-event-i-1)
- [ClearTax Australia — "New Zealand Citizens in Australia: What the ATO Really Taxes Under Subclass 444"](https://cleartax.com.au/tax/specific-taxes-and-levies/taxes-under-subclass-444/)
- ATO Taxation Determination TD 2012/18 (issued 11 Jul 2012, on the related question
  of an SCV holder's status after departing Australia — referenced, not the primary
  source for the conclusions above; not indicated as withdrawn as of this research)

---

## 2. AU/NZ tax residency tests, and the DTA tie-breaker

This section covers a question that's easy to answer wrong by intuition: **what
actually has to happen to stop being an Australian tax resident, and separately, what
makes you an NZ tax resident again?** These are two independent questions with two
independent (and asymmetric) sets of tests, and — the part most often assumed
incorrectly — the tax treaty doesn't override either country's own domestic answer to
its own question.

### Ceasing Australian residency

Australia uses four tests; satisfying any *one* of them makes you a resident for that
year. Two are relevant to someone actually living and working in Sydney:

- **The resides test** — a holistic, facts-and-circumstances test: where you actually
  live, your family, your job, your social and economic ties. This is very likely the
  test that currently makes our illustrative persona an Australian resident, given
  they've been physically living and working in Sydney continuously since March 2021.
  It's also the test whose answer changes most directly if someone genuinely
  relocates — once you're no longer actually living, working, and maintaining your
  life in Australia, this test alone stops being satisfied.
- **The domicile test** — a separate, narrower test: if your legal *domicile* is
  Australia, you're deemed a resident unless you can show your permanent place of
  abode is genuinely elsewhere. This test mainly matters for people whose domicile
  *is* Australia (e.g., Australian-born, or someone who's taken deliberate legal steps
  to adopt Australia as their domicile of choice) who go overseas temporarily — it's a
  backstop against claiming non-residency while keeping Australia as your true legal
  home base. Our illustrative persona's domicile of origin is New Zealand; nothing in
  this research indicates deliberate steps toward establishing an Australian domicile
  of choice, so this test is unlikely to be the operative one here — but domicile is a
  legal, not just practical, concept and isn't something this document can determine
  with certainty; worth confirming directly if this ever becomes a real decision.
- The other two (183-day test, Commonwealth superannuation test) aren't relevant to
  this persona's situation.

**Practical reading**: ceasing Australian tax residency, for someone in this
position, is less about a specific day-count and more about the whole picture
genuinely changing — relocating your actual life (home, work, day-to-day presence)
back to NZ, not just being physically absent for a while. There's no single bright
line here the way there is on the NZ side (below); it's a "look at the whole picture"
determination, which cuts both ways — harder to game, but also harder to pin down a
precise trigger date in advance.

### Becoming an NZ tax resident again

NZ's tests are more mechanical, and — this is the part worth knowing before assuming
symmetry with the AU side — **easier to trigger than to escape**:

- **The 183-day test**: physically present in NZ for more than 183 days in *any*
  rolling 12-month window (not the tax year) makes you NZ tax resident, backdated to
  the first day of that window. Two separate trips adding up to 184 days inside a
  rolling year is enough — it doesn't need to be one continuous stay.
- **The permanent place of abode (PPOA) test**: operates independently of the
  day-count test. If you maintain a dwelling in NZ you habitually return to, this
  test can make you resident even without hitting 183 days — courts weigh the whole
  pattern (a dwelling, continuity of use, intention, family/social ties), not a
  checklist.
- **Ceasing NZ residency, by contrast, requires *both***: more than 325 days absent
  from NZ in a rolling 12-month period, **and** loss of a permanent place of abode
  there. This asymmetry is real and worth internalizing: NZ residency is easy to
  re-acquire (183 days) and comparatively hard to shed again (325 days absent, plus no
  PPOA) — relevant background if a future NZ stay isn't intended to be permanent.

**Practical reading**: if you move back to NZ with any real intention of staying,
you're very likely to become NZ tax resident quickly — within a matter of months, via
the 183-day test alone, well before Australia's own "did your whole life actually
move" question necessarily resolves the same way. A period of dual residency (both
countries treating you as resident simultaneously) is a realistic scenario, not an
edge case — which is exactly what the tie-breaker below exists for.

### The DTA tie-breaker — and what it does *not* do

When someone is a tax resident of both countries at once, Article 4 of the
Australia–New Zealand Double Tax Agreement resolves which country gets primary
taxing rights under the *treaty*, via a sequential test: permanent home available in
only one country → if unclear, centre of vital interests (closer personal and
economic ties) → if still unclear, habitual abode → then nationality → then mutual
agreement between the two tax authorities as a last resort.

**The nuance that's easy to get wrong**: winning the tie-breaker for NZ does not, by
itself, mean you stop being an Australian resident under Australia's own domestic
law. The treaty tie-breaker only governs *treaty* outcomes (which country's taxing
rights prevail, relevant for double-tax relief) — Australia's own CGT event I1
(Section 3) is triggered by ceasing to be a resident under Australia's *domestic*
residency tests above, not by the treaty tie-breaker landing on NZ. In practice this
means the more directly relevant question for event I1 is still "has your resides-
test answer actually changed," not "who wins the DTA tie-breaker" — the tie-breaker
matters most for double-tax relief during any window of genuine dual residency, not
for pinpointing when the deemed-disposal trigger fires.

### Sources consulted
- [ATO — Residency tests](https://www.ato.gov.au/individuals-and-families/coming-to-australia-or-going-overseas/residency-tests) (linked, not directly fetchable — see sourcing note in Section 1; this section draws on secondary summaries of the same tests)
- [AusTax AI — Australian Tax Residency: 4 ATO Tests Explained](https://austaxai.com.au/guides/australian-resident-for-tax-purposes)
- [NZTaxTools — NZ Tax Residency Rules 2026: 183-Day Test, 325-Day Test, Permanent Place of Abode + DTA Tie-Breaker](https://nztax.tools/tax-insights/nz-tax-residency-rules/)
- [James Coleman — Residence Disputes under DTA tie-breaker provisions](https://www.jhcoleman.co.nz/blog/residence-disputes-under-dta-tie-breaker-provisions/)
- [TaxTonic — Dual tax residents – breaking the tie and tug of wars](https://taxtonic.co.nz/dual-tax-residents-breaking-the-tie-and-tug-of-wars/)

Same sourcing caveat as Section 1: ato.gov.au blocked direct automated access, so the
AU side rests on secondary summaries rather than the primary ATO pages. The NZ side
(IRD) was reachable via secondary sources citing the *Diamond v CIR* [2015] NZCA 613
case law directly, which is a stronger source than pure paraphrase, but still not the
IRD's own primary guidance page. Same recommendation as Section 1: verify directly
before relying on this for a real decision.

---

## 3. AU CGT event I1 — the mechanism itself, and how it maps to a real portfolio

Section 1 established that event I1 likely doesn't apply to our illustrative persona
*right now*, as a temporary resident. This section covers the mechanism on its own
terms — what it does, what it doesn't touch, and the choice available — since that's
still the relevant picture for the day (if it ever comes) temporary-resident status
ends.

### The mechanism

When an individual stops being an Australian tax resident, CGT event I1 deems them to
have disposed of every CGT asset they hold **except** taxable Australian property
(TAP), at market value, on the day residency ceases. The point of the rule is to stop
someone avoiding Australian CGT on an already-accrued gain simply by leaving before
selling.

**Taxable Australian property** is a defined set of five categories, the two relevant
ones being: direct interests in Australian real property, and indirect interests in
"land-rich" entities (broadly, foreign or resident entities where you hold a
non-portfolio interest — generally 10%+ — in an entity that's predominantly Australian
real property by value). Ordinary shareholdings, ETF holdings, and cryptocurrency are
not TAP under either category. Nothing in the sample portfolio is close to the scale
or structure that would trigger the land-rich indirect-interest category.

### Mapped to a real portfolio (using this template's sample platforms)

- **Meridian, Northbridge (US-listed shares/ETFs), Crypto** — none of these are TAP.
  If event I1 applied (i.e., once temporary-resident status no longer covers them),
  these would be the assets swept into the deemed disposal.
- **SouthernCross** (an AU superannuation-style fund) — a member's interest in an
  Australian complying super fund is specifically excluded from CGT event I1
  entirely, independent of temporary-resident status. It isn't treated as a personal
  CGT asset that gets deemed-disposed at all; it simply stays in the fund, taxed
  under superannuation's own separate rules, unaffected by the member's personal
  residency change for this purpose. (Broader questions — what withdrawal/access
  looks like as a non-resident down the track — are a superannuation access
  question, not a CGT one, and are out of scope for this document.)
- **Kowhai** (an NZ KiwiSaver-style fund) — this is the one genuine asymmetry worth
  flagging clearly: the superannuation-specific exclusion above is tied to Australian
  superannuation law: it applies to interests in Australian complying super funds. A
  NZ-regulated KiwiSaver-adjacent scheme is not an Australian super fund, so nothing
  found in this research suggests it gets the same automatic carve-out. On the
  research so far, a fund like Kowhai would most likely be treated as an ordinary
  foreign investment — not TAP (it's not Australian real property), so currently
  covered by the temporary-resident exemption in Section 1 the same as the
  share/crypto holdings, but **not** independently excluded from event I1 the way an
  Australian super fund is. If temporary-resident status ever ends, a fund like this
  would need to be reassessed as an ordinary non-TAP CGT asset, not assumed to be
  treated like the Australian super fund.

### The deferral election

Separately from the temporary-resident exemption, an individual (not a company) can
choose, asset by asset, to disregard the CGT event I1 gain or loss entirely and
instead keep treating that asset as TAP until it's actually sold (or some other CGT
event happens to it) — deferring the tax point from "the day residency ceases" to
"whenever it's actually disposed of." This is a genuine choice with a real trade-off,
not a formality: crystallizing the gain at the deemed-disposal date locks in today's
numbers and the current tax rules, while deferring means the eventual bill depends on
the asset's value and the tax rules *at actual sale*, whenever that turns out to be —
better if the asset keeps falling or rules become more favorable, worse if it keeps
compounding upward. Both paths are modeled side by side in Section 6 rather than
assuming one is obviously better.

### Sources consulted
- [Bristax — "CGT event I1"](https://bristax.com.au/cgt-articles/cgt-event-i1/)
- [Bristax — "Taxable Australian Property"](https://bristax.com.au/tax-articles/taxable-australian-property/)
- [Baron Accounting — "Ceasing to be an Australian Resident: CGT Event I1"](https://www.baronaccounting.com/post/individual-or-company-stops-being-an-australian-resident-cgt-event-i-1)
- [CountryTaxCalc — "Moving from Australia Tax Guide 2026"](https://www.countrytaxcalc.com/tax-guides/moving-from-australia-tax-guide-2026/)
- [Andersen Australia — "CGT Leaving Australia: Essential Tax Guide for Emigrants"](https://au.andersen.com/leaving-australia-cgt-issues/)

Sourcing caveat: same as Sections 1–2 — ato.gov.au and austlii.edu.au both blocked
direct automated access, so this rests on professional secondary sources rather than
the primary legislation (ITAA 1997 Division 855 for TAP, s104-160/104-165 for event
I1 itself) or the ATO's own guidance pages. **The KiwiSaver-style-fund finding above
(not covered by the same super-fund exclusion as an Australian fund) is a reasoned
inference from how the exclusion is described, not a directly confirmed ruling on
foreign retirement schemes specifically** — flagged as the single least-certain claim
in this section, worth the most scrutiny before relying on it.

---

## 4. NZ FIF regime — and two findings worth checking against your own portfolio

If you're NZ tax resident (Section 2) and not exempt some other way, the FIF regime
governs how NZ taxes overseas share/ETF/crypto holdings — not on realised gains like
Australia's CGT, but on a formula-based *deemed* return each year, regardless of
whether anything was actually sold.

### The mechanism

FIF applies once the total cost of a NZ tax resident's foreign investment fund
interests exceeds a **NZD $50,000 de minimis threshold at any point in the income
year**, measured on historical cost, not current market value — a portfolio bought for
$40k that's since grown to $80k is still under the threshold; one bought for $60k that's
since fallen to $30k is over it. Once over the threshold, two calculation methods are
available (the same method must be used for all FIF holdings in a given year, and the
taxpayer generally picks whichever gives the lower figure):

- **Fair Dividend Rate (FDR)**: deemed income of 5% of the portfolio's opening market
  value on 1 April (the NZ tax year start) — taxed whether or not the portfolio
  actually returned 5%, went up, or went down that year.
- **Comparative Value (CV)**: taxes the actual change in value plus dividends received,
  minus additional purchases during the year — closer to a real economic return, and
  the only method that can produce a nil or negative result in a down year (FDR can't
  go below zero).

### Two findings worth checking, illustrated against the sample portfolio

**1. The "Australian exemption" doesn't apply to holdings like these.** NZ exempts
shares in an Australian tax-resident company listed on the ASX from FIF entirely
(taxed like NZ shares instead — on realised gains, not deemed). Worth checking for
any AU broker holdings specifically: if they're ASX-listed shares in Australian
companies, this exemption applies; if they're US-listed shares/ETFs held via an AU
broker's US market access (as the sample Meridian holdings are), it doesn't — the
exemption looks at what the underlying company is and where it's listed, not which
broker the shares sit in.

**2. The transitional resident exemption is worth checking against your own timeline.**
New Zealand exempts most foreign income — FIF included — for 48 months for a
"transitional resident": a new migrant, or a returning New Zealander who has been
overseas for **10 years or more**. Our illustrative persona left New Zealand in March
2021; a return any time in the next several years would fall well short of the
10-year gap the exemption requires — worth checking against your own actual years
overseas, since this one genuinely depends on the specific gap.

**Net effect (for the illustrative persona)**: becoming NZ tax resident while holding
a Meridian/Northbridge/Crypto portfolio above NZD $50,000 in historical cost would
mean ordinary FIF treatment (FDR or CV, your choice each year) applies from day one —
no Australian-shares exemption and no transitional-resident grace period cushion it.
**A KiwiSaver-style fund like Kowhai is a different question**: if it's already a
NZ-domiciled scheme, not a foreign one from NZ's perspective, FIF (a regime for
*foreign* investment funds) shouldn't apply to it at all once you're NZ resident
again — it would simply become an ordinary NZ investment, not requiring any special
research beyond what's already established elsewhere in this document.

### Sources consulted
- [NZTaxTools — "FIF Tax NZ: Overseas Investment Tax Rules, Rates & $50k Threshold"](https://nztax.tools/tax-insights/fif-tax-overseas-investments-guide/)
- [Become.nz — "NZ FIF Rules: 2026 Changes, Thresholds, FDR, CV, RAM Methods"](https://www.become.nz/articles/fif-rules-nz-overseas-investment-tax-guide)
- [Tax Technical (IRD) — "Exemption for interests in an ASX-listed company"](https://www.taxtechnical.ird.govt.nz/new-legislation/act-articles/taxation-international-investment-and-remedial-matters-act-2012/applying-the-fif-rules/exemption-for-interests-in-an-asx-listed-company)
- [FIF.NZ — "FIF exemptions NZ: ASX shares, ETFs & PIEs"](https://fif.nz/guides/fif-exemptions/)
- [William Buck NZ — "What tax exemptions apply to transitional residents?"](https://williambuck.com/nz/news/business/general/transitional-residents/)
- [BDO NZ — "Tax residency: New Zealand transitional residency unpacked"](https://www.bdo.nz/en-nz/insights/tax/tax-residency-new-zealand-transitional-residency-unpacked)

Sourcing caveat: the "Tax Technical" source is IRD's own technical commentary site
(a step closer to primary than the general advisory-firm articles used elsewhere in
this document), reachable directly this time. The core IRD guidance pages
(ird.govt.nz proper) were not attempted directly given the pattern of blocked access
on equivalent AU government sites — worth a direct check before relying on this.

---

## 5. US estate tax exposure — often the biggest single number in this exercise

This is unrelated to residency or moving anywhere — it's a live exposure for anyone
holding US-situs assets as a non-US person, and it's worth reading even if the AU/NZ
questions above don't apply to you at all.

### The mechanism

A non-resident alien (a non-US person) gets only a **US$60,000 exemption** against US
estate tax on US-situs property — a small fraction of the multi-million-dollar
exemption a US person gets. Above that, rates start at 18% and climb quickly to 40%.
This isn't inflation-adjusted, hasn't moved in decades, and applies regardless of AU
or NZ tax residency — it's purely a function of holding US-situs assets while being a
non-US person.

**What counts as US-situs**: direct shares in US corporations, and US-*domiciled*
ETFs (a US-domiciled ETF is itself a US corporation for this purpose) — both are
US-situs regardless of who holds them or where the account is. An ETF tracking the
same index but domiciled in Ireland (common for UCITS funds sold to non-US investors)
is a foreign corporation and is not US-situs. **Beneficial ownership is what
determines this, not the custodian** — holding US shares through a broker's own
custodial/nominee structure, rather than directly on the US share register in your
own name, makes no difference to situs; the IRS looks through to who actually owns
the asset.

**Crypto is a genuine unsettled question, not a clear answer either way.** There's no
specific IRS guidance on crypto's estate-tax situs. The closest applicable rule is a
catchall for intangible property with a US "issuer" (or the entity closest to an
issuer being US tax resident) — decentralized assets without a single identifiable US
issuer (Bitcoin, Ethereum, and similarly structured tokens) sit awkwardly against
that rule, suggesting they're *less* likely to be characterized as US-situs than a
direct US share, but this is stated as uncertainty, not a finding — nothing found in
this research resolves it definitively.

### Mapped to the sample portfolio

- **Northbridge** (~US$65k cost basis of US-listed shares) and **Meridian's** US-listed
  holdings are all US-situs on the sources above — direct US corporate/ETF exposure,
  full stop.
- **Crypto** — genuinely unclear, per above.
- **Kowhai, SouthernCross** — neither is a US asset; not in scope for US estate tax
  at all.

### Treaty relief — and the one open question that matters most here

The **US–Australia estate tax treaty (1953)** is a real, significant mitigant:
instead of the bare $60,000 NRA exemption, it extends a *proportional* share of the
much larger exemption a US person would get, to someone who is "domiciled in"
Australia (not a matter of citizenship — you don't need to be an Australian citizen
for this). **There is no equivalent estate tax treaty between New Zealand and the
US** — someone domiciled in NZ instead would be back to the bare $60,000 exemption,
no treaty cushion.

This is where Section 2's domicile discussion becomes directly financially relevant,
not just an academic residency-test distinction: the treaty's protection turns on
being domiciled in Australia specifically, and *domicile* (a legal-intent concept —
broadly, the place you treat as your permanent home with no fixed intention to
leave) is a different, higher bar than ordinary tax residency. Someone can be
unambiguously an Australian tax *resident* while whether they're Australian-
*domiciled* for this treaty's purposes stays genuinely unclear, depending on facts
(intentions, ties, whether deliberate steps have been taken toward treating Australia
as permanent) that aren't something a document like this can determine. **This is the
single highest-value thing in this entire research phase to get a real cross-border
estate planning opinion on** — the difference between treaty-protected and the bare
$60,000 exemption, applied to a meaningful chunk of US-situs holdings, is not a
rounding error.

### Sources consulted
- [3tej — "The $60,000 Line: US Estate Tax on Non-Residents Who Own US Stocks"](https://3tej.com/blog/us-estate-tax-non-residents-60000-threshold)
- [Skybound Wealth — "US Estate Tax for Non-Residents: Do Your ETFs & Stocks Qualify?"](https://www.skyboundwealth.com/technical-guides/u-s-estate-tax-rules-for-non-residents)
- [US Tax Talk — "US Estate Tax - What is 'Situs'?"](https://us-tax.org/2024/02/01/us-estate-tax-what-is-situs-location-of-assets-makes-a-world-of-difference/)
- [US Tax Talk — "5 U.S. Estate Tax Surprises For Nonresident Alien Investors"](https://us-tax.org/2025/06/19/5-u-s-estate-tax-surprises-for-nonresident-alien-investors/)
- [Asena Advisors — "The US Australia Estate Tax Treaty Explained"](https://asenaadvisors.com/blog/international-estate-planning-the-u-s-australia-estate-tax-treaty-explained/)
- [SF Tax Counsel — "How Australian Investors Can Utilize the U.S.-Australia Estate Tax Treaty"](https://sftaxcounsel.com/blog/us-australia-estate-tax-treaty-australian-investors/)
- [US Tax Team NZ — "US Tax on a Kiwi Estate?"](https://www.usatax.nz/post/us-tax-on-a-kiwi-estate)

Sourcing caveat: same pattern as earlier sections — irs.gov and the actual treaty
text (available via irs.gov/pub/irs-trty/austtech.pdf, found but not directly
fetched) weren't reachable directly; this rests on professional secondary sources.
Given this section carries the largest dollar exposure and the least certain
open question (domicile) of anything in this document, it's the strongest single
candidate for actual professional advice before relying on any of it.

---

## 6. AU→NZ move scenario model

This is illustrative, not a forecast and not a filing-ready number. It uses this
template's sample portfolio (pulled directly from the dashboard's own pipeline) so
the figures are grounded in a real calculation rather than invented placeholders, but
every dollar figure below depends on facts that will keep changing if you adapt this
to your own real portfolio — market prices, your actual holdings, and (most of all)
whether the finding in Section 1 still holds by the time this is ever relevant to you.

### Scenario A — moving to NZ today, on today's facts

Section 1's finding is the direct answer to the question this whole exercise is
built around ("what happens if I move back to NZ and sell my portfolio"): **on
today's facts, likely nothing, AU-CGT-wise.** As a temporary resident, CGT event I1
doesn't apply — Meridian, Northbridge, Crypto, and Kowhai all stay outside the
Australian CGT net, the same way they already are today. SouthernCross is separately
excluded from event I1 regardless of temporary-resident status (Section 3). This is
the realistic answer for as long as the three facts in Section 1 (visa, spouse,
PR/citizenship) stay as they are.

### Scenario B — what the mechanism would produce if temporary-resident protection didn't apply

This exists to actually answer the "how big is the number" part of the original
question, for the version of the future where Section 1's protection is no longer in
play (for instance, sometime after gaining AU PR or citizenship). No specific future
date is assumed for that change; the figures below are simply "what the
deemed-disposal gain would be, before any CGT discount," at today's sample numbers
and at two illustrative future points assuming the portfolio keeps growing.

**Today's sample numbers**, per-platform unrealized gain (value minus cost basis,
from the dashboard's own reconstruction):

| Platform | Value | Cost basis | Unrealized gain |
|---|---:|---:|---:|
| Northbridge | $451,956.95 | $64,250.22 | $387,706.73 |
| Meridian | $351,467.17 | $187,684.80 | $163,782.37 |
| Crypto | $150,064.98 | $55,353.60 | $94,711.38 |
| Kowhai | $251,479.63 | $216,824.45 | $34,655.17 |
| **Total in-scope for event I1** | **$1,204,968.73** | **$524,113.07** | **$680,855.66** |
| SouthernCross (excluded regardless — Section 3) | $801,910.55 | — | not in scope |

**If this happened today**: a deemed gain of roughly **$680,900**, before any
discount.

**Illustrative future points** (assuming, for illustration only, the in-scope
holdings keep compounding at 10%/year — a round number for illustration, not a
projection of actual future returns, which have been far more volatile than that
historically):

| Timing | Illustrative in-scope value | Illustrative cost basis (unchanged) | Illustrative deemed gain |
|---|---:|---:|---:|
| Today | $1,204,969 | $524,113 | ~$680,856 |
| +3 years | ~$1,604,400 | $524,113 | ~$1,080,300 |
| +5 years | ~$1,940,500 | $524,113 | ~$1,416,400 |

**On the CGT discount**: this table deliberately shows the *undiscounted* gain, not a
discounted one. The 50% discount only applies to gain accrued while you're an
*ordinary* Australian resident (not foreign, not temporary) — apportioned by days for
any asset held across a mix of residency statuses. Every day counted in the table
above would currently be a temporary-resident day, which attracts no discount at
all; the discount only starts accruing from whatever future date (if any) temporary-
resident status actually ends. Without a real date for that, computing a specific
"with discount" figure would invent more precision than the facts support — the
honest statement is that the real number, if this scenario ever becomes live for you,
would be somewhere below the undiscounted figures above, by an amount that depends
entirely on timing this document can't know in advance.

**On the tax rate**: the table shows the *gain*, not a tax bill. AU resident marginal
rates for 2026-27 run 30% ($45,001–$135,000) and 37% ($135,001–$190,000), plus a 2%
Medicare levy, rising further above that — so a gain of this size stacked on top of
other income would land at a meaningfully higher effective rate than the numbers
above alone suggest, entirely dependent on what else is in your income that year and
which brackets the gain actually falls into. This is illustrative arithmetic, not a
computed liability — an actual figure needs an actual tax return, not a document like
this one.

### The deferral election path

Separately from all of the above: Section 3 covered that an individual could elect,
asset by asset, to disregard the event I1 gain entirely and keep treating an asset as
taxable Australian property until it's actually sold. Under this path, **nothing in
the tables above crystallizes at the move date at all** — no deemed gain, no tax
point, nothing to calculate today. The eventual liability (if any) depends entirely
on the asset's value and your residency/discount position whenever it's actually
sold, which could be years away or never. This path doesn't have an "illustrative
number" the way Scenario B does, by design — that's the whole point of deferring:
today's numbers stop being the relevant ones. It's included here as a real, live
choice, not a footnote to Scenario B.

### What this section doesn't do

It doesn't pick a "better" path — that depends on your actual expectations for where
these assets are headed, your actual future income, and what actually happens to your
residency status, none of which this document can know. It doesn't attempt FX
projections, doesn't model a KiwiSaver-style fund's underlying NZD/AUD conversion at
a future date beyond noting the same principle applies, and doesn't touch the
locked/liquid split some funds carry (a liquidity question, not a tax one — see
`pipeline/lib/config.py`'s `ILLIQUID_PLATFORMS` comment for how this template treats
that approximation).

---

## Adapting this to your own real situation

If you're using this template with your own real platforms and holdings:

1. Replace the illustrative persona's facts in Section 1 with your own (visa/
   residency status, spouse, PR/citizenship plans) — this is the section that
   changes the whole document's conclusion, so get it right first.
2. Re-run Section 6's table against your own dashboard's real numbers once your own
   exports are wired in — the query is just "value minus cost basis, per platform,"
   already computed by `run_dashboard.py` for the dashboard's own Overview tab.
3. Treat every citation above as a starting point, not a finished answer — tax law
   changes, and several sources here couldn't be verified against primary government
   guidance directly (see each section's sourcing note). Get anything with real
   dollars attached checked by a registered tax agent or cross-border tax accountant
   before acting on it.
