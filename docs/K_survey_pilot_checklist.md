# HeatShield student survey pilot checklist

Use this checklist before distributing the production survey. The pilot is a usability check, not a source of research findings. Do not commit pilot responses, names, contact details, response-sheet links, or form links to this repository.

## Before the five-person pilot

- [ ] Run `buildHeatShieldSurveyForms()` in the Apps Script project from [K_form_builder.gs](./K_form_builder.gs); review the generated form titles, bilingual text, sections, and age branching.
- [ ] In the survey form settings, verify email collection is off, sign-in is not required, and one-response-per-person restriction is off.
- [ ] Apps Script disables email collection and the one-response restriction; it does not set the account/organization sign-in restriction. Verify sign-in access in the Google Forms UI before sharing.
- [ ] Confirm the 18+ “No” path ends politely without exposing research questions. Google Forms may save the gate-only navigation response; exclude it from eligible-response counts and confirm no research answers are present.
- [ ] Confirm the separate pilot sign-up form is not connected to the survey's response destination.
- [ ] Do not post or broadly distribute either form during the pilot.

## Test with five students

Include **five college students aged 18 or older**, with **at least two Hindi-first readers**. Ask each participant to test on their normal phone/browser where possible, independently, and without the survey author explaining questions. Tell them this is a usability test and not to enter real contact details or identifying information.

For each participant, record only a pilot code (P1–P5), language preference (English-first/Hindi-first/bilingual), device category (phone/computer), start and finish time, elapsed minutes, and question numbers that were confusing. Do not record names, roll numbers, phone numbers, emails, health disclosures, or test answers in project files. Keep any working notes private and delete them when the wording fixes are complete.

| Pilot code | Language preference | Device | Start time | Finish time | Minutes | Confusing question numbers / wording issue | Fix made |
|---|---|---|---|---|---:|---|---|
| P1 |  |  |  |  |  |  |  |
| P2 |  |  |  |  |  |  |  |
| P3 |  |  |  |  |  |  |  |
| P4 |  |  |  |  |  |  |  |
| P5 |  |  |  |  |  |  |  |

After each test:

- [ ] Confirm completion is close to the stated 4 minutes; if most pilot participants take materially longer, shorten or clarify before launch and update the invitation's estimate.
- [ ] Ask which questions were unclear, uncomfortable, hard to answer, or difficult to read on a phone. Do not ask for personal health details.
- [ ] Check that participants understood “last summer (April–June 2026),” the day-scholar/hostel options, commute-time bands, the “select all that apply” items, and the difference between heat-alert use and information sources.
- [ ] Ask Hindi-first testers whether the Hindi wording is natural and equivalent to the English, especially the consent, opt-out, symptoms, and location-sharing items.
- [ ] Verify keyboard/screen-reader labels and grid usability if a tester uses assistive technology or reports an accessibility issue.
- [ ] Revise confusing wording; test the changed question(s) again with at least one student before launch. Keep a brief, non-identifying change note in private team notes.
- [ ] Exclude all pilot/test submissions from the production analysis. Clear pilot test data before launch if using the final form; do not mix it into the production sheet.

## Production settings and privacy sign-off

- [ ] **Do not collect email addresses** in the survey form. Turn off “Collect email addresses.”
- [ ] **Do not require sign-in.** Turn off organization restrictions and the “Limit to 1 response” setting. Google Forms cannot guarantee one response per person under this anonymous configuration; the form asks participants to answer once and the team screens cautiously for obvious duplicates.
- [ ] The age-gate “No” option routes to the end page; test that it does not reach research questions. If Forms records the gate-only response, exclude it from eligible-response counts.
- [ ] Test that the consent checkbox is required and the survey cannot proceed without it.
- [ ] Test the final-page link opens the **separate** pilot sign-up form. Confirm the survey answers do not contain or join to sign-up contact details.
- [ ] Choose a **team-owned Google Sheet** as the survey response destination. Share it only with the three team members who need access; verify the sheet and form are not link-shared and no broader group has inherited access.
- [ ] Ensure the signup form uses a different response destination with the same restricted access. Never copy email/contact answers into the survey sheet or join the sheets.
- [ ] Confirm the live form is accepting responses and inspect the respondent view on a phone and desktop. Keep the generated form and sheet links in the private team workspace only.
- [ ] Secure campus permission for survey circulation and posters; confirm the academic calendar and avoid exam weeks.
- [ ] Record the five completed pilot checks and privacy/settings sign-off before public distribution. Do not claim the form is live or tested until these checks are actually completed.
