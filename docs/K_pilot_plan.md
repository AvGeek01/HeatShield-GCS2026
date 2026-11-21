# HeatShield adult worker and campus-staff pilot plan

## Purpose and status

Run a small formative pilot to learn whether HeatShield's risk explanation,
action prompts, and city-planning views are understandable and feasible for
adults who work outdoors or support outdoor work around DTU/Rohini. This is
not a representative survey, clinical study, safety certification, or test
of whether HeatShield prevents illness.

**Recruitment status: not started.** No outreach has been sent. The team
currently has no confirmed distribution channel or partner permission.
Prepare materials only; do not post, contact workers, or install devices until
the local permission, privacy, consent, and participant-safety gates below
are complete.

## Questions the pilot can answer

1. Can an adult participant explain what the risk band and its uncertainty
   mean?
2. Can they identify an action that is both understandable and realistically
   available to them?
3. Which information channel and interface format are usable with their
   device/connectivity conditions?
4. Can a partner verify a small set of resource records and understand the
   limitations of the hotspot/optimizer output?
5. Are the demo's data source, freshness, and “synthetic versus observed”
   labels clear?

Do not use a 20–50 person convenience sample to estimate health prevalence,
city-wide demand, sensor validity across all of Delhi, intervention
effectiveness, or economic benefit.

## Eligibility, sample, and recruitment

- **Target:** 20–50 adults, age 18 or older, who voluntarily self-identify as
  belonging to one of the groups below. No employer should select or require
  participation.
- **Initial batch, if permission is later granted:** invite 5–10 adults through
  an approved partner channel. Seek representation from at least three
  participant groups before expanding. Recruitment is not underway.
- **Planning ranges:** delivery workers 5–12; construction/outdoor-site
  workers 5–12; street vendors 5–12; campus staff with outdoor duties 5–12.
  Categories overlap in real life; record only the participant's chosen
  primary category and do not claim quota representativeness.
- **Approach:** purposive, voluntary recruitment via a worker-support
  organization, authorized campus contact, or public notice with permission.
  Do not approach people while they are actively working in unsafe heat,
  require employer permission in front of a supervisor, or imply that
  employment, campus access, pay, or services depend on joining.
- **Participation:** one 8–10 minute, 12-question survey and optionally a
  short prototype walkthrough. No audio/video recording, exact GPS, name,
  phone, employer name, medical history, or diagnosis is needed.
- **Compensation:** none is assumed in this proposal. If compensation or
  refreshments are later offered, disclose terms before consent and obtain
  required approvals; do not make payment contingent on particular answers.
- **Language/access:** offer a spoken explanation and accessible display
  option. Translate and independently review Hindi or any other language
  before using it; do not present machine-translated text as reviewed.

## Recruitment message (ready-to-share draft; not distributed)

> **Voluntary HeatShield pilot feedback — DTU/Rohini**
>
> We are a student team testing an early heat-safety information prototype.
> We are inviting adults aged 18 or older who do delivery, construction or
> outdoor-site work, street vending, or campus work with outdoor duties to
> complete a short 8–10 minute survey and, if they wish, look at a prototype.
> The survey asks about work context, heat information, and access to
> practical options such as water, shade, and rest. It does not ask for your
> name, phone number, employer, exact location, or medical history.
>
> Taking part is your choice. You may skip any question or stop at any time.
> Your decision will not affect work, pay, campus access, services, or your
> relationship with any organization. The prototype is not a warning service
> or medical advice, and its demo data may be synthetic. Please participate
> only when it is safe and convenient to do so.
>
> Before sharing: the team must add an approved, monitored project contact
> method and privacy/retention details in the participant information sheet.
> Do not add a personal phone number or a participant list to this repository.

The invitation is **not ready to publish** until the team has confirmed an
authorized channel, named a responsible contact privately, approved the data
handling and retention statement, and obtained site/partner permission.
Nothing in this draft should be treated as an endorsement by DTU, an employer,
or a public authority.

## Participant flow and safety

1. **Permission gate:** confirm campus/site rules and whether the team's
   institution or partner requires ethics or other review for this activity.
   Record approvals privately; do not claim approval until received.
2. **Private screening:** explain the study; ask only whether the person is at
   least 18 and belongs to an eligible adult participant group. Do not collect
   a date of birth or copy identification.
3. **Consent:** provide [the blank consent template](./K_consent_form.md) in a
   language the person understands. Allow questions, time to decide, and
   refusal without explanation. Do not recruit through a supervisor who can
   observe an individual's choice.
4. **Survey:** use [the 12-question instrument](./K_survey_questions.md);
   participants may skip optional items or stop. Do not enter answers on
   their behalf unless they ask for assistance and agree.
5. **Optional prototype walkthrough:** use only synthetic/demo information.
   Do not capture identifiable screen recordings, photos, voice, or exact
   location. If later adding recording or public quotations, obtain separate,
   specific consent before recording or publication.
6. **Close:** thank the participant, remind them how to withdraw while a
   response can still be located, and provide only a verified contact route.
   Do not give medical advice; direct urgent symptoms to local emergency or
   health services rather than interpreting them.

## Data handling and analysis

- Configure the form so it does not request names, phone/email, employer,
  exact address/GPS, health condition, or file uploads. Do not require
  sign-in; disable email collection; test the actual respondent preview and
  response sheet before launch. Google service metadata may still be governed
  by Google's own terms, so do not promise absolute anonymity.
- Store the response sheet in an approved team-controlled account with access
  limited to the authorized team. Do not publish the response link or include
  raw responses, signed consent, recruitment lists, or contact details in
  Git, issue trackers, or presentation assets. Raw data and completed forms
  stay in approved private storage only.
- Before launch, fill the retention period and deletion date in the consent
  copy; delete raw identifiable or potentially identifying notes on that
  schedule. Keep only non-identifying aggregate counts in public materials.
- Review free-text responses for accidental identifying information; exclude
  or redact them from reports. Suppress small cells (fewer than five people)
  and avoid cross-tabs that could identify someone in a small worksite.
- Report recruitment counts, refusals if voluntarily counted without
  identifiers, missing responses, group mix, and limitations. Do not infer
  illness or causal impact from survey answers.

## Measures and stop/go checks

| Measure | Pilot method | Proposed threshold / response |
|---|---|---|
| Comprehension | Ask the participant to describe the risk band and one action in their own words. | At least 8/10 in an initial usability batch correctly explain both; if not, revise copy and retest before broader use. |
| Action feasibility | Ask whether the suggested action is available without risking pay, permission, or safety. | Report barriers, including “none available”; do not present advice as usable where participants say it is not. |
| Source transparency | Ask whether the participant can identify forecast/demo provenance and freshness. | Fix any screen where a participant mistakes synthetic data for a live warning. |
| Data quality | Separate sensor bench/field tests from participant survey. | Publish only QA-reviewed sensor results with sample size, reference, and missingness. |
| Partner usefulness | Have a partner review resource verification and a budget scenario. | Record whether they understand assumptions and what approval/information would be needed to act. |

**Stop recruitment or testing** if consent is unclear, a participant feels
pressured, site permission is absent, a privacy incident occurs, or a screen
could plausibly be mistaken for an official warning. Escalate to the team's
designated supervisor/partner contact using the privately approved protocol.

## Readiness checklist

- [ ] Confirm 2026–27 GSC/video submission requirements with the official
  portal; the public guide identifies a 2-minute project overview video.
- [ ] Obtain site and partner permission and any required institutional
  review before recruiting.
- [ ] Finalize a non-personal team contact route and response-sheet owner in
  private materials; never commit contact details.
- [ ] Set and disclose retention/deletion dates; test access controls,
  respondent preview, email collection, sign-in requirements, and form
  branching before distribution.
- [ ] Review consent and questions with a local worker-support or
  occupational-health advisor; translate and validate participant-facing
  languages.
- [ ] Rehearse the no-recording, stop/withdrawal, and urgent-symptom
  procedures.
- [ ] Only after all gates pass, let the authorized partner/team member share
  the invitation with the first 5–10 adults.

**Current recruiting result:** 0 contacted / 0 consented / 0 responses. No
recruitment was initiated because no authorized distribution channel was
confirmed. This is a preparation plan, not an outreach claim.
