# Fitness criterion: the cancellation confirmation surface (UI button + response payload) clearly communicates to the user that access continues until period_end and is not lost on click

**Source REQ(s):** REQ-001, REQ-002
**Judge:** persona-judge (manual workflow — see `fitness/README.md` "How to run a persona-judge rubric")
**Threshold:** >= 8/10

> **WARNING TO THE JUDGING AGENT:**
> Research (JudgeBench) shows naively-written rubrics drop judge accuracy
> from 55.6% (no rubric) to 42.9% (bad rubric) — 13 points *worse* than
> nothing. Use the structured sub-dimensions below verbatim. Do not collapse
> into "overall impression". Cite at least one passage from the inputs
> supporting every score.

## How to run

See `fitness/README.md` "How to run a persona-judge rubric" for the manual workflow (fresh Claude session, paste rubric, score with citations, compare to threshold). That section is the single canonical place for the procedure; this file does not duplicate it.

## Inputs

The judge examines:
- `src/components/CancelSubscriptionButton.tsx` (or equivalent — the rendered button + confirmation modal)
- `src/components/SubscriptionStatusView.tsx` (or equivalent — the post-cancellation state display)
- A screenshot or rendered HTML of the confirmation flow (request from implementer if not in repo)
- The API response payload spec/example for `POST /api/subscription/cancel` (from `specs/subscription-cancellation/spec.md` REQ-001 and the integration test `test_cancel_api_returns_200_and_cancellation_record`)

## Audience archetype

**Audience archetype: paying customer about to click "Cancel"**

- A paying customer mid-subscription who has decided to stop renewing.
- Likely worried that clicking "Cancel" will immediately revoke access to features they paid for through the end of the current period.
- Reads UI labels once; if the meaning is ambiguous they will either cancel reluctantly or stop and contact support.
- Does NOT read terms-of-service modals or developer-facing API docs.
- Cares about: (a) "will I lose access right now?" (b) "exactly when does access actually end?" (c) "is this reversible if I change my mind?"

## Rubric

### Sub-dimension 1: continuity_clarity (weight 0.40)

How clearly does the surface communicate that access continues until `period_end` rather than ending immediately on click?

Score 1-10 with these anchors:

- **10** — The pre-click button copy explicitly says access continues until the dated end of the current billing period (e.g. "Cancel — your access continues until June 30, 2026"). The post-click confirmation reaffirms the same date. The user could not reasonably believe access ends "now".
- **7** — The continuity is communicated but requires the user to read a secondary line (e.g. small tooltip or modal body). The date is shown but not contextually anchored ("you'll lose access on [date]" with no indication this is the END of the paid period).
- **4** — Continuity is mentioned somewhere on the page but is easy to miss; the primary button copy says only "Cancel subscription" with no temporal context. The user would have to hunt for the period_end information.
- **1** — The button copy or confirmation modal implies immediate revocation ("Cancel now and lose access", or a generic "Are you sure? You will no longer be able to access premium features."). No mention of `period_end` continuity.

The judge must cite at least one passage (UI string, modal copy, label) from the inputs supporting the score.

### Sub-dimension 2: date_concreteness (weight 0.25)

Is the actual `period_end` timestamp shown in user-friendly form, or is it hidden behind generic language?

Score 1-10 with these anchors:

- **10** — A concrete, locale-aware date is shown both before AND after the user clicks Cancel (e.g. "June 30, 2026 at 2:32 PM your local time"). The date format does not leak technical terminology.
- **7** — A concrete date is shown but only after clicking Cancel (the pre-click button doesn't carry it); or the date is shown but in UTC / ISO format that a non-technical user has to parse.
- **4** — A relative date is shown ("until the end of your current period") but no concrete calendar date. User cannot tell exactly when access ends.
- **1** — No date is shown anywhere on the surface.

Cite a passage.

### Sub-dimension 3: reassurance_against_immediate_loss (weight 0.20)

Does the language affirmatively reassure that no immediate access loss occurs on click — addressing the user's primary fear directly?

Score 1-10 with these anchors:

- **10** — The confirmation modal contains an explicit reassurance sentence (e.g. "You will keep all premium features until [date]. We will not charge you again."). Both the access-continuity and the no-future-charge points are made affirmatively.
- **7** — The continuity point is made but the no-future-charge point is implicit (or only in fine print).
- **4** — Reassurance is implied through layout/iconography but not stated in plain English.
- **1** — No reassurance text. The modal reads like a destructive action confirmation ("Are you sure? This cannot be undone.") without addressing the temporal nuance.

Cite a passage.

### Sub-dimension 4: post_cancel_status_display (weight 0.15)

After successful cancellation, does the UI continue to show the user (a) their current status (`cancelled_active`) and (b) the date access ends, so the user is not left wondering whether the action succeeded?

Score 1-10 with these anchors:

- **10** — The subscription management view immediately reflects `cancelled_active` with a concrete date and a clear visual indicator (e.g. a banner: "Subscription cancelled — premium access until June 30, 2026"). The user can navigate away and come back and still see this.
- **7** — Status is shown but the date is shown elsewhere (a separate "expiry" field) so the user has to assemble the two pieces.
- **4** — Only a transient toast/success message is shown; the persistent view returns to a generic "manage subscription" state with no status indicator.
- **1** — No visual indication that cancellation succeeded; the user must guess from absence of a "Cancel" button.

Cite a passage.

## Aggregation

Final score = (continuity_clarity × 0.40) + (date_concreteness × 0.25) + (reassurance_against_immediate_loss × 0.20) + (post_cancel_status_display × 0.15)

(Weights sum to 1.0.)

## Pass/fail

Pass if:
- final score >= 8.0
- AND no sub-dimension scored below 5

The second clause prevents a strong dimension from masking a weak one (e.g. great date display but the button copy still says "lose access").

## Re-run policy

If first pass produces a score within ±0.5 of threshold (i.e. 7.5–8.5), run the judge a second time on the revised artifact and require the score to not decrease before declaring pass. This catches the regression case where addressing one weakness opens another.
