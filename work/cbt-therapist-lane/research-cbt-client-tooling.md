# CBT Client Tooling Research

Date: 2026-07-04

Scope: comparative research for a possible Ariadne CBT client toolkit. This is
not a PRD and not a clinical protocol. The focus is the tooling a CBT client
normally needs between sessions: thought records, action plans / homework,
behavioral experiments, exposure practice, activity and mood monitoring,
session prep, review loops, and export/share workflows. AI therapy products are
included only where they clarify the product landscape.

## Executive Read

The premise is supported if framed as an adjunctive CBT practice toolkit with a
literature-grounded assistant, not as a replacement therapist. The evidence and
market both point to the same gap: people need fast, private, structured CBT
practice in real life, while therapist-facing platforms are better at assigning
tasks than at creating a rich client-owned workspace.

I did not find an open-source harness mature enough to replace Ariadne. FreeCBT
/ Quirk is the strongest open-source reference, but it is intentionally narrow:
quick thought capture, cognitive distortions, and alternative thoughts. The
newer `cbt-llm-kit` is directly relevant as a schema/prompt reference for
LLM-guided thought records, daily check-ins, and pattern analysis, but it is a
tiny repo with no evidence of production maturity. These are reusable ideas, not
drop-in lane replacements.

The first Ariadne slice should not be a broad "mental health app". It should be
a schema-first CBT record store plus one excellent guided thought-record flow,
then homework / action-plan tracking, behavioral experiments, exposure ladders,
and activity monitoring.

## 1. Competing Products And Services

### Open Source Candidates

**FreeCBT / Quirk**

FreeCBT is a GPL React Native / Expo fork of Quirk, built as a CBT thought diary
for iOS and Android. It is quick and discreet, and explicitly avoids coupling
thought capture to mood tracking or condition-specific flows. It also has a
Bulgarian translation. The design notes are unusually relevant: keep it focused,
avoid bloat, treat thoughts as highly sensitive data, avoid manipulative
engagement loops, and prioritize data-loss prevention above ordinary product
features.

Implication for Ariadne: reuse the constraints, not the whole app. It argues for
quick capture, skippable fields, local/private data, export, and no mandatory
mood gate before thought work. It does not cover therapist/lane orchestration,
corpus-grounded guidance, homework planning, behavioral experiments, or exposure
review deeply enough to replace the Ariadne lane.

**cbt-llm-kit**

`cbt-llm-kit` is the closest open-source "LLM harness" I found. It defines a
12-step guided thought record, daily check-ins, pattern analysis, local JSON
records, a schema, question script, and CBT cheat sheet. Local inspection shows
the record schema includes situation, automatic thought, emotions before/after,
physical sensations, behavior, evidence for/against, alternative thought,
cognitive distortions, safety behavior, core beliefs, location, and people
involved.

Implication for Ariadne: very useful as a reference for record schemas and
agent workflow boundaries. It is not enough as a product base: the public repo
is very small, has no production UI, no broader CBT tool surface, and no clear
safety/clinical governance layer.

**CBTree, Rephrame, and small thought diary repos**

CBTree describes itself as a free, open-source thought-record journal. Rephrame
is a very small offline-first PWA described in GitHub topics as a local private
CBT journal with no account/server/analytics. Other repos, such as a FastAPI
thought diary, exist but appear to have very low adoption and incomplete
feature sets.

Implication for Ariadne: these reinforce that the open-source need exists, but
none look like a mature harness to adopt wholesale.

### Commercial Client Apps

**Clarity / CBT Thought Diary**

Clarity positions itself as an all-in-one mental-health app: mood tracking,
thought reframing, AI journaling/chat, guided journals, programs/courses,
assessments, reports, and wellness content. Its public site claims 3M+ downloads
and 60+ guided exercises, and App Store metadata shows a high rating and a
self-help/educational disclaimer.

Implication for Ariadne: validates demand for the bundle of thought records,
mood/activity tracking, guided exercises, insights, and AI support. It also
shows the danger of drifting into a broad subscription wellness product where
the CBT lane loses precision.

**MindShift CBT and anxiety-focused apps**

MindShift CBT and similar anxiety apps emphasize practical tools such as thought
journals, fear ladders / exposure hierarchies, breathing, and anxiety education.

Implication for Ariadne: exposure ladders and fear-facing logs should be a
first-class tool family, not hidden inside generic journaling.

**Feeling Great, Wysa, Woebot, Youper**

AI-guided CBT and mental-health companions show that users understand the
"pocket therapist" framing, but they also surface risk. Wysa has the most
evidence-heavy positioning and FDA breakthrough-designation claims. Feeling
Great leans strongly on TEAM-CBT and has aggressive outcome marketing. Woebot's
direct-to-consumer app was retired in 2025, which is a cautionary signal about
business continuity and sensitive data continuity.

Implication for Ariadne: AI can guide structured practice, but the product
should avoid pretending to be therapy and should make export/delete/data
continuity boringly reliable.

### Therapist And Clinic Platforms

**Quenza**

Quenza is the closest commercial "tool orchestration" analog. It lets
clinicians create protocols, schedule interventions, assign homework/tasks,
track progress, share session summaries, comment, and exchange files. It
explicitly names behavioral activation schedules and exposure exercises as
tasks clients can complete between sessions.

Implication for Ariadne: its useful pattern is "assigned structured activities
with progress review", not chat. Ariadne can implement the client-owned side:
records, action plans, evidence review, and therapist-share export.

**SimplePractice, TheraNest, TheraPlatform**

These are mainly practice-management/client-portal systems: scheduling,
paperwork, telehealth, billing, messages, and sometimes worksheets.

Implication for Ariadne: they are not the thing to copy for CBT skill practice.
They matter only if we later need export formats or therapist collaboration.

### Worksheet And Knowledge Libraries

**Therapist Aid, Psychology Tools, Beck Institute, NHS, Think CBT**

These sources converge on a taxonomy:

- thought logs / thought records
- cognitive restructuring and Socratic questioning
- activity charts, activity scheduling, pleasure/mastery ratings
- graded task assignments
- behavioral experiments
- exposure hierarchies and exposure logs
- session prep, action-plan review, feedback, and relapse planning
- psychoeducation / models / handouts

Implication for Ariadne: the CBT lane needs a tool taxonomy, not only a corpus
picker. The literature corpus should ground explanations and prompts, while
structured tools capture durable user state.

### Substitute Workflows

Users already substitute with paper worksheets, fillable PDFs, Notes/Obsidian,
spreadsheets, screenshots sent to therapists, reminders/calendar, mood trackers,
and generic journaling apps.

Implication for Ariadne: the bar for the first tool is not "full therapy app".
It is "less annoying than paper and less ambiguous than a blank note".

## 2. Community Signals

The community signal is anecdotal, but the pattern is clear across Reddit,
reviews, and app positioning.

Users want:

- phone-in-pocket capture, especially in public or during behavioral
  experiments
- simple thought records without lots of unrelated features
- free or low-cost access to basic CBT tools
- privacy, local storage, passcodes, export, and no surprise data sharing
- the ability to share useful summaries with a therapist
- reminders that support practice without becoming engagement manipulation
- "practice" / "exercise" language rather than shaming homework language

Users dislike:

- subscriptions or paywalls around basic thought-record functions
- paper or spreadsheet workflows when they are out of the house
- losing records or not being able to recover/export them
- apps that become another chore
- too many simultaneous habits, trackers, badges, and streaks
- workflows that force mood tracking before the user can do thought work

Therapist-community signal:

- homework non-compliance is expected and should be debugged collaboratively
- tasks should be small, concrete, meaningful, and easy to start
- worksheets are less likely to be completed when they are generic or not tied
  to an in-session insight
- review of what happened and what got in the way is part of the intervention

Product implication: Ariadne should ask "what got in the way?" without blame,
record partial attempts, and make completion less important than useful
learning.

## 3. Science And Expert Evidence

### Homework / Practice Matters, But Friction Is Real

CBT homework is normally defined as structured therapeutic activities completed
between sessions. Review literature categorizes homework into psychoeducation,
self-assessment, and modality-specific work such as exposure. Reported barriers
include pen-and-paper friction, unclear instructions, time burden, forgetting,
not understanding the rationale, and failure to anticipate obstacles.

A 2017 JMIR paper proposes six features for mobile apps supporting CBT homework
compliance: therapy congruency, fostering learning, guiding therapy, connection
building, emphasis on completion, and population specificity. A 2025 BMC
Psychology paper summarizes meta-analytic homework effects: both quality and
quantity of homework engagement predicted post-treatment outcomes, with Hedges'
g around 0.78-0.79 in the cited 2016 meta-analysis.

Product implication: the app should not merely store assignments. It should
explain the rationale, make the task doable, adapt difficulty, review barriers,
and help the client learn from partial completion.

### Core CBT Tool Families Are Stable

The major CBT app/tool sources repeatedly identify cognitive restructuring,
behavioral activation, exposure, and problem solving as fundamental CBT
techniques. Thought records are the canonical cognitive restructuring tool.
Behavioral activation needs activity schedules/logs and pleasure/mastery
ratings. Exposure needs hierarchies, planned trials, safety-behavior tracking,
and review. Session/action-plan notes need a way to carry learning into the
next review.

Product implication: the schema layer should start with reusable primitives:
`situation`, `automatic_thought`, `emotion_rating`, `behavior`,
`evidence_for`, `evidence_against`, `balanced_response`, `planned_action`,
`attempt`, `barrier`, `learning`, `next_step`, and `shareable_summary`.

### Mobile And Momentary Interventions Are Promising

Standalone smartphone CBT-based ecological momentary interventions have been
reviewed across 26 studies and found deliverable, helpful/satisfying to users,
and associated with improved well-being or reduced symptoms, although study
quality was heterogeneous.

Product implication: a desktop-only Ariadne flow misses a major use case. For
the prototype, this is acceptable, but the data model should anticipate quick
capture from phone/browser later.

### The Mental-Health App Marketplace Is Weak On Evidence And Privacy

A systematic assessment of 98 self-guided CBT depression apps found only 28
offered at least four evidence-based CBT techniques. Cognitive restructuring was
common, but suicide-risk resources were present in only about a third. Privacy
policies were widespread, yet 80% stated data sharing with third-party service
providers.

Product implication: Ariadne can differentiate sharply by being local-first,
explicit about data, exportable, and narrow about safety boundaries.

## 4. Product Implications For Ariadne

### Decision

Proceed with Ariadne integration. Do not pause for an external OSS harness. Use
FreeCBT / Quirk as product-constraint inspiration and `cbt-llm-kit` as a schema
/ workflow reference. Build our own lane primitives because Ariadne needs model
routing, corpus selection, structured records, UI reflection, safety policy,
Bulgarian register, and future tool orchestration.

### Recommended MVP Order

1. **CBT record store**
   - Local-first structured records owned by the user.
   - Explicit export/delete path.
   - No corpus payload in git.
   - Stable schemas for thought records, assignments, experiments, exposure,
     activity logs, and summaries.

2. **Guided thought record**
   - Start with quick 3-column mode and full 7-column mode.
   - Do not require mood tracking first.
   - Include "save partial" and "come back later".
   - Let the persona guide, but require user confirmation before storing or
     rewriting user content.

3. **Practice / action-plan tracker**
   - Prefer "practice", "exercise", or "action plan" over "homework" in user
     copy.
   - Track planned task, rationale, when/where, obstacle plan, attempt,
     completion, barrier, and learning.
   - Review "what got in the way?" without blame.

4. **Behavioral experiment planner**
   - Prediction, experiment, safety behaviors to drop, result, learning, next
     experiment.
   - This is a natural next tool after thought records.

5. **Exposure ladder and exposure log**
   - Fear ladder / hierarchy, SUDS ratings, safety behaviors, planned exposures,
     repeated trials, anxiety curve, learning.
   - Needs stronger safety and scope boundaries.

6. **Activity and mood monitoring**
   - Activity chart with pleasure/mastery or values/alignment ratings.
   - Mood is useful but should not be mandatory everywhere.

7. **Session prep / review**
   - Goals for next session, important events, action-plan review, notes to
     therapist, exportable summary.
   - Useful even when Ariadne is not connected to a real therapist.

8. **Corpus-grounded micro-guidance**
   - When a tool opens, the persona should automatically select the CBT corpus
     and show the active corpus in UI.
   - Retrieval should support the current tool: e.g. thought-record guidance,
     action-plan troubleshooting, behavioral experiment rationale.

### Non-Goals For First Prototype

- No broad "AI therapist" claim.
- No disorder-specific full protocols before core primitives are stable.
- No streak-driven engagement loops.
- No hidden cloud sync or unclear analytics.
- No automatic modification of user records by the model.
- No merging CBT corpus with medicine or offsec corpora.
- No literature/corpus artifacts in git.

### UX Constraints

- Make the first screen the actual tool, not a landing page.
- Keep capture fast enough for use immediately after an event.
- Let users skip unknown fields and preserve partial records.
- Store therapist-share summaries separately from private raw notes.
- Reflect selected persona/model/corpus in UI after persona selection.
- Keep Bulgarian natural and therapeutic, not translated/manual-like.
- Present the assistant as a CBT-informed guide/tooling layer, not a therapist.

### Risks To Validate

- Ariadne is currently desktop/local-server oriented; CBT practice often needs
  phone-in-pocket capture.
- Users may want therapist collaboration/export more than standalone analysis.
- AI-guided thought challenging can feel invalidating if too fast or too
  confident.
- Structured tools can become heavy; the user signal strongly favors simple
  entry and partial completion.
- Safety routing must be explicit for self-harm, abuse, crisis, medication, and
  scope boundaries.

## 5. Source Notes

- FreeCBT GitHub: GPL React Native / Expo CBT app, fork of Quirk, quick and
  discreet thought diary, Bulgarian translation, privacy/product constraints.
  https://github.com/erosson/freecbt
- FreeCBT about page: simple open-source front door; thoughts stay on phone,
  future cloud sync would need client-side encryption.
  https://freecbt.erosson.org/about/
- Quirk GitHub: strong design notes on avoiding bloat, avoiding bad incentives,
  treating thoughts as highly sensitive data, and prioritizing data integrity.
  https://github.com/flaque/quirk
- `cbt-llm-kit`: 12-step LLM-guided thought records, daily check-ins, pattern
  analysis, local JSON records; useful reference, tiny adoption footprint.
  https://github.com/arktnld/cbt-llm-kit
- CBTree: free/open-source thought-record app signal.
  https://kylehgc.github.io/CBTree/
- Rephrame GitHub topic listing: small offline-first CBT journal signal.
  https://github.com/topics/cognitive-behavioral-therapy?l=javascript&o=desc&s=stars
- Clarity / CBT Thought Diary: all-in-one CBT self-help journal with thought
  reframing, mood tracking, AI journaling/chat, guided exercises, and courses.
  https://www.thinkwithclarity.com/
- Clarity App Store page: self-help/educational disclaimer and privacy claims.
  https://apps.apple.com/us/app/clarity-cbt-self-help-journal/id1010391170
- Quenza for Therapists: protocols, homework assignments, progress tracking,
  behavioral activation schedules, exposure exercises, shared notes, comments.
  https://quenza.com/quenza-for-therapists
- Therapist Aid Thought Log: centrality of thought logs and their core fields.
  https://www.therapistaid.com/therapy-worksheet/thought-log
- Psychology Tools worksheets: worksheets as client/therapist data capture,
  thought monitoring, activity diary, behavioral experiment worksheets.
  https://www.psychologytools.com/downloads/worksheets
- Psychology Tools CBT resources taxonomy: worksheets for assessment,
  self-monitoring, thought challenging, real-world application, progress.
  https://www.psychologytools.com/downloads/cbt-worksheets-and-therapy-resources
- Beck Institute CBT worksheet packet: activity chart, pleasure/mastery,
  graded task assignments, action-plan/session review.
  https://learn.beckinstitute.org/cms/delivery/media/MCPNPP5FFGJVDJ7C74SMXCMM5CWY
- Beck Institute thought record worksheet: 5-10 minute thought-record guidance,
  distortions, adaptive response, mood change check.
  https://beckinstitute.org/wp-content/uploads/2021/08/Thought-Record-Worksheet.pdf
- NHS Every Mind Matters thought record: 7-prompt thought record as a common CBT
  exercise; can be completed on paper, phone app, or electronic document.
  https://www.nhs.uk/every-mind-matters/mental-wellbeing-tips/self-help-cbt-techniques/thought-record/
- JMIR homework compliance review: six design features for mobile CBT homework
  apps; barriers to homework compliance.
  https://mental.jmir.org/2017/2/e20/
- BMC Psychology 2025 homework engagement study: summarizes homework engagement
  and meta-analytic effects for quality and quantity.
  https://link.springer.com/article/10.1186/s40359-025-03167-0
- JMIR mHealth 2020 EMI review: standalone smartphone CBT-based ecological
  momentary interventions can be delivered and may support daily life.
  https://mhealth.jmir.org/2020/11/e19836/
- JMIR 2021 CBT app assessment: 98 apps, limited comprehensive CBT coverage,
  weak suicide-risk resources, widespread third-party data sharing.
  https://preprints.jmir.org/preprint/27619
- JMIR 2022 implementation review: CBT mHealth techniques include cognitive
  restructuring, behavioral activation, problem solving, exposure; evidence and
  privacy details are often insufficient.
  https://www.jmir.org/2022/3/e27791/
- Center for Technology and Behavioral Health review summary: users describe
  CBT apps as "pocket therapists"; privacy, security, reliability, and data loss
  matter strongly.
  https://www.c4tbh.org/user-experience-of-cognitive-behavioral-therapy-apps-for-depression-an-analysis-of-app-functionality-and-user-reviews/
- Reddit / r/CBT app discussions: repeated demand for simple/free thought
  records, phone use during behavioral experiments, and fewer extra features.
  https://www.reddit.com/r/CBT/comments/lmg83i/what_are_some_of_the_well_known_apps_for_cbt/
  https://www.reddit.com/r/CBT/comments/1kmttc3/an_app_that_is_just_a_thought_record/
- Reddit / r/therapists homework discussion: "practice/exercises" framing,
  barrier debugging, and making tasks easier.
  https://www.reddit.com/r/therapists/comments/1ub843o/how_do_you_actually_handle_homework_noncompliance/

