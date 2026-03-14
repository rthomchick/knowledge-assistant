Version 0.6.3 | March 1, 2026

Richard Thomchick | Senior Product Manager, Personalization and Buying Groups

# Table of Contents

[Introduction](#_Toc221808880)

[Section 1. Governing Principles](#section-1.-governing-principles)

[Section 2. Buying Group Roles: What We're Identifying](#section-2.-buying-group-roles-what-were-identifying)

[Section 3. Signal Taxonomy](#section-3.-signal-taxonomy)

[Section 4. Buying Group Roles: Definitions and Behavioral Hypotheses](#section-4.-buying-group-roles-definitions-and-behavioral-hypotheses)

[Section 5. Signal-To-Role Mapping](#section-5.-signal-to-role-mapping)

[Section 6. identification model](#section-6.-identification-model)

[Section 7. Conflict Resolution & Edge Cases](#section-7.-conflict-resolution-edge-cases)

[Section 8. Signal Recency & Decay](#section-8.-signal-recency-decay)

[Section 9. Negative Signals & Exclusions](#section-9.-negative-signals-exclusions)

[Section 10. Data Dependencies & Integration Status](#section-10.-data-dependencies-integration-status)

[Section 11. Governance & Evolution](#section-11.-governance-evolution)

[References](#references)

[Appendix A. Signal Cross-Reference Matrix](#appendix-a.-signal-cross-reference-matrix)

[Appendix B. Confidence Scoring Examples](#appendix-b.-confidence-scoring-examples)

[Appendix C. Glossary](#appendix-c.-glossary)

[Changelog](#changelog)

# PURPOSE

This document is the canonical reference for how we identify website visitors as members of specific buying group roles in service of personalizing web experiences for ServiceNow's 48K Target Account List[^1]. It is intended to enable every team touching personalization, including engineering, content, analytics, campaign ops, and product management, to answer three questions without ambiguity:

1.  What data do we observe? (Signal inventory)

2.  What does that data mean? (Interpretation logic)

3.  What do we do with that meaning? (Activation thresholds)

# Intended Audience

**Primary:** The practitioners who implement and operate personalization, including Adobe Target specialist, tagging engineers, AEP architects, content strategists building variants, and analytics teams measuring outcomes.

**Secondary:** Product managers, campaign leads, and stakeholders who need to understand what personalization can and cannot do today, and what governs those boundaries. They need the decision logic without the implementation wiring.

**Not the audience:** Executive leadership. They need a one-page summary or a slide. Trying to make this doc palatable to execs is what causes signal definition documents to lose their technical rigor.

# What's in This Document

This document covers the complete signal-to-classification pipeline across three layers of buying group identification, each of which has its own signals and unlocks different personalization capabilities[^2]:

1.  Account identification (is this visitor from a target account, and what do we know about that account?)

2.  Buying group stage recognition (where is this account's buying group in its journey?)

3.  Individual role classification (what role does this person play in the purchasing decision?).

The five MVP buying group roles (Champion, Economic Buyer, Influencer, User, and Ratifier)[^3] receive the deepest treatment, as role identification is the most complex layer and the primary focus of the personalization program. Account-level and buying group stage signals are covered as foundational layers that both enable role identification and support personalization in their own right.

**NOTE:** This work operates as a complement to the centralized D&A buying group classification model, which assigns roles using CRM, sales, and marketing activity data. Where a D&A-assigned role exists, the signals described here serve as confirmation or enrichment. Where it does not, they provide the primary basis for inference.

# Expected Outcomes

When this document is done well, the following things become true:

-   An engineer can implement a new signal end-to-end without a meeting, because the doc tells them: source system, collection method, schema, weight, decay, and activation rule.

-   A content strategist can design a new experience variant by looking up what roles or segments it maps to and what confidence level triggers it.

-   An analyst can build a measurement framework because the doc clearly separates classification confidence from engagement intensity.

-   A new team member can onboard to the personalization program in a day, not a month.

-   Stakeholder debates about "why didn't this visitor get personalized?" can be resolved by pointing to the decision tree, not by re-litigating strategy in a meeting.

# Section 1. Governing Principles

A short set of declarative design decisions that constrain everything else in the document. Not an executive summary or a narrative introduction. Rather, a set of statements that any team member can internalize and use to make judgment calls independently.

**Principles to articulate:**

Buying group personalization is TAL-only (48K accounts). Non-TAL visitors receive brand awareness content.

Web signals complement the centralized D&A classification model; they do not replace it. Where CRM-assigned roles exist, web signals confirm or enrich.

The identification pipeline is layered: account → buying group stage → role. Each layer unlocks progressively more specific personalization.

When classification confidence is insufficient, the system defaults to a broader personalization level (role → buying group stage → solution interest → brand awareness) rather than guessing.

Role classification confidence is distinct from engagement scoring. Confidence measures how certain we are about who someone is. Engagement measures how active they are.

Signal weights represent testable hypotheses about role behavior, not permanent values. They are designed to be tuned with real data.

The system must handle the full spectrum of visitor knowledge, from completely anonymous to CRM-confirmed, gracefully at every stage.

**Rationale:** Previous versions opened with GTM transformation context or phase capability comparisons. Both are useful background, but they don't give practitioners a decision-making framework. When an engineer, content strategist, or analyst faces an ambiguous situation, they should be able to reference these principles and make a sound call without escalating.

The following principles govern all signal definition, interpretation, and activation decisions in this document. They are designed to be internalized by team members working on personalization so that judgment calls can be made independently and consistently.

**TAL-Only Scope.** Buying group identification and personalization apply exclusively to ServiceNow's 48K TAL (Target Account List). Visitors from non-TAL accounts receive default experiences. No buying group signals are captured and no role classification is attempted for non-TAL traffic. This constraint reflects the GTM principle of focusing on the right accounts, not more accounts.[^4]

**Complement, Not Replace.** The signals and classification logic in this document operate as a complement to the centralized D&A buying group classification model, which assigns roles using CRM, sales engagement, and marketing activity data. Where the D&A model has assigned a role, web signals serve as confirmation or behavioral enrichment, but they do not override. Web-based behavioral inference is the primary classification method only when a D&A role assignment is absent for a given visitor.

**Layered Identification.** The identification pipeline operates in three layers:

-   Account identification

-   Buying group stage recognition

-   Individual role classification

Each layer has its own signal sources and unlocks progressively more specific personalization capabilities. A visitor does not need to be classified at every layer to receive value. Each layer supports meaningful personalization independently. Account-level personalization is achievable today; role-level personalization depends on data maturity.

**Graceful Degradation.** When classification confidence is insufficient at any layer, the system defaults to the next broader personalization level rather than guessing. The fallback cascade is: **role-specific content → role-influenced content → solution-interest content → account-level content → brand awareness**. A well-chosen fallback is a deliberate design decision, not a failure state. Serving generic content to an ambiguous visitor is preferable to serving the wrong role-specific content.

**Confidence Is Not Engagement.** Role classification confidence measures how certain we are about who a visitor is. Engagement scoring measures how active they are. These are distinct concepts that serve different purposes. A visitor can be high-engagement but low-confidence (active on the site but role-ambiguous), or high-confidence but low-engagement (CRM-confirmed role but infrequent visitor). Personalization decisions use confidence to determine what content to serve and engagement to determine urgency and prioritization.

**Testable Hypotheses.** Signal weights represent testable hypotheses about how each buying group role behaves on the web, not permanent values. Every weight has a documented rationale rooted in a behavioral hypothesis about the role it identifies. Weights are initial estimates designed to be validated against real traffic data and recalibrated when evidence warrants. This makes tuning informed rather than arbitrary. When a weight changes, the hypothesis it tests should be re-evaluated alongside it.

**Full-Spectrum Design.** The system must handle the complete range of visitor knowledge, from a completely anonymous first-time visitor to a CRM-confirmed buying group member with a known role, engagement history, and account context, and must do so with an appropriate, intentional response at every point on that spectrum. No visitor state should produce an undefined or broken experience. The identification pipeline and fallback cascade are designed so that every visitor receives the best experience their available data supports.

# Section 2. Buying Group Roles: What We're Identifying

An overview of the three-layer identification model. This section establishes the conceptual architecture before diving into signal details. Each layer is introduced with its core question, its primary data sources, and the personalization it enables.

Layer 1: Account Identification

Core question: Is this visitor from a TAL account? What do we know about that account?

Primary signals: IP/domain matching (Demandbase or 6sense), authentication/login, CRM account match, cookie/device graph

Personalization unlocked: Industry-specific content, company-size-appropriate messaging, solution recommendations based on account whitespace, account-level buying group stage awareness

Current status: Available today via third-party enrichment + CRM TAL flag

Layer 2: Buying Group Stage Recognition

Core question: Where is this account's buying group in its journey for a given solution category?

Primary signals: BG stage from D&A model (Targeted → Engaged → Prioritized → Qualified), number of identified BG members, engagement score aggregation, active opportunity status

Personalization unlocked: Stage-appropriate content (education vs. acquisition vs. progression), campaign cohort alignment, urgency and messaging tone

Current status: Available via CRM intermediary (account + BG level, not individual)

Layer 3: Role Classification

Core question: What role does this individual play in the buying group?

Primary signals: CRM role assignment (via Kafka integration, March 15), zero-party data (form fills), behavioral signal inference, job title/seniority

Personalization unlocked: Role-specific content experiences, targeted CTAs, role-appropriate depth and framing

Current status: Behavioral inference available now (medium confidence). CRM-confirmed roles require the Kafka integration (Snowflake → AEP), going live March 15.

**Rationale:** This section replaces the "Current Capabilities vs. Future State" comparison from v0.9. Instead of a phase-based framing that expires when infrastructure changes, the pipeline model is durable: the layers remain the same even as the data sources underneath them evolve. It also establishes that account-level personalization is valuable and achievable now, which prevents the document from reading as a plan for something that mostly can't be done yet.

Before identifying a visitor's role in a buying group, the system must first determine whether the visitor belongs to a target account and if so, where that account's buying group stands in its journey. These are not preliminary steps to get out of the way. They are distinct identification layers, each with its own signals and each capable of driving meaningful personalization independently. The pipeline operates as a series of progressively deeper questions, where each layer builds on the one before it.

## Layer 1: Account Identification

**Core question:** Is this visitor from a Target Account List account, and what do we know about that account?

Account identification is the foundation of the pipeline and the gating criterion for all buying group personalization. The system resolves a visitor to a specific account using IP/domain matching via Demandbase, authenticated login, or CRM contact match. Once an account is identified, the system checks TAL membership. If the account is on the TAL, the visitor enters the buying group personalization pipeline. If not, the visitor receives default experience and no buying group signals are captured (per Principle 1).

For identified TAL accounts, even without knowing anything about the individual visitor, the system has access to account-level attributes: industry vertical, company size, geographic region, existing customer status, product footprint, and solution fit scores from the D&A model. These attributes support meaningful personalization today, including industry-specific content, company-size-appropriate messaging, solution recommendations based on account whitespace, without requiring any personal identification.

**Current status:** Available today via third-party enrichment and CRM TAL flag. This is the most mature layer of the pipeline and the one with the broadest visitor coverage across TAL traffic.

## Layer 2: Buying Group Stage Recognition

**Core question:** Where is this account's buying group in its journey for a given solution category?

Once an account is identified, the system can determine the buying group's stage within each of ServiceNow's four solution categories (IT, CRM, Employee Experience, Security & Risk). The centralized D&A model classifies buying groups into four stages based on engagement signals across marketing and sales channels:[^5]

  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Stage**         **Description**
  ––––––––- ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Targeted**      No engagement from any buying group members in the last 180 days. The buying group exists on paper but has not yet shown interest. Personalization at this stage focuses on education, shaping how the account thinks about their challenges before a buying cycle begins.

  **Engaged**       At least one engagement from any member in the last 180 days. Early interest is present. Personalization shifts toward acquisition, connecting challenges to ServiceNow capabilities and encouraging deeper exploration.

  **Prioritized**   Two or more members (or a hand-raiser) engaged in the last 90 days with no active opportunity in the solution. The buying group is showing real momentum. Personalization emphasizes progression: proof points, competitive differentiation, and paths to direct engagement with sales.

  **Qualified**     The buying group has at least one accepted member converted into a Stage 1 opportunity. Sales is actively engaged. Web personalization at this stage supports the active deal by reinforcing value propositions, surfacing relevant case studies, and reducing friction in the evaluation process.[^6]
  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

Buying group stages map directly to campaign cohort alignment. Education cohort campaigns target accounts in the Targeted stage, Acquisition campaigns target the Engaged stage, and Progression campaigns target the Prioritized stage. This alignment ensures that web personalization and campaign messaging reinforce each other rather than conflict.[^7]

**Current status:** Available at the account and buying group level via the CRM intermediary. Stage data flows from D&A through CRM to AEP on a 24- to 48-hour batch cycle. Individual-level stage attribution will be available with the Kafka integration (Snowflake → AEP), going live March 15.[^8]

## Layer 3: Role Classification

**Core question:** What role does this individual play in the buying group?

Role classification is the deepest and most complex layer of the pipeline. It attempts to determine whether an individual visitor is acting as a Champion, Economic Buyer, Influencer, User, or Ratifier within their buying group. Unlike the first two layers, which rely primarily on data from centralized models, role classification on the web depends on a mix of data sources with varying availability and reliability.

The strongest role signal is a CRM role assignment from the D&A classification model, which uses job title, function, and solution-category relevance to assign roles. When this data is available for a visitor, it serves as the authoritative classification. The next strongest source is zero-party data (information the visitor provides directly through form fills, such as job title and role). When neither CRM nor zero-party data is available, the system falls back to behavioral inference: interpreting the visitor's on-site behavior patterns against role-specific signal profiles to estimate which role they most likely occupy. Sections 4 and 5 define these behavioral hypotheses and signal mappings in detail.

Role classification unlocks the most targeted personalization capabilities: role-specific content experiences (e.g., showing the Economic Buyer an ROI calculator while showing the User a product tour), targeted CTAs aligned to role-appropriate next actions, and content framing that matches the visitor's likely concerns and decision criteria.

**Current status:** Behavioral inference is available today at medium confidence. Zero-party data is available when visitors submit forms. CRM-confirmed individual role assignments require the Kafka integration[^9] (Snowflake → AEP), going live March 15, which will enable near real-time role data at the contact level. The D&A model's February MVP classification is limited to three roles (Economic Buyer, Champion, and Influencer), with all others defaulting to Unclassified.[^10]

## How the Layers Interact

The three layers are sequential but not all-or-nothing. A visitor who is identified at Layer 1 (account) but not Layer 3 (role) still receives account-level personalization; they are not treated the same as a completely unknown visitor. This is the practical application of Principle 3 (Layered Identification) and Principle 4 (Graceful Degradation): each layer adds specificity, and the system delivers the best experience the available data supports at any given moment.

In practical terms, this means the vast majority of TAL visitors today will be personalized at Layer 1 and Layer 2, with a smaller subset receiving Layer 3 role-specific experiences. As the D&A classification model matures and the Kafka integration enables individual-level role data, the proportion of visitors classified at Layer 3 will increase. The pipeline architecture is designed so that this maturation requires expanding capability, not restructuring the identification model.

# Section 3. Signal Taxonomy

A complete, structured inventory of every signal available to the web personalization layer, organized by signal type. Pure reference: no interpretation, no weighting. This is the periodic table of the personalization program.

**Signal types to inventory:**

**3.1 Behavioral Signals**: Actions the visitor takes on-site

Page views by content type (pricing, technical docs, case studies, ROI calculators, etc.)

Asset downloads (whitepapers, briefs, datasheets)

Demo/trial requests

Product tour engagement (completion, depth)

Video engagement

Site search terms

Session patterns (depth, duration, frequency, recency)

Solution area exploration breadth vs. depth

Community/forum engagement

**3.2 Zero-Party Signals**: Information the visitor explicitly provides

Form fills (job title, role, company, use case, solution interest)

Webinar/event registration fields

Chat/bot interactions with self-declaration

Preference center selections

**3.3 Firmographic Signals**: Account-level attributes from external sources

Third-party enrichment (industry, company size, revenue, tech stack) via Demandbase/6sense

CRM account data (TAL status, existing customer, product footprint)

Account whitespace and solution fit scores from D&A

**3.4 Professional Profile Signals**: Individual-level attributes (title, seniority, function, role assignment)

**3.5 Engagement & Relationship Signals**: Cross-channel activity surfaced to the web layer

BG member engagement score (from D&A model, 0-100)

BG stage (Targeted / Engaged / Prioritized / Qualified)

Campaign history and cohort membership

Event attendance (webinars, EBC, in-person)

Sales engagement indicators (Outlook activity, CRM engagement)

**3.6 Contextual Signals**: Session-level context

Entry point and referral source

Campaign attribution (UTM parameters, ad click-throughs)

Device type and browsing context

Geographic location

Time of visit (business hours vs. off-hours)

**3.7 Negative Signals**: Indicators that suppress or exclude classification

Career page visits (job seeker pattern)

.edu email domain (academic/student)

Competitor domain identification

Support-only browsing patterns (existing customer support)

Bot/crawler indicators

**For each signal, the taxonomy table will capture:**

Signal name and description

Source system

Collection method / integration path

Latency (real-time, near real-time, batch)

Current availability status (available now / March 15 Kafka / planned)

Data owner

**Rationale:** v0.9 blended the inventory with the interpretation: "what signals exist" was tangled with "how much they're worth for each role." Separating them makes the taxonomy useful as a standalone reference. When someone asks "do we collect X?" or "where does Y come from?", they can answer it here without wading through role-specific weighting logic. The addition of engagement and relationship signals (3.4) reflects the reality that the web layer has access to cross-channel data through AEP, not just on-site behavior.

This section inventories every signal available to the web personalization layer. It is organized by signal type and is intended as a standalone reference. For each signal, the taxonomy captures what the signal is, where it originates, how it reaches the web layer, how quickly it becomes available, whether it is available today, and who owns the data. Signal interpretation (what each signal means for role identification) is covered in Sections 4 and 5. Signal weighting is covered in Section 5. This separation is intentional: when someone asks "do we collect X?" or "where does Y come from?", this section provides the answer without requiring knowledge of the role classification model.

## 3.1 Behavioral Signals

Behavioral signals are actions the visitor takes on servicenow.com. They are the primary input for role inference when CRM and zero-party data are unavailable, and they serve as confirmation or enrichment when those sources are present. All behavioral signals in this section are collected via Adobe Analytics through the AEP Web SDK and are available in real time.

All behavioral signals are collected via Adobe Analytics through the AEP Web SDK. Content type categorization is the primary differentiator between role profiles. Known gaps: scroll depth tracking not available, video completion rates inconsistent across embeds, with the migration to ePDFs (HTML-hosted), page-level engagement metrics are now available, along with PDF-specific events: PDF loaded, download from viewer, PDF internal search, and PDF print.

  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Signal**                         **Source**                  **Latency**                  **Status**                    **Owner**
  ––––––––––––––––– –––––––––––––- –––––––––––––– ––––––––––––––- –––––––––––-
  **Page views by content type**     Adobe Analytics             Real-time                    Available now                 Web Analytics

  **Asset downloads**                Adobe Analytics             Real-time                    Available now                 Web Analytics

  **Demo / trial requests**          Adobe Analytics + Marketo   RT (event); Near RT (form)   Available now                 Web Analytics / Forms

  **Product tour engagement**        Adobe Analytics             Real-time                    Available now                 Web Analytics

  **Video engagement**               Adobe Analytics             Real-time                    Partial (completion gaps)     Web Analytics

  **Site search terms**              Adobe Analytics             Real-time                    Available now                 Web Analytics

  **Session patterns**               Adobe Analytics             Real-time                    Available (no scroll depth)   Web Analytics

  **Solution area exploration**      Adobe Analytics (derived)   Real-time                    Available now                 Web Analytics

  **Community / forum engagement**   Adobe Analytics             Real-time                    Available now                 Web Analytics

  **ePDF: page loaded**              Adobe Analytics             Real-time                    Available now                 Web Analytics

  **ePDF: download from viewer**     Adobe Analytics             Real-time                    Available now                 Web Analytics

  **ePDF: internal search**          Adobe Analytics             Real-time                    Available now                 Web Analytics

  **ePDF: print**                    Adobe Analytics             Real-time                    Available now                 Web Analytics
  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-

## 3.2 Zero-Party Signals

Zero-party signals are information the visitor explicitly provides. They carry high authority for role classification because the visitor is self-declaring attributes that would otherwise require inference. The primary limitation is coverage: typical form conversion rates are 2–5% of visitors, so zero-party data is available for a small subset of traffic.

  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Signal**                                     **Source**                 **Latency**        **Status**               **Owner**
  ––––––––––––––––––––––– ––––––––––––– ––––––––– –––––––––––– ––––––––––
  **Form fills (title, role, dept, use case)**   Marketo / AEM Forms        Near real-time     Available now            Forms Team (Sneha)

  **Webinar / event registration fields**        Event Platform / Marketo   Post-event batch   Available now            Events (Tamer)

  **Chat / bot interactions**                    Chat platform              Near real-time     Planned (not in AEP)     Web Experience

  **Preference center selections**               Marketo / CRM              24–48hr batch     Available (low adopt.)   Marketing Ops
  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

## 3.3 Firmographic Signals

Firmographic signals are account-level attributes sourced from CRM, sales systems, and third-party data providers. They describe the organization, not the individual. Firmographic signals are essential for account identification (Layer 1) and provide the foundation for account-level personalization. They are relatively stable (they change infrequently compared to behavioral signals) and provide a durable baseline for classification. Individual-level attributes such as job title, seniority, department, and role assignment are covered separately in Section 3.4 (Professional Profile Signals).

  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Signal**                             **Source**        **Integration**                   **Latency**      **Status**      **Owner**
  ––––––––––––––––––– ––––––––- ––––––––––––––––- –––––––– –––––––- –––––––––
  **Third-party account enrichment**     Demandbase        AEP partner connector             Real-time        Available now   ABM Team

  **CRM account data (TAL, customer)**   Dynamics CRM      CRM connector → AEP               24–48hr batch   Available now   CRM / Sales Ops

  **Acct whitespace / solution fit**     D&A / Snowflake   CRM (current); Kafka (March 15)   Daily refresh    Available now   Data & Analytics
  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

## 3.4 Professional Profile Signals

Professional profile signals are individual-level attributes that describe the person, not the organization. They include job title, seniority level, department or function, and D&A-assigned buying group role. These signals are the primary input for firmographic role classification (the first two classification paths in Section 4) and are distinct from firmographic signals (Section 3.3), which describe the account. The distinction matters because professional profile data feeds Layer 3 (role classification) while firmographic data feeds Layer 1 (account identification). Professional profile signals become available through two paths: zero-party data from form fills (available now) and CRM contact data via the Kafka integration (March 15).

  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Signal**                                                Source                Integration               Latency              Status             Owner
  ––––––––––––––––––––––––––––- ––––––––––- ––––––––––––- –––––––––– ––––––––– ––––––––––
  **CRM contact data (title, seniority, dept, function)**   Dynamics CRM          Kafka (Snowflake → AEP)   Near RT (March 15)   March 15 (Kafka)   CRM / Sales Ops

  **D&A role assignment**                                   D&A / Snowflake       Kafka (Snowflake → AEP)   Near RT (March 15)   March 15 (Kafka)   Data & Analytics

  **Zero-party professional profile (form fills)**          Marketo / AEM Forms   Form connector → AEP      Near real-time       Available now      Forms Team (Sneha)
  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

## 3.5 Engagement and Relationship Signals

Engagement and relationship signals represent cross-channel activity that is surfaced to the web personalization layer through AEP. These signals originate outside of web behavior (in marketing campaigns, sales interactions, and events) but are relevant because they provide context about the visitor's relationship with ServiceNow beyond what on-site behavior alone reveals.

  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Signal**                             **Source**               **Integration**                   **Latency**        **Status**         **Owner**
  ––––––––––––––––––– –––––––––––– ––––––––––––––––- ––––––––– ––––––––– –––––––––
  **BG member engagement score**         D&A / Snowflake          CRM (current); Kafka (March 15)   24–48hr batch     Active (acct/BG)   Data & Analytics

  **BG stage**                           D&A / Snowflake          CRM (current); Kafka (March 15)   24–48hr batch     Active (acct/BG)   Data & Analytics

  **Campaign history / cohort**          Marketo / Dynamics       CRM connector → AEP               24–48hr batch     Available now      Marketing Ops

  **Event attendance**                   Event Platform / CRM     CRM connector → AEP               Post-event batch   Available now      Events (Tamer)

  **Sales engagement indicators**        Dynamics CRM / Outlook   CRM (current); Kafka (March 15)   24–48hr batch     Active (acct/BG)   CRM / Sales Ops

  **NPS / customer reference history**   NPS Platform / CRM       CRM connector → AEP               Batch              Available now      Customer Success
  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

## 3.6 Contextual Signals

Contextual signals describe the circumstances of a visit rather than the visitor themselves. They are generally weaker for role identification than behavioral or firmographic signals, but they provide useful session-level context that can refine classification when combined with other signal types.

  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Signal**                           **Source**                     **Latency**   **Status**      **Owner**
  –––––––––––––––––– ––––––––––––––– ––––––- –––––––- –––––––––––––
  **Entry point / referral source**    Adobe Analytics                Real-time     Available now   Web Analytics

  **Campaign attribution (UTMs)**      Adobe Analytics                Real-time     Available now   Web Analytics / Mktg Ops

  **Device type / browsing context**   Adobe Analytics                Real-time     Available now   Web Analytics

  **Geographic location**              Adobe Analytics / enrichment   Real-time     Available now   Web Analytics

  **Time of visit**                    Adobe Analytics (derived)      Real-time     Available now   Web Analytics
  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

## 3.7 Negative Signals

Negative signals indicate that a visitor should be excluded from buying group classification or that their classification confidence should be reduced. These signals are critical for avoiding wasted personalization effort and for maintaining the integrity of engagement metrics. Negative signal handling rules (including exclusion scope and hierarchy) are defined in Section 9.

  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Signal**                                **Source**                  **Latency**      **Status**               **Owner**
  ––––––––––––––––––––- –––––––––––––- –––––––– –––––––––––– –––––––––––––
  **Career page visits**                    Adobe Analytics             Real-time        Available now            Web Analytics

  **.edu email domain**                     Marketo / AEM Forms         Near real-time   Available (on form)      Forms Team

  **Competitor domain**                     Demandbase                  Real-time        Available now            ABM Team

  **Support-only browsing (3+ sessions)**   Adobe Analytics (derived)   Multi-session    Available (logic req.)   Web Analytics

  **Bot / crawler indicators**              Adobe Analytics / CDN       Real-time        Available now            Web Analytics / Platform

  **Insufficient engagement (\<30s)**       Adobe Analytics             Real-time        Available now            Web Analytics
  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

# Section 4. Buying Group Roles: Definitions and Behavioral Hypotheses

The five MVP roles with definitions, typical titles, and, critically, the behavioral hypothesis for each. What do we believe each role does on the website, and why? The hypothesis is the bridge between the role definition and the signal weights in Section 5.

**For each of the five MVP roles (Champion, Economic Buyer, Influencer, User, Ratifier):**

**Definition:** What this role does in the buying process

**Typical titles:** Job titles commonly associated with this role

**Behavioral hypothesis:** What we believe this role's web behavior looks like and why. For example: "We hypothesize that Champions consume breadth (exploring multiple solution areas, downloading case studies and competitive comparisons, and returning frequently) because their job is to build internal consensus and arm stakeholders with proof points."

**Primary indicators:** The 3-4 strongest signals for this role

**Secondary indicators:** Supporting signals that increase confidence when combined with primary indicators

**Counter-indicators:** Signals that argue against this role classification

**Relationship to D&A classification model:**

When CRM has assigned a role via the D&A model, web signals serve as confirmation or enrichment, not override

The D&A model uses title, role, and function importance for each solution category; this is the authoritative source when available

Web behavioral signals are the primary classification method only when D&A role assignment is absent

**Additional roles (future phases):** Brief mention of Executive Sponsor, Project Owner, Security Leader, Technical Validator, acknowledged but not defined in this version.

**Rationale:** Previous versions defined roles and jumped straight to signal weights without articulating the reasoning. Without the behavioral hypothesis, the weights are just numbers. You can't tune them intelligently because you don't know what assumption you're testing. When post-launch data shows that the Champion weights aren't performing, the hypothesis tells you whether to adjust the weights or reconsider the behavioral model entirely.

This section defines each of the five MVP buying group roles and establishes three classification paths for each:

-   Firmographic rules (deterministic classification from job title, level, and function when available via CRM or form fills)

-   Zero-party declaration (self-reported role information)

-   Behavioral inference (pattern-based classification from on-site behavior).

For each role, the section also articulates a behavioral hypothesis about what we believe that role's web behavior looks like and why. The behavioral hypothesis serves two purposes: a) it is the basis for signal weights in Section 5 (used when firmographic and zero-party data are unavailable), and b) it provides a confirmation layer for visitors whose role has been assigned through CRM or form data. With Kafka integration going live March 15 and lead-gen forms already capturing job title, level, and department/function, a meaningful portion of identifiable traffic can be classified through firmographic rules or zero-party data rather than behavioral inference. Behavioral inference remains essential because it covers the largest segment by volume: anonymous visitors from TAL accounts who have not yet submitted a form or been matched to a CRM contact.

**Critical principle: role classification is per-solution-category, not per-person.** A single individual can hold different buying group roles for different solution categories simultaneously. A VP of IT may be the Economic Buyer for ITSM (budget authority over that domain) and a Champion or Influencer for CRM (interested and engaged, but not the budget holder). This means that firmographic classification rules must always be evaluated in the context of a specific solution category. The title-to-role mappings below are not universal; they vary by solution. The signal-to-role mappings in Section 5 inherit this principle: a visitor's behavioral signals are interpreted relative to the solution category they are engaging with, and a visitor exploring multiple solution areas may receive different role classifications for each.

**Sub-solution granularity.** Some solution categories contain sub-solutions with meaningfully different title-to-role mappings. IT encompasses three named solutions: Autonomous Service Ops, AI + Data Orchestration, and Autonomous IT & Security. CRM encompasses Service (CSM, FSM) and Sales (SOM). The D&A model classifies roles at the solution category level, not the sub-solution level. The title mappings below include sub-solution breakdowns where available because they affect firmographic classification accuracy: a VP Data Strategy browsing AI + Data Orchestration content is a stronger Champion signal than the same title browsing Autonomous Service Ops content. When sub-solution intent can be inferred from the visitor's content consumption, it should refine the firmographic classification. The behavioral hypotheses in this section are written at the solution-category level and apply across sub-solutions.

## 4.1 Champion

**Definition:** The insider who believes in ServiceNow early and rallies the room to make the deal happen. The Champion is the internal advocate who builds the case across stakeholders, gathers proof points, and drives consensus.

**Typical titles:** Product Manager, Director, Department Head, IT Manager, Senior Manager.

**Firmographic classification:** Requires evaluation of title × function × solution category. Champions are typically Director-to-VP level in an operational or transformation function relevant to the solution category, senior enough to drive organizational change but not the ultimate budget authority. Example mappings for CRM solutions (Service and Sales): Director of Customer Service Operations, Head of Digital Transformation / Service Innovation, Director of Field Service, Customer Success Director, Director of Sales Operations, Head of Revenue Operations, Director of Sales Strategy & Planning, Director of Sales Enablement. Note that EVP/SVP/VP of Technology appears as a Champion for Service solutions; this VP-level title would be classified as Economic Buyer for ITSM. This illustrates why solution category context is essential. The D&A model classifies Champions in the February MVP using title, role, and function importance weighted by solution category. Example mappings for IT solutions: for Autonomous Service Ops, VP IT Services, VP IT Operations, Director IT Services, Platform Owner; for AI + Data Orchestration, VP Data Strategy/Data Platforms, Director Data Governance; for Autonomous IT & Security, VP IT Operations, VP IT Services, VP Automation & Orchestration, VP IT Asset Management, Director IT Ops. Note that IT Champion titles are more operationally and technically oriented than CRM Champions, which may result in heavier technical documentation engagement than the behavioral hypothesis below predicts. This should be considered when interpreting IT Champion signals.[^11]

**Behavioral hypothesis:** We hypothesize that Champions consume breadth. Their job is to build a cross-functional case for ServiceNow, which means they need ammunition for multiple audiences: case studies to show peers what's possible, competitive comparisons to preempt objections, demo experiences to build their own conviction, and content spanning multiple solution areas to understand organizational impact. We expect Champions to exhibit high return frequency (they're building a case over time, not making a one-time evaluation), broad content consumption across solution categories, and a strong preference for proof-point content (case studies, success stories, competitive analysis). Their sessions tend to be moderately deep; not the longest on any single page, but covering more ground per visit than other roles.

**Primary indicators:** Case study and success story downloads; competitive comparison page views; demo request submissions; exploration of three or more solution areas within a 90-day window.

**Secondary indicators:** High return visit frequency (3+ sessions per month); webinar registration or attendance; product tour completion; multiple asset downloads across content types.

**Counter-indicators:** Exclusive focus on technical documentation without proof-point content (suggests Technical Buyer/Ratifier, not Champion); exclusive focus on pricing and ROI content without breadth (suggests Economic Buyer); single-session engagement without return visits (Champions build cases over time).

## 4.2 Economic Buyer

**Definition:** The person with budget authority who approves the spend and makes the final call. The Economic Buyer evaluates the business case, assesses financial justification, and ultimately signs off on the purchase.

**Typical titles:** CIO, CFO, COO, VP, SVP, C-suite executives.

**Firmographic classification:** Requires evaluation of title × function × solution category. Economic Buyers hold budget authority over the specific solution domain. They are typically C-suite or EVP/SVP/VP level in the function that owns the purchasing decision for that solution category. Example mappings for CRM solutions (Service and Sales): Chief Customer Officer, Chief Operating Officer, EVP/SVP/VP Customer Service, EVP/SVP/VP of Field Service, EVP/SVP/VP of Sales / Sales Operations, EVP/SVP/VP of Operations. A title like CFO may appear as Economic Buyer for one solution and Ratifier for another. For solutions where finance owns the budget, CFO is the Economic Buyer; for solutions where finance provides compliance oversight, CFO is the Ratifier. The D&A model classifies Economic Buyers in the February MVP. Form fills that capture a C-suite or VP+ title with a function that maps to budget authority for the visitor's solution area of interest should trigger HIGH confidence Economic Buyer classification. Example mappings for IT solutions: CIO and CTO appear across all three IT sub-solutions as Economic Buyer. Additional mappings: for Autonomous Service Ops, COO; for Autonomous IT & Security, VP IT Ops, CISO, CRO. Note that the IT BG program uses "Decision Maker" as an alternate label for Economic Buyer; forms and campaign materials using "Decision Maker" should be mapped to the Economic Buyer role for classification purposes.

**Behavioral hypothesis:** We hypothesize that Economic Buyers consume depth in financial justification content but are otherwise sparse visitors. Their time is scarce, so their sessions tend to be short and targeted: pricing pages, ROI calculators, executive briefs, and business value content. They are unlikely to spend extended time on technical documentation, product tours, or how-to guides. That evaluation is delegated to others. When Economic Buyers do visit the site, they focus on the content that helps them answer "is this worth the investment?" and "what is the business impact?" We expect low page depth, short session duration, summary-oriented content focus, and low return frequency. Their engagement pattern is narrow and purposeful, not exploratory. Note: with CRM data (available via Kafka integration, March 15) and form fills providing job title and seniority, Economic Buyer classification will increasingly rely on firmographic rules rather than this behavioral hypothesis. The behavioral pattern described here is most valuable as a confirmation signal and as the fallback for anonymous senior visitors who have not yet been identified through firmographic data.

**Primary indicators:** ROI calculator usage; pricing page views; executive brief downloads; business value and CFO/CIO-targeted content views.

**Secondary indicators:** Low overall page depth per session (focused, not exploratory); short session duration; CRM-confirmed seniority level of VP or above (available via Kafka integration, March 15); zero-party declaration of a C-suite or VP title via form fill (available now).

**Counter-indicators:** Extended time on technical documentation (suggests delegation of evaluation has not occurred); community or forum engagement (too hands-on for this role); high session frequency and broad content exploration (suggests Champion rather than Economic Buyer). Note: Economic Buyer and Champion are the hardest pair to distinguish through behavioral signals alone. With job title and seniority data from CRM (via Kafka integration, March 15) or form fills (available now), this ambiguity is largely resolved: seniority is the clearest differentiator. For anonymous visitors where firmographic data is unavailable, the system should default to the broader classification when behavioral signals are ambiguous between these two roles.

## 4.3 Influencer

**Definition:** The voice that shapes opinions behind the scenes, even without formal authority. The Influencer evaluates how a solution would impact their team or function and provides input that others weigh in the decision process.

**Typical titles:** Manager, Team Lead, Business Analyst, Process Owner.

**Firmographic classification:** Requires evaluation of title × function × solution category. Influencers are typically VP-to-Director level in a function that is adjacent to (but does not own the budget for) the solution category, or in a cross-functional role that provides input to the buying decision. Example mappings for CRM solutions (Service and Sales): VP of IT / Director of Business Applications, Head of Workforce Management, VP of Product or Operations, Finance or FP&A Leader, VP of Marketing / Demand Generation, VP of Customer Success, Director of IT or Business Systems, Finance Controller. Note that Influencer titles overlap with Economic Buyer at the VP level; the differentiator is whether the function owns the budget for the specific solution. A VP of IT is likely an Economic Buyer for ITSM but an Influencer for CRM. The D&A model classifies Influencers in the February MVP. Example mappings for IT solutions: for AI + Data Orchestration, CISO, CDO/CDAO, CAIO, Head of AI CoE, Head of Data Engineering, Risk & Compliance Lead, Enterprise Architect, VP of Automation/App Dev; for Autonomous Service Ops, CISO, Enterprise Architect; for Autonomous IT & Security, VP Business Transformation, VP Security, Enterprise Architect, Strategy Realization Office (SRO). The IT Influencer title set is notably broader than CRM, with several C-suite titles (CISO, CDO, CAIO) appearing as Influencer rather than Economic Buyer because they do not hold budget authority over the specific IT sub-solution. Enterprise Architect appears as Influencer across all three IT sub-solutions, making it a particularly strong firmographic Influencer indicator for IT.

**Behavioral hypothesis:** We hypothesize that Influencers consume depth within a single solution area. Unlike Champions who explore broadly, Influencers are evaluating fit for their specific domain. They focus on use cases, product tours, best practices guides, and industry-specific content that answers "how would this work for my team?" Their browsing is more focused than the Champion's but more exploratory than the User's. We expect moderate session frequency (they check in periodically as the evaluation progresses), content consumption concentrated in one solution area, interest in webinars and thought leadership content, and moderate page depth per session. The Influencer's behavioral pattern sits between the Champion's breadth-first approach and the User's task-oriented approach.

**Primary indicators:** Use case page exploration; product tour engagement (start and progression, not necessarily completion); webinar registration or attendance; industry-specific content views within a single solution category.

**Secondary indicators:** Best practices guide views; moderate return visit frequency; content consumption concentrated in one solution area with occasional exploration of adjacent areas; moderate session duration.

**Counter-indicators:** Pricing or ROI content focus (suggests Economic Buyer); competitive comparisons and case study hoarding (suggests Champion); exclusive focus on how-to and training content (suggests User); security or compliance content focus (suggests Ratifier).

*Note: Influencer is the broadest and most ambiguous role behaviorally. When signals are ambiguous, the system should fall back to solution-interest content rather than defaulting to an Influencer classification.*

## 4.4 User

**Definition:** The hands-on operator who cares whether the solution actually works in real life. The User will interact with the platform day-to-day and evaluates it based on usability, task efficiency, and practical fit with their workflows.

**Typical titles:** Individual Contributor, Specialist, Coordinator, End User, Analyst.

**Firmographic classification:** Requires evaluation of title × function × solution category. Users are the people who will operate the solution day-to-day: frontline staff, managers of operational teams, and individual contributors in the functions the solution serves. Example mappings for CRM solutions (Service and Sales): Customer Service Manager / Supervisor, Service Agent / Support Specialist, Field Service Technician, Dispatcher / Scheduler, Account Executive, Sales Development Rep, Sales Engineer, Customer Success Manager. Note that User titles for CRM solutions include roles that would be classified differently for other solution categories; an Account Executive is a User for Sales Operations Management but might not appear in an ITSM buying group at all. The D&A model does not classify Users in the February MVP; contacts at this level default to Unclassified. Form fills capturing an operational title with a function that maps to the solution's end-user base provide the strongest firmographic path. Example mappings for IT solutions: for AI + Data Orchestration, AI Ops Manager, Data Engineer/Steward, Platform Owner/Admin; for Autonomous Service Ops, IT Manager, Service Desk Manager, IT Ops Manager; for Autonomous IT & Security, IT Ops Admin, Incident Manager, Automation Engineer, Agentic Engineer, Director IT PMO. IT User titles include emerging roles (Agentic Engineer, AI Ops Manager) that are not yet established in CRM title taxonomies. These titles should be monitored as they appear on forms and in CRM data; their presence is a strong User signal for the corresponding IT sub-solution.

**Behavioral hypothesis:** We hypothesize that Users consume task-oriented, practical content. They are asking "how does this work?" and "can I do my job with this?" rather than "should we buy this?" We expect Users to gravitate toward how-to guides, training resources, FAQs, support documentation, and community forums. Their browsing is narrow and task-specific: they search for particular capabilities, evaluate specific features, and look for evidence that the platform handles their real-world use cases. Sessions may be shorter than the Influencer's but more targeted. Users may show specific search terms related to features or workflows. They are unlikely to engage with pricing, ROI, or executive-level content. Community and forum engagement is a strong differentiator for this role: Users are the most likely to seek peer validation and practical tips.

**Primary indicators:** How-to and training content views; community and forum engagement; FAQ and support documentation visits; task-specific site search terms.

**Secondary indicators:** Product tour engagement (especially focused on specific features rather than full product overview); content consumption concentrated in a single narrow use case; CRM-confirmed title at the individual contributor level (available via Kafka integration, March 15; note: D&A model does not classify Users in February MVP); quick exits from non-operational content.

**Counter-indicators:** Pricing or ROI content engagement (suggests a decision-making role, not an operational one); case study or competitive comparison downloads (suggests Champion); exploration of multiple solution areas (Users typically focus on one domain); executive brief downloads (wrong audience level).

*Note: the User role overlaps with existing customer support patterns. A visitor who is exclusively browsing support and knowledge base content across multiple sessions may be an existing customer seeking support rather than a User evaluating a new purchase. The support-only browsing negative signal (Section 3.7) should be applied before User classification is attempted.*

## 4.5 Ratifier

**Definition:** The checkpoint ensuring the deal is sound and compliant. The Ratifier validates that the solution meets security, legal, compliance, or procurement requirements. They can block a deal but rarely initiate one.

**Typical titles:** Legal Counsel, Compliance Officer, Procurement Manager, Security Lead, CISO, Data Protection Officer.

**Firmographic classification:** Requires evaluation of title × function × solution category. Ratifiers operate in a validation or compliance capacity: they clear security, legal, financial, and procurement hurdles. Unlike other roles where seniority is the primary differentiator, Ratifier classification is driven primarily by function, with titles spanning from Director to C-suite. Example mappings for CRM solutions (Service and Sales): Chief Financial Officer, VP of Finance / FP&A Leader, Chief Information Officer, Chief Technology Officer, Head of Data Privacy / Security. Critically, several Ratifier titles (CFO, CIO, CTO) overlap with Economic Buyer titles in other solution categories. A CIO is likely the Economic Buyer for ITSM but a Ratifier for CRM. A CFO may hold budget authority for finance solutions (Economic Buyer) while providing financial compliance validation for service solutions (Ratifier). When the same title maps to both Economic Buyer and Ratifier, the solution category the visitor is engaging with, and their behavioral signals within that category, must disambiguate. The D&A model does not classify Ratifiers in the February MVP. Example mappings for IT solutions: CFO and Chief Procurement Officer appear across all three IT sub-solutions as Ratifier. Additional mappings: for Autonomous Service Ops, VP IT Finance, Legal Counsel; for Autonomous IT & Security, Director Strategic Sourcing, Legal Counsel; for AI + Data Orchestration, Compliance Officer, Legal Counsel/Data Protection Officer. IT Ratifier titles are largely consistent with CRM Ratifier titles, reflecting the cross-functional nature of the validation role. The key IT-specific addition is VP IT Finance, who may appear as Ratifier for IT solutions while holding a different role (or no role) in CRM buying groups.

**Behavioral hypothesis:** We hypothesize that Ratifiers consume validation and compliance content with high specificity and low breadth. Their job is to answer "does this meet our requirements?" rather than "should we buy this?" We expect Ratifiers to focus almost exclusively on security whitepapers, compliance and governance documentation, technical architecture and integration documentation, and any content related to data privacy, regulatory standards, or audit readiness. Their visits may be infrequent but deep within their focus area; they are thorough when they do engage. Ratifiers typically enter the evaluation later in the buying cycle (at the Prioritized or Qualified stage), so their engagement pattern often appears as a late-stage burst of activity concentrated on risk and compliance topics. They are among the least likely roles to request a demo or explore broad product content.

**Primary indicators:** Security whitepaper downloads; compliance and governance content views; technical documentation engagement exceeding 10 minutes per session; data privacy or regulatory content views.

**Secondary indicators:** Late-stage engagement timing (activity appearing after account has reached Prioritized or Qualified stage); narrow content focus (security and compliance content without exploration of other content types); CRM-confirmed title in legal, compliance, procurement, or security (available via Kafka integration, March 15; note: D&A model does not classify Ratifiers in February MVP); form fill capturing a legal, compliance, procurement, or security function (available now).

**Counter-indicators:** Demo requests (Ratifiers validate, they don't evaluate features); case study or competitive comparison engagement (suggests Champion); pricing or ROI content (suggests Economic Buyer); broad solution area exploration (Ratifiers focus on their validation domain).

*Note: a Ratifier and a technically oriented Champion can produce overlapping behavioral signals around security and compliance content. The key differentiator is breadth: a Champion who downloads a security whitepaper will also engage with case studies, competitive content, and other solution areas. A Ratifier's engagement will be concentrated almost exclusively on validation topics.*

## Relationship to the D&A Classification Model

Role classification operates through three paths, listed in order of authority.

1.  CRM role assignment from the D&A model, which classifies contacts using job title, function, and solution-category relevance. With the Kafka integration going live March 15, this data will be available in AEP at the individual contact level in near real-time. When a D&A-assigned role exists, it is the authoritative classification.

2.  Zero-party declaration through form fills. Our lead-gen forms already capture job title, job level, and department/function; these fields enable deterministic role classification at the moment of form submission, without waiting for CRM data to sync.

3.  Behavioral inference using the signal weights defined in Section 5. This path serves the largest segment by volume (anonymous TAL visitors who have not yet submitted a form or been matched to a CRM contact), but carries the lowest confidence.

The behavioral hypotheses described above serve all three paths. For CRM-classified visitors, behavioral signals confirm that the assigned role is consistent with observed behavior. This is a sanity check that can surface potential misclassifications. For form-identified visitors, behavioral signals enrich the classification with engagement context. For anonymous visitors, behavioral signals are the primary classification method. In practice, the relative volume across these paths will shift as the Kafka integration matures: more visitors will be classified through firmographic rules, and behavioral inference will increasingly serve as the fallback and confirmation layer rather than the primary engine.

The D&A model's February MVP classifies three roles: Economic Buyer, Champion, and Influencer. All other contacts default to Unclassified. This means that User and Ratifier roles have two available classification paths rather than three: zero-party data (form fills capturing title, level, and function) and behavioral inference. For these two roles, form strategy is particularly important. Capturing department/function on lead-gen forms is the most reliable path to User and Ratifier classification until the D&A model expands its role coverage.

## Jobs to Be Done by Role and Stage

Each role has distinct jobs to be done at each buying stage. These JTBD are the foundation for behavioral signal interpretation: the content a visitor consumes to accomplish their job is the signal that identifies their role. The signal weights in Section 5 are derived from these JTBD. Content that supports a specific role's job at a specific stage is a signal for that role at that stage.

**During Acquisition (Validation and Framing).** The Economic Buyer is sizing the problem, translating pains into target outcomes, and shortlisting viable approaches. The Champion is socializing a service-first narrative, collecting early proof and peer references, and recruiting allies within the organization. The Influencer is helping shape requirements and stress-testing how work will flow for their team. The Ratifier is clarifying the procurement need and path, identifying risk flags, and understanding governance, privacy, and security requirements. The User is surfacing frontline friction and must-have workflows and participating in concept workflows.

**During Progression (Value Alignment and Commitment).** The Economic Buyer is validating ROI and TCO scenarios, confirming the solution meets defined KPI goals, and understanding rollout and adoption plans. The Champion is securing executive sponsorship, standing up use cases, and orchestrating consensus across the organization. The Influencer is validating "how it works for us" use cases, running or interpreting proof of concept, and issuing recommendations. The Ratifier is ensuring standards alignment and finalizing terms, SLAs, and liability. The User is validating use-based demos and recommending adoption and training milestones.

The content and messaging that supports each role's JTBD should be designed accordingly. During Acquisition, Economic Buyer content should translate pain to measurable service outcomes and make the cost of legacy drag visible and urgent. Champion content should build the internal case for the platform shift. Influencer content should shape requirements and eliminate risk early. Ratifier content should help avoid end-stage surprises and establish boundaries for data and AI use. User content should show the art of the possible for daily work. During Progression, the messaging shifts: Economic Buyer content de-risks the investment and confirms value in quarters, not years. Champion content supports orchestrating consensus and sponsorship. Influencer content validates "how this works here." Ratifier content addresses risk, compliance, and closing terms and conditions. User content proves adoption readiness. When content is designed with a specific role and stage in mind, visitor engagement with that content becomes a high-confidence role signal.

The JTBD framework above covers the Acquisition and Progression stages, where role-specific behavior is most observable and role-level personalization is most actionable. Education stage JTBD describe what each role needs during early problem awareness before the buying cycle begins. During Education (Problem Identification), the buying group is recognizing and validating a problem. The Economic Buyer is assessing the strategic and financial impact of the problem, validating the problem against organizational goals, and determining if it warrants investment. The Champion is articulating the problem in a compelling, actionable way, rallying internal support for addressing the problem, and connecting it to strategic priorities. The Influencer is evaluating how the problem affects their team or function and beginning to form a point of view on what a solution needs to address. The Ratifier is monitoring for risk flags and governance implications that would need to be cleared if the organization pursues a solution. The User is experiencing the problem firsthand and surfacing the specific pain points and workflow friction that make the status quo unsustainable. Education-stage JTBD are sourced from the IT Buying Group Program Working Deck and generalized across solution categories. For signal definition purposes, the impact on role classification is limited: visitors from accounts in the Education/Targeted stage are unlikely to exhibit sufficient behavioral signal diversity for role classification because their engagement is typically broad and exploratory. Personalization at the Education stage operates primarily at Layer 1 (account) and Layer 2 (BG stage), not Layer 3 (role). However, these JTBD inform what content should be designed for each role at the Education stage, and visitor engagement with that role-targeted Education content becomes a signal when the account advances to Acquisition.

## Buying Group Convergence Points

Convergence points are the moments in the buying process where multiple roles must align for the deal to advance. They define where signal overlap between roles is expected and where behavioral disambiguation becomes most important. Six convergence points have been identified, with the key roles that must align at each:

  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Convergence Point**                         **Objective**                                                      **Required Roles**
  ––––––––––––––––––––––- ––––––––––––––––––––––––––––––––– –––––––––––––––––––
  **Problem Validation**                        Align on whether the problem is real, urgent, and worth solving.   Champion, Economic Buyer, Influencer

  **Requirements Framing**                      Define what "good" looks like and set evaluation criteria.         Champion, Influencer, User

  **Solution Validation**                       Confirm ServiceNow meets functional and technical needs            Champion, Influencer, User

  **Business Value Alignment**                  Align on ROI, TCO, and measurable outcomes.                        Champion, Economic Buyer, Influencer

  **Risk, Compliance & Technical Validation**   Clear security, legal, and procurement hurdles.                    Champion, Economic Buyer, Ratifier

  **Final Commitment**                          Achieve full alignment on value, risk, readiness to sign.          Champion, Economic Buyer, Ratifier
  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-

A note on source alignment: the CRM Buying Group program includes Champion at Final Commitment alongside Economic Buyer and Ratifier. The IT Buying Group program lists only Economic Buyer and Ratifier at Final Commitment. This document retains the CRM model (Champion present at Final Commitment) as the more inclusive framework, since Champions typically remain engaged through deal closure to maintain internal consensus even if they are not the primary actors at this stage. Two patterns are significant for signal interpretation:

1.  The Champion appears at every convergence point, reinforcing why Champion behavioral signals emphasize breadth across the entire buying journey.

2.  The convergence points reveal where role ambiguity is highest: at Problem Validation and Business Value Alignment, Champion, Economic Buyer, and Influencer are all active on similar content (problem framing, outcomes, ROI).

At the final two convergence points (Risk/Compliance Validation and Final Commitment), the Champion, Economic Buyer, and Ratifier converge on compliance and procurement content. These convergence points are the primary zones where behavioral disambiguation is needed, and where the solution-category-specific firmographic rules and the JTBD-derived content signals are most valuable for resolving which role a visitor occupies.

## Additional Roles (Future Phases)

ServiceNow defines nine total buying group roles. Beyond the five MVP roles defined above, four additional roles are planned for future phases: Executive Sponsor (senior leader providing strategic support and air cover), Project Owner (owns implementation and delivery), Security Leader (validates security and compliance requirements), and Technical Validator (evaluates technical fit and integration capabilities). Behavioral hypotheses and signal profiles for these roles will be developed as they enter scope. The Technical Validator role is particularly noteworthy because its behavioral profile will likely overlap significantly with the Ratifier's; the distinguishing factor will be whether the content focus is on security and compliance (Ratifier) versus integration architecture and technical feasibility (Technical Validator).[^12]

# Section 5. Signal-To-Role Mapping

The heart of the document and the direct answer to the non-negotiable question. For each role, this section maps which signals indicate that role, the weight assigned to each signal, and the rationale for that weight.

Structure: Role-by-role, not signal-by-signal.

Each role gets its own subsection with a complete signal profile:

Primary indicators with weights and rationale

Secondary indicators with weights and rationale

Counter-indicators with negative weights and rationale

Example composite scenario showing how signals combine for a realistic visitor

Why role-by-role instead of a cross-reference matrix: The primary consumer question is "how do I identify a Champion?" not "what does a pricing page view mean across all roles?" Role-by-role is more actionable for the content strategist building the Champion experience, the analyst measuring Champion identification accuracy, or the engineer implementing the Champion classification logic. A summary cross-reference matrix can be included as an appendix for those who need the signal-centric view.

Signal interaction rules:

How co-occurring signals combine (additive by default)

Whether any signal combinations are multiplicative (e.g., form fill declaring "CIO" + pricing page view = stronger Economic Buyer signal than the sum of parts)

Minimum signal thresholds before a role classification is attempted

**Rationale:** This is where the non-negotiable question gets answered. The restructuring from matrix to role-by-role profiles is the biggest departure from v0.9. The addition of rationale for each weight and signal interaction rules are the pieces that make the document useful for ongoing tuning, not just initial implementation.

This section maps specific signals to each buying group role. It is organized role-by-role rather than signal-by-signal because the primary consumer question is "how do I identify a Champion?" rather than "what does a pricing page view mean?" A signal-by-signal cross-reference matrix is provided in Appendix A for those who need the transposed view.

**Each role profile includes behavioral signal weights on a scale of 0-25 points**, where the weight represents the signal's strength as an indicator for that role. Weights are additive across signals within a session and across sessions within the recency windows defined in Section 8. A visitor's role is determined by the highest cumulative score after applying recency decay. Weights are grounded in the JTBD framework from Section 4 content that directly supports a role's job at a given stage receives a higher weight for that role than content that is tangentially related. All weights are **initial estimates**; per Principle 6, they are testable hypotheses designed to be validated and recalibrated with real traffic data.

Remember that behavioral signal weights are the third classification path, applied when firmographic rules (Section 4) and zero-party data are unavailable. When CRM or form data has identified a visitor's role, behavioral signals serve as confirmation and enrichment, not the primary classification method. Remember also that role classification is per-solution-category: the weights below apply relative to the solution area the visitor is engaging with.

## 5.1 Champion Signal Profile

**Core behavioral signature:** Breadth across content types and solution areas, proof-point accumulation, high return frequency. The Champion's job is to build the internal case and recruit allies, which requires ammunition for multiple audiences.

**Primary Signals for Champion**

  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Signal**                                  **Weight**   **Rationale**
  –––––––––––––––––––––- –––––– –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Customer success story view/download**    +20          Directly supports the Champion's Acquisition JTBD of collecting proof and peer references, and the Progression JTBD of orchestrating consensus. Case studies are shareable artifacts Champions use to convince peers.

  **Competitive comparison page view**        +18          Champions need to preempt "why not competitor X?" objections from other stakeholders. This content is almost exclusively consumed by someone building an internal case.

  **Demo request submission**                 +20          A demo request during Acquisition signals the Champion is building conviction and moving toward socializing the solution internally.

  **3+ solution areas explored in 90 days**   +15          Breadth is the Champion's defining behavioral characteristic. Exploring multiple solution areas indicates cross-functional case-building, not single-domain evaluation.
  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

### Secondary Signals for Champion

  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Signal**                                               **Weight**   **Rationale**
  –––––––––––––––––––––––––––– –––––– ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **High return visit frequency, 3+ sessions per month**   +8           Champions build cases over weeks, not in a single session.

  **Webinar registration or attendance**                   +8           Supports the Acquisition JTBD of socializing a narrative and collecting proof.

  **Product tour completion**                              +8           A demo request during Acquisition signals the Champion is building conviction and moving toward socializing the solution internally.

  **Multiple asset downloads across content types**        +10          Accumulating diverse proof points (briefs, case studies, datasheets) signals internal distribution, a core Champion behavior.

  **ePDF download from viewer**                            +8           Downloading assets to their machine suggests content accumulation for internal distribution, a core Champion behavior of arming stakeholders with proof points.
  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-

### Counter-Indicators for Champion

  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Signal**                                                                   **Weight**   **Rationale**
  –––––––––––––––––––––––––––––––––––––– –––––– –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Exclusive focus on technical documentation without proof-point content**   -10          Suggests a validation or technical evaluation role (Ratifier or future Technical Validator), not an internal advocacy role.

  **Exclusive focus on pricing and ROI content without breadth**               -8           Narrow financial focus without cross-functional content exploration suggests Economic Buyer, not Champion.

  **Single-session engagement without return visits**                          -5           Champions build cases over weeks with repeated visits. A single session, however strong, is inconsistent with the sustained advocacy pattern.

  **Exclusive focus on security and compliance content**                       -8           Concentrated compliance content without breadth suggests Ratifier. A Champion may view security content but will also engage with case studies, competitive content, and multiple solution areas.
  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-

**Example scenario:** A visitor from a TAL account views a CRM case study (+20), then a competitive comparison page (+18), explores IT solution pages in the same session (+15 for breadth), and returns the following week to request a demo (+20) and download an executive brief (+10). Cumulative Champion score: 83. With no competing role score above 30, this visitor is classified as Champion with HIGH confidence.

## 5.2 Economic Buyer Signal Profile

**Core behavioral signature:** Narrow, purposeful engagement with financial justification content. Short sessions, low page depth, summary-oriented. The Economic Buyer's job is to evaluate the investment, not the product.

**Primary Signals for Economic Buyer**

  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Signal**                                **Weight**   **Rationale**
  ––––––––––––––––––––- –––––– –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **ROI calculator usage**                  +22          Directly supports the Progression JTBD of validating ROI and TCO scenarios. ROI calculators are the single strongest Economic Buyer signal because they require inputting business-specific data, indicating active financial evaluation.

  **Pricing page view**                     +15          Supports both Acquisition (shortlisting viable approaches) and Progression (validating investment size).

  **Executive brief download**              +12          Summary-format content designed for senior leaders making investment decisions.

  **Business value and outcomes content**   +12          Supports the Acquisition JTBD of translating pains into target outcomes and the messaging framework of making the cost of legacy drag visible.
  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

**Secondary Signals for Economic Buyer**

  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Signal**                                      **Weight**   **Rationale**
  –––––––––––––––––––––––- –––––– –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Low page depth per session, under 5 pages**   +5           Economic Buyers are focused, not exploratory: low page depth combined with financial content signals a senior evaluator, not a disengaged visitor.

  **Short session duration, under 5 minutes**     +3           Reinforces the pattern of purposeful, time-constrained visits.

  **Adoption and rollout planning content**       +8           Supports the Progression JTBD of understanding rollout and adoption plans before committing budget.

  **ePDF print**                                  +5           Printing an executive brief or ROI summary suggests preparation for an offline review or executive briefing, consistent with Economic Buyer behavior.
  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

**Counter-Indicators for Economic Buyer**

  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Signal**                                                    **Weight**   **Rationale**
  ––––––––––––––––––––––––––––––- –––––– ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Technical documentation engagement exceeding 10 minutes**   -10          Extended technical deep-dives suggest evaluation has not been delegated, inconsistent with Economic Buyer behavior.

  **Community or forum engagement**                             -12          Too hands-on and operational for a budget authority role. Community engagement is characteristic of Users, not decision-makers.

  **How-to or training content views**                          -10          Operational content indicates a practitioner evaluating usability, not a senior leader evaluating investment.

  **High session frequency with broad content exploration**     -8           Suggests Champion rather than Economic Buyer. Economic Buyers visit infrequently with narrow focus; broad exploration indicates case-building.
  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-

*Note: behavioral signals alone produce MEDIUM confidence for Economic Buyer at best. This role is most reliably identified through professional profile data (VP+ title in budget-authority function) or zero-party form declaration. When behavioral signals suggest Economic Buyer but professional profile data is unavailable, the confidence ceiling should be MEDIUM.*

**Example scenario:** A visitor from a TAL account views the pricing page (+15), uses the ROI calculator (+22), and downloads an executive brief (+12) in a single 4-minute session (+3 for short duration, +5 for low page depth). Cumulative Economic Buyer score: 57. No other role scores above 15. Classification: Economic Buyer at MEDIUM confidence (behavioral only, no firmographic corroboration). If the same visitor had previously submitted a form declaring a VP title, classification upgrades to HIGH confidence.

## 5.3 Influencer Signal Profile

**Core behavioral signature:** Depth within a single solution area, use case evaluation, requirements-oriented content. The Influencer's job is to assess fit for their team and shape the requirements the solution must meet.

**Primary Signals for Influencer**

  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Signal**                                                        **Weight**   **Rationale**
  ––––––––––––––––––––––––––––––––- –––––– ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Use case page exploration**                                     +15          Directly supports both the Acquisition JTBD of shaping requirements and the Progression JTBD of validating "how it works for us" use cases.

  **Product tour engagement with step progression**                 +12          Influencers stress-test how work will flow for their team, engaging with product tours at a functional level rather than just starting them.

  **Webinar registration or attendance**                            +15          Supports the Acquisition JTBD of shaping requirements and eliminating risk early, and the Progression JTBD of running or interpreting proof of concept.

  **Industry-specific content within a single solution category**   +12          Influencers evaluate fit for their specific domain, not across the organization.
  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

**Secondary Signals for Influencer**

  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Signal**                                                     **Weight**   **Rationale**
  ––––––––––––––––––––––––––––––– –––––– ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Best practices and implementation guide views**              +8           Influencers evaluate operational feasibility.

  **Content consumption concentrated in one solution area**      +5           Reinforces the single-domain focus hypothesis.

  **Moderate return visit frequency, 1–2 sessions per month**   +5           Influencers check in periodically as the evaluation progresses but don't exhibit the Champion's high-frequency pattern.

  **Moderate session duration, 5–15 minutes**                   +3           Moderate depth per session, between the Economic Buyer's brevity and the User's task-focused deep-dives.
  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-

**Counter-Indicators for Influencer**

  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Signal**                                           **Weight**   **Rationale**
  –––––––––––––––––––––––––– –––––– ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Pricing or ROI content focus**                     -8           Financial justification content suggests Economic Buyer. Influencers shape requirements, they don't evaluate investment.

  **Competitive comparison and case study hoarding**   -8           Accumulating shareable proof points suggests Champion case-building, not domain-specific evaluation.

  **Exclusive how-to and training content**            -5           Task-oriented operational content suggests User, not Influencer. Influencers evaluate at a higher level than individual workflows.

  **Security and compliance content focus**            -8           Concentrated validation content suggests Ratifier. Influencers may touch compliance topics but don't focus on them.

  **Three or more solution areas explored**            -5           Cross-functional breadth suggests Champion. Influencers focus on their domain.
  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

*Note: Influencer is the most behaviorally ambiguous role. The signal profile sits between Champion (breadth) and User (task-specificity). When behavioral signals are ambiguous and no firmographic or zero-party data is available, the system should fall back to solution-interest content per Principle 4 rather than defaulting to Influencer as a catch-all classification.*

**Example scenario:** A visitor from a TAL account views three CRM use case pages (+15), engages with a product tour through 6 of 8 steps (+12), and registers for a CRM webinar (+15) across two sessions over three weeks (+5 for moderate frequency, +5 for single-solution focus). Cumulative Influencer score: 52. Champion score is 20 (product tour and webinar overlap), but without breadth or case study signals, Influencer is the stronger classification. Classification: Influencer at MEDIUM confidence.

## 5.4 User Signal Profile

**Core behavioral signature:** Task-oriented, practical content consumption. Feature-specific exploration, how-to content, community engagement. The User's job is to determine whether the solution works for their daily workflows.

**Primary Signals for User**

  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Signal**                                 **Weight**   **Rationale**
  ––––––––––––––––––––– –––––– –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **How-to and training content views**      +18          Directly supports the Acquisition JTBD of surfacing frontline friction and must-have workflows, and the Progression JTBD of recommending adoption and training milestones.

  **Community and forum engagement**         +15          Users are the most likely role to seek peer validation and practical tips. This is the strongest User differentiator: no other role exhibits meaningful community engagement.

  **FAQ and support documentation visits**   +12          Users evaluate a solution by looking at its support infrastructure, not its business case.

  **Task-specific site search terms**        +10          Search queries like "incident routing," "SLA configuration," or "agent workspace" indicate someone evaluating specific operational capabilities.
  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-

**Secondary Signals for User**

  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Signal**                                                         **Weight**   **Rationale**
  ––––––––––––––––––––––––––––––––– –––––– ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Feature-focused product tour engagement**                        +8           Supports the Progression JTBD of validating use-based demos. Users engage with specific features rather than the full product overview.

  **Content consumption concentrated in a single narrow use case**   +5           Users focus on their specific workflow domain, not the broader solution.

  **Quick exits from non-operational content**                       +3           Users leave executive briefs and business value content quickly because it doesn't address their concerns.

  **ePDF internal search (how-to / training content)**               +8           Searching within how-to guides or training documents indicates task-oriented evaluation of specific capabilities, a core User behavior.

  **ePDF print (how-to / training content)**                         +5           Printing operational documentation suggests preparing reference material for daily workflows, consistent with the User role.
  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-

**Counter-Indicators for User**

  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Signal**                                           **Weight**   **Rationale**
  –––––––––––––––––––––––––– –––––– –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Pricing or ROI content engagement**                -12          Financial content suggests a decision-making role, not an operational one. Users evaluate usability, not investment.

  **Case study or competitive comparison downloads**   -10          Proof-point accumulation suggests Champion. Users don't need to build an internal case.

  **Exploration of multiple solution areas**           -8           Users focus on one domain. Cross-functional exploration suggests Champion breadth.

  **Executive brief downloads**                        -10          Wrong audience level. Executive-format content is designed for senior decision-makers, not operational evaluators.
  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

*Note: User behavioral signals overlap with existing customer support patterns. The support-only browsing negative signal (Section 3.7) must be evaluated before User classification is attempted: a visitor with 3+ sessions focused exclusively on support content should be flagged as a potential existing customer, not classified as a User in a new buying group.*

**Example scenario:** A visitor from a TAL account searches for "field service dispatch scheduling" (+10), views two how-to articles on dispatch workflows (+18), visits the community forum and reads three threads on field service configuration (+15), and views the FAQ page for mobile capabilities (+12). Cumulative User score: 55. No other role scores above 10. Classification: User at MEDIUM confidence (no firmographic corroboration). If the visitor had submitted a form declaring "Field Service Technician" as their title, classification upgrades to HIGH confidence.

## 5.5 Ratifier Signal Profile

**Core behavioral signature:** Narrow, deep engagement with security, compliance, and governance content. Late-stage timing. Infrequent but thorough visits. The Ratifier's job is to clear hurdles and validate that the solution meets organizational requirements.

**Primary Signals for Ratifier**

  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Signal**                                                    **Weight**   **Rationale**
  ––––––––––––––––––––––––––––––- –––––– –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Security whitepaper download**                              +20          Directly supports the Acquisition JTBD of identifying risk flags and understanding governance, privacy, and security requirements.

  **Compliance and governance content views**                   +18          Supports both the Acquisition JTBD of establishing boundaries for data and AI use, and the Progression JTBD of ensuring standards alignment.

  **Technical documentation engagement exceeding 10 minutes**   +12          Ratifiers are thorough: extended time on technical and architecture documentation indicates validation-oriented evaluation, not casual browsing.

  **Data privacy, regulatory, and audit readiness content**     +15          Supports the Progression JTBD of finalizing terms, SLAs, and liability.
  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-

**Secondary Signals for Ratifier**

  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Signal**                                                                **Weight**   **Rationale**
  ––––––––––––––––––––––––––––––––––––- –––––– ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Late-stage engagement timing**                                          +8           Ratifier activity often appears after the account has reached Prioritized or Qualified stage, consistent with the convergence points showing Ratifiers entering at Risk/Compliance Validation and Final Commitment.

  **Narrow content focus, security and compliance only**                    +5           Security and compliance content without exploration of other content types reinforces the validation-only behavioral pattern.

  **Form fill with legal, compliance, procurement, or security function**   +15          Zero-party confirmation of a validation-oriented function. Strongest non-CRM professional profile signal for Ratifier.

  **ePDF internal search**                                                  +10          Searching within a security whitepaper or compliance document indicates thorough, validation-oriented review. This is the strongest ePDF signal for Ratifier, as it suggests active requirements-checking rather than casual browsing.

  **ePDF download from viewer**                                             +5           Downloading compliance or security documentation suggests archiving for internal review or audit trail, consistent with the Ratifier validation workflow.
  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-

**Counter-Indicators for Ratifier**

  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
  **Signal**                                            **Weight**   **Rationale**
  ––––––––––––––––––––––––––- –––––– –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Demo request submission**                           -12          Ratifiers validate, they don't evaluate features. A demo request indicates product evaluation, not compliance review.

  **Case study or competitive comparison engagement**   -10          Proof-point accumulation suggests Champion. Ratifiers validate against requirements, they don't build business cases.

  **Pricing or ROI content**                            -8           Financial justification content suggests Economic Buyer. Ratifiers validate compliance, not investment.

  **Broad solution area exploration**                   -10          Ratifiers focus on their validation domain. Cross-functional browsing suggests Champion.

  **How-to or training content**                        -8           Operational content suggests User. Ratifiers evaluate whether the solution meets requirements, not how to use it.
  –––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

*Note: a visitor who engages with both security content and broad product content (case studies, competitive comparisons, multiple solution areas) is more likely a security-conscious Champion than a Ratifier. The key differentiator is breadth: Ratifier engagement is concentrated almost exclusively on validation topics.*

**Example scenario:** A visitor from a TAL account at the Prioritized stage (+8 for late-stage timing) downloads a security whitepaper (+20), spends 14 minutes on the technical architecture documentation (+12), and views the data privacy and compliance page (+15) in a single focused session (+5 for narrow content focus). Cumulative Ratifier score: 60. Champion score is 10 (security content overlap only). Classification: Ratifier at MEDIUM confidence. If the visitor's account reached Prioritized stage two weeks prior and the visitor submitted a form listing "Head of Data Privacy" as their title, classification upgrades to HIGH confidence.

## 5.6 Signal Interaction Rules

The following rules govern how signals combine when multiple signals are present for the same visitor.

**Default combination: additive.** Signal weights within a role profile are summed. A visitor who triggers three Champion signals at +20, +18, and +15 receives a cumulative Champion score of 53.

**Firmographic confirmation bonus.** When firmographic data (CRM role assignment or form-declared title/function) aligns with the highest behavioral score, apply a +30 confirmation bonus. This reflects the multiplicative increase in confidence when two independent classification paths agree. A behavioral Champion score of 50 with a CRM-confirmed Champion assignment becomes 80, crossing the HIGH confidence threshold.

**Firmographic contradiction flag.** When firmographic data assigns a role that contradicts the highest behavioral score (e.g., CRM says Economic Buyer but behavior strongly suggests Champion), the CRM role is maintained per the data source hierarchy (Section 9), but the contradiction is flagged for review. Persistent contradictions across multiple sessions may indicate a misclassification in the CRM that should be surfaced to the CRM/Sales Ops team.

**Minimum signal threshold.** A minimum cumulative score of 25 points is required before any role classification is attempted. Below this threshold, the visitor is classified as UNKNOWN and receives solution-interest or account-level content. Additionally, the top role score must exceed the second-highest role score by at least 10 points. If the gap is smaller, the classification is ambiguous and the system should fall back to the broader personalization level per Principle 4.

**Session engagement minimum.** A session must exceed 60 seconds or 2+ page views before any signals from that session are counted toward role classification. Single page views under 30 seconds are classified as insufficient engagement (Section 3.7).

**Cross-solution-category scoring.** Role scores are calculated independently for each solution category the visitor engages with. A visitor may score as Champion for CRM and Influencer for IT simultaneously. Personalization is delivered based on the role classification for the solution category the visitor is currently browsing. When a visitor moves between solution areas within a session, the role classification and content experience update accordingly.

# Section 6. Identification Model

The decision tree as a system specification. When a visitor arrives, what sequence of checks determines their classification at each pipeline layer?

**6.1 Account Identification Logic**

IP/domain match → TAL lookup → account attributes populated

Authentication/login path → CRM contact match → full profile

Third-party enrichment fallback when IP/domain doesn't resolve

Non-TAL handling: brand awareness content, no BG signals captured

**6.2 Buying Group Stage Logic**

For identified TAL accounts: pull BG stage from D&A model

Stage determines campaign cohort alignment and content tone

Stage transitions and what triggers them (from the centralized model)

**6.3 Role Classification Logic**

Step 1: Check for CRM role assignment (via D&A model)

Step 2: Check for zero-party self-identification (form data)

Step 3: Apply behavioral signal weights (Section 5) and calculate role scores

Step 4: Evaluate confidence (Section 7) and determine personalization response

Edge case handling at each step

**6.4 The Fallback Cascade**

HIGH confidence role classification → role-specific experience

MEDIUM confidence role classification → role-influenced content with safe fallback

LOW confidence / account identified only → solution-interest or account-level personalization

Unknown / non-TAL → default brand experience

**Rationale:** The decision tree from v0.9 was sound. The main refinements are: incorporating account-level and BG-stage identification as explicit steps (not just "Step 1: is this a TAL account?"), making the fallback cascade an explicit design decision at each confidence level, and making the logic precise enough that an engineer could implement conditional logic directly from the doc.

This section specifies the decision logic that executes when a visitor arrives at servicenow.com. It follows the three-layer pipeline defined in Section 2 and incorporates the classification paths and signal weights from Sections 4 and 5. The logic is presented as a sequential specification precise enough that an engineer could implement the conditional logic directly from this document.

## 6.1 Account Identification Logic

Step 1: Resolve visitor to account. Attempt IP/domain match via Demandbase. If no match, check for authenticated login or CRM contact cookie. If still unresolved, visitor is unidentified; serve default brand experience and capture no BG signals. Step 2: Check TAL membership. If the resolved account is on the 48K TAL, proceed to Layer 2. If not on the TAL, serve brand awareness content. No buying group signals are captured and no role classification is attempted (Principle 1). Step 3: Populate account attributes. For identified TAL accounts, load available account-level data: industry vertical, company size, region, existing customer status, product footprint, and solution fit scores. These attributes are available for Layer 1 personalization immediately, independent of Layer 2 and Layer 3 outcomes.

## 6.2 Buying Group Stage Logic

Step 4: Determine BG stage for each solution category. For the identified TAL account, retrieve the buying group stage from the D&A model for each of the four solution categories. Stage data flows via CRM intermediary on a 24–48 hour batch cycle via CRM, or near real-time via Kafka (live March 15). If stage data is unavailable for a solution category, default to Targeted. Step 5: Determine campaign cohort alignment. Map BG stage to campaign cohort: Targeted → Education, Engaged → Acquisition, Prioritized → Progression, Qualified → active deal support. Cohort alignment informs content tone and messaging framework. Step 6: Apply Layer 2 personalization. Deliver stage-appropriate content based on the BG stage for the solution category the visitor is currently browsing. If the visitor is exploring multiple solution categories, apply the stage for each independently.

## 6.3 Role Classification Logic

Step 7: Check for CRM role assignment. Query whether the D&A model has assigned a buying group role for this contact in the relevant solution category. If yes, use the CRM-assigned role as the authoritative classification (HIGH confidence). Proceed to Step 10 to apply behavioral confirmation. If no CRM assignment exists (or Kafka data is not yet available), proceed to Step 8. Step 8: Check for zero-party self-identification. Has this visitor submitted a form that captured job title, job level, and/or department/function? If yes, evaluate the firmographic classification rules in Section 4 for the relevant solution category. If the title × function × solution category mapping produces a clear role, classify accordingly (HIGH confidence if title + behavioral confirmation; MEDIUM-HIGH if title alone). Proceed to Step 10. If no form data exists, proceed to Step 9. Step 9: Apply behavioral signal inference. Calculate role scores using the signal weights in Section 5 for each solution category the visitor has engaged with. Apply recency decay (Section 8). Evaluate against minimum signal thresholds (Section 5.6): cumulative score must exceed 25, and the top role must lead by at least 10 points. If thresholds are met, classify by highest cumulative score (MEDIUM confidence maximum for behavioral-only classification). If thresholds are not met, classify as UNKNOWN. Step 10: Evaluate confidence level and determine personalization response using the confidence model in Section 7.

## 6.4 The Fallback Cascade

When the identification pipeline cannot classify a visitor at a given layer, the system falls back to the next broader personalization level. This cascade is the operational expression of Principle 4 (Graceful Degradation). Each level in the cascade represents an intentional design decision, not a failure state.

**Level 1: Role-specific experience.** Triggered when role classification confidence is HIGH. Content, CTAs, and framing are tailored to the specific role for the relevant solution category. **Level 2: Role-influenced experience.** Triggered when role classification confidence is MEDIUM. Content leans toward the classified role but includes safe fallback elements that work across roles. No highly role-specific CTAs. **Level 3: Solution-interest experience.** Triggered when role classification confidence is LOW or UNKNOWN but the visitor's solution area of interest is identified. Content is organized by solution category without role-specific framing. **Level 4: Account-level experience.** Triggered when the visitor is from a TAL account but no solution interest or role classification exists. Content is personalized by industry vertical, company size, or account attributes only. **Level 5: Default brand experience.** Triggered for non-TAL visitors or unidentified visitors. The standard servicenow.com experience with no personalization applied.

# Section 7. Conflict Resolution & Edge Cases

How individual signal scores aggregate into a confidence classification, what the threshold boundaries are, and what happens at each level. This section explicitly separates role classification confidence from engagement scoring.

**7.1 Confidence Levels**

HIGH (80-100%): CRM role confirmation OR zero-party + behavioral match → full role-specific experience

MEDIUM (50-79%): Strong behavioral pattern (3+ signals) without CRM/form confirmation → role-influenced content with fallback

LOW (20-49%): Limited behavioral signals, ambiguous patterns → solution-interest or account-level content

UNKNOWN (\<20%): Insufficient data → default experience

**7.2 Confidence vs. Engagement: Why the Distinction Matters**

Confidence = how certain are we about who this person is (role classification accuracy)

Engagement = how active is this person (behavioral intensity, scored 0-100 by D&A model)

A visitor can be high-engagement but low-confidence (active but role-ambiguous)

A visitor can be high-confidence but low-engagement (CRM-confirmed role but infrequent visits)

Personalization decisions use both dimensions but for different purposes

**7.3 Confidence Score Calculation**

How individual signal weights aggregate

Thresholds for advancing from one confidence level to the next

Minimum signal diversity requirements (e.g., a single very strong signal is not sufficient for HIGH confidence without corroboration)

**Rationale:** The confidence levels from v0.9 were well-structured. The key additions are the explicit confidence-vs-engagement distinction (which prevents the most common stakeholder confusion: "why isn't this High-engagement visitor getting personalized content?") and the confidence score calculation mechanics, which were implied but not specified in previous versions.

The confidence model determines how certain the system is about a visitor's role classification and what personalization action follows at each level. Confidence is distinct from engagement, a distinction critical enough to warrant its own governing principle (Principle 5).

## 7.1 Confidence Levels

  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Level**     **Score Range**   **Trigger Conditions**                                                                                                                        **Personalization Action**
  ––––––- ––––––––- ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––- –––––––––––––––––––––––––––––––-
  **HIGH**      80–100 pts       CRM role assignment exists; OR zero-party form data + behavioral confirmation (+30 bonus)                                                     Full role-specific experience (Fallback Level 1)

  **MEDIUM**    50–79 pts        Zero-party form classification without behavioral confirmation; OR strong behavioral pattern (3+ signals, score 50+, top role leads by 10+)   Role-influenced content with safe fallback (Fallback Level 2)

  **LOW**       25–49 pts        Limited behavioral signals (1–2 signals); OR ambiguous pattern (top role does not lead by 10+)                                               Solution-interest content only (Fallback Level 3)

  **UNKNOWN**   \<25 pts          Insufficient data (single page view, \<30 sec, no history); OR all signals below minimum thresholds                                           Account-level (Level 4) or default brand experience (Level 5)
  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-

## 7.2 Confidence vs. Engagement: Why the Distinction Matters

Confidence and engagement measure fundamentally different things. Confidence answers "how certain are we about who this person is?" (role classification accuracy). Engagement answers "how active is this person?" (behavioral intensity, scored 0–100 by the D&A model over the last 180 days). These dimensions are independent. A visitor can be high-engagement but low-confidence: they visit frequently and consume a lot of content, but their behavioral pattern is ambiguous across roles (perhaps they exhibit both Champion and Influencer signals without a clear differentiation). A visitor can be high-confidence but low-engagement: their CRM role assignment is authoritative, but they rarely visit the website.[^13]

Personalization decisions use both dimensions but for different purposes. Confidence determines what content to serve (role-specific vs. solution-interest vs. generic). Engagement determines urgency and prioritization: how prominently to surface conversion opportunities, how aggressively to encourage next steps, and how to prioritize this account in campaign and sales activation. When a stakeholder asks, "why isn't this High-engagement visitor getting personalized role content?" the answer is that their engagement is high, but their role confidence is low. The system correctly serves solution-interest content until it can classify their role with sufficient certainty.

## 7.3 Confidence Score Calculation

The confidence score for a visitor's role classification is the cumulative signal score for the highest-scoring role, after applying recency decay (Section 8), the firmographic confirmation bonus when applicable (Section 5.6), and the minimum threshold requirements. The score maps directly to the confidence levels above. Confidence scores are calculated per-solution-category, consistent with the cross-solution-category scoring rule in Section 5.6.

A minimum signal diversity requirement applies: a single very strong signal is not sufficient for HIGH confidence without corroboration from at least one additional signal source. For example, a visitor who uses the ROI calculator (+22) but has no other signals should not be classified as Economic Buyer at HIGH confidence from that single interaction alone, even if the cumulative score exceeds 80 after a firmographic bonus. At least two distinct signal types (e.g., behavioral + zero-party, or two different behavioral signals) should be present before HIGH confidence is assigned. This requirement prevents over-classification from isolated actions that may not represent sustained role behavior.

# Section 8. Signal Recency & Decay

Time windows, decay multipliers, and their alignment with the centralized buying group model.

**8.1 Time Windows**

Current session: 1.5x multiplier (strongest indicator of current intent)

Last 90 days: 1.0x baseline (aligns with Prioritized stage: 2+ members with engagement)

Last 180 days: 0.7x (aligns with BG Member engagement scoring window)

180 days: 0x excluded (historical context only, not counted)

**8.2 Session vs. Historical Interaction**

How a single strong session interacts with a thin historical profile

How a rich historical profile interacts with a contradictory current session

Returning visitor recalculation logic

**Rationale:** This was Section 10 in v0.9, buried near the end. Recency logic materially affects every signal weight calculated in Section 5, so it belongs earlier in the document. The alignment with the D&A model's 90-day and 180-day windows is intentional and should be made explicit.

Signal recency determines how much weight a signal retains over time. More recent signals are stronger indicators of current intent; older signals decay in value. The time windows below are intentionally aligned with the centralized D&A model's engagement scoring windows to ensure consistency between web-layer role classification and the D&A model's buying group stage and engagement calculations.

## 8.1 Time Windows and Decay Multipliers

  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Time Window**       **Multiplier**    **D&A Alignment**                                       **Application**
  ––––––––––- ––––––––- –––––––––––––––––––––––––––- ––––––––––––––––––––––––––––––––––––––-
  **Current session**   1.5x              N/A (session-level only)                                Strongest indicator of current intent. Real-time personalization decisions.

  **Last 90 days**      1.0x (baseline)   Prioritized stage: 2+ members engaged in last 90 days   Current and reliable indicators of role behavior.

  **91–180 days**      0.7x              BG Member engagement scoring window (180 days)          Still contributes but discounted. Role and intent may have evolved.

  **\>180 days**        0x (excluded)     D&A excludes activity beyond 180 days                   Historical context only. Does not contribute to role scores.
  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-

## 8.2 Session vs. Historical Interaction

Three scenarios require explicit handling when current-session signals interact with historical profile data.

**Strong current session, thin history.** A first-time or infrequent visitor produces a concentrated burst of role-indicative signals in a single session. The 1.5x session multiplier amplifies these signals, but the confidence ceiling remains MEDIUM because there is no historical pattern to corroborate. A single strong session is suggestive but not sufficient for HIGH confidence behavioral classification. The system should serve role-influenced content (Fallback Level 2) and accumulate additional sessions before upgrading confidence.

**Rich history, contradictory current session.** A visitor with a strong historical profile as one role exhibits signals for a different role in the current session. For example, a visitor historically classified as Influencer suddenly engages heavily with security and compliance content (Ratifier signals). The current session receives 1.5x weighting, which may be enough to shift the top role score temporarily. The system should respond to the current session's signals for real-time personalization (serve compliance content) but should not permanently reclassify the visitor based on a single contradictory session. If the new pattern persists across 2–3 sessions, the role classification updates. This handles legitimate role drift (the Influencer has been asked to take on compliance review) without overreacting to one-off browsing behavior.

**Returning visitor recalculation.** When a returning visitor starts a new session, the system recalculates all role scores by combining the current session (1.5x) with the full historical profile (1.0x for 0–90 days, 0.7x for 91–180 days). This means role classification can evolve over time as new sessions accumulate and older signals decay. The recalculation happens at session start and updates in real time as the visitor navigates during the session.

# Section 9. Negative Signals & Exclusions

What happens when the data is messy. This section starts with known scenarios and is designed to grow as a living registry of resolved ambiguities.

**9.1 Data Source Hierarchy**

CRM role assignment (highest authority)

Zero-party self-identification (form data)

Behavioral inference (lowest authority)

When and how a lower-authority source can flag a potential misclassification in a higher-authority source

**9.2 Known Conflict Scenarios**

Multi-role signals: visitor behavior indicates two roles with similar scores

Tie-breaking rules: when scores are within a defined threshold, fallback to broader personalization

Source contradiction: form data says one role, behavioral signals say another

Role drift: visitor's behavioral pattern shifts over time from one role to another

TAL account visitor exhibiting non-buyer behavior (job seeker, support user, competitor)

**9.3 Negative Signal Handling**

Exclusion hierarchy: does a negative signal override a positive CRM role assignment?

Exclusion scope: session-level vs. persistent exclusion

Career page, .edu, competitor domain, support-only patterns

\<2 BG members identified → defaults to Education cohort

Single page view \<30 seconds → no classification attempted

**Rationale:** v0.9 had conflict resolution rules embedded in the confidence scoring section. Giving this its own section signals that edge cases are first-class design considerations. The addition of exclusion scope (session vs. persistent) and the hierarchy question (can a negative signal override CRM?) are design decisions that get made ad hoc in implementation if not documented here.

This section defines the rules for resolving ambiguous, conflicting, or exceptional classification scenarios. It is designed as a living registry; as new edge cases are encountered in production, their resolutions should be documented here.

## 9.1 Data Source Hierarchy

When multiple classification paths produce different results, the following hierarchy determines which source prevails. First: CRM role assignment from the D&A model (highest authority). The D&A model classifies roles using title, function, and solution-category relevance across the full breadth of CRM, sales, and marketing data. When this classification exists, it is authoritative. Second: zero-party self-identification via form fill. The visitor has declared their own title, level, and function. This has high authority because it comes directly from the visitor, though it may be inaccurate (people sometimes select aspirational titles or use non-standard descriptions). Third: behavioral inference via signal weights (lowest authority). Behavioral patterns are probabilistic, not deterministic. A lower-authority source cannot override a higher-authority classification. However, when a lower-authority source persistently contradicts a higher-authority classification across 3+ sessions, the contradiction should be flagged for review by the CRM/Sales Ops team, as it may indicate a misclassification or role change in the source system.

## 9.2 Known Conflict Scenarios

**Multi-role signals.** A visitor's behavioral signals indicate two roles with similar cumulative scores. Resolution: if the gap between the top two role scores is less than 10 points, the classification is ambiguous. The system falls back to solution-interest content (Fallback Level 3) rather than guessing. If the gap is 10+ points, the higher-scoring role is assigned.

**Source contradiction.** Form data says one role (e.g., visitor declares "VP of Finance" suggesting Economic Buyer or Ratifier depending on solution), but behavioral signals strongly suggest another role (e.g., Champion-pattern browsing). Resolution: the form data prevails per the data source hierarchy. Behavioral signals are logged as enrichment context. If the contradiction persists across 3+ sessions, the discrepancy is flagged for review. The most common cause of this scenario is a visitor whose firmographic profile maps to one role but who is actually operating in a different capacity within this specific buying group.

**Cross-solution-category role conflict.** A visitor holds different roles for different solution categories (e.g., Economic Buyer for ITSM, Champion for CRM). Resolution: this is not a conflict; it is expected behavior per the solution-category-dependent classification principle (Section 4). Role scores are maintained independently per solution category. Personalization is delivered based on the role for the solution area the visitor is currently browsing.

**Role drift.** A visitor's behavioral pattern shifts over time from one role to another (e.g., early sessions looked like Influencer, recent sessions look like Champion). Resolution: the recency decay model (Section 8) handles this naturally. Older Influencer signals decay while newer Champion signals accumulate at full or amplified weight. If the new pattern is consistent across 2–3 sessions, the role classification updates. The system should not attempt to prevent role drift; it reflects genuine changes in how a person is engaging with the buying process.

**TAL account visitor exhibiting non-buyer behavior.** A visitor identified as belonging to a TAL account exhibits job seeker, support-only, or competitor-like behavior. Resolution: apply the negative signal rules in Section 9.3 below. Negative signals can suppress role classification even for TAL account visitors.

## 9.3 Negative Signal Handling

Negative signals (defined in Section 3.7) suppress or exclude visitors from role classification. Two design decisions govern their application.

**Exclusion scope.** Career page visit: session-level exclusion. The visitor is excluded from role classification for the current session but not permanently; a TAL account employee might browse careers in one session and evaluate solutions in the next. .edu email domain: persistent exclusion. Once captured via form, the visitor is excluded from all buying group classification. Competitor domain: persistent exclusion. Bot/crawler: persistent exclusion. Support-only browsing (3+ sessions): persistent suppression of Economic Buyer and Champion scores (−15 per Section 3.7) but not full exclusion; the visitor may still be classified as User if behavioral signals support it. Insufficient engagement (single page view \<30 seconds): session-level exclusion. No signals captured from this session.

**Exclusion hierarchy.** Negative signals cannot override a CRM role assignment. If the D&A model has classified a contact as Champion but the visitor's current session includes a career page visit, the CRM classification is maintained; the career page visit suppresses behavioral signal capture for the current session only. Negative signals can override zero-party and behavioral classifications. If a visitor submits a form with a .edu email address, the .edu exclusion takes precedence over any role classification that the form's title and function fields might suggest. The rationale is that CRM classifications reflect a validated organizational assessment, while negative signals address visitor-level disqualifiers that the CRM may not capture.

**Buying group formation threshold.** When fewer than 2 buying group members have been identified for an account in a given solution category, the account defaults to the Education cohort regardless of individual role classification. Individual visitors may still be classified at Layer 3, but the personalization response should reflect the account's early-stage status. This aligns with the D&A model's BG stage definitions: a buying group with fewer than 2 engaged members is in the Targeted stage.[^14]

# Section 10. Data Dependencies & Integration Status

A clean reference table showing the current state of every data source. No roadmap narrative: when infrastructure changes, update the status column.

**For each data source:**

Source system

Integration method

Latency profile

Current operational status (Active / In Progress / Planned)

Data owner

Dependencies or blockers

**Key integration milestones (reference only, not a project plan):**

CRM connector (current state)

Kafka integration (Snowflake → AEP direct)

Third-party enrichment provider status

Forms integration status

**Rationale:** This replaces the phase-based comparison from v0.9. The phase framing has a shelf life: once Kafka goes live, the entire section becomes historical. A status-based reference table stays current with column updates and doesn't require structural rewrites.

This section provides a reference table of every data source that feeds the identification pipeline. It is designed to be updated in place as integration status changes: when a data source goes live or a new dependency is identified, update the status column rather than rewriting the section.

  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-
  **Data Source**                          **Integration**                   **Latency**                     **Status**         **Owner**
  –––––––––––––––––––– ––––––––––––––––- –––––––––––––––- ––––––––– –––––––––––-
  **Adobe Analytics (behavioral)**         AEP Web SDK                       Real-time                       Active             Web Analytics

  **Marketo / AEM Forms (zero-party)**     Form connector → AEP              Near real-time                  Active             Forms Team (Sneha)

  **Demandbase (account enrichment)**      AEP partner connector             Real-time                       Active             ABM Team

  **Dynamics CRM, account data**           CRM connector → AEP               24–48hr batch                  Active             CRM / Sales Ops

  **Dynamics CRM, contact data**           Kafka (Snowflake → AEP)           Near RT (March 15)              In Progress        CRM / Sales Ops + D&A

  **D&A / Snowflake (BG stage, scores)**   CRM (current); Kafka (March 15)   CRM: 24–48hr; Kafka: Near RT   Active (acct/BG)   Data & Analytics

  **Event Platform / CRM**                 CRM connector → AEP               Post-event batch                Active             Events (Tamer)

  **Marketo / CRM (campaign history)**     CRM connector → AEP               24–48hr batch                  Active             Marketing Ops

  **Chat platform**                        Not yet integrated                N/A                             Planned            Web Experience
  ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––-

# Section 11. Governance & Evolution

How the document and the signal model stay accurate after launch.

**11.1 Ownership**

Who owns signal weight tuning

Who owns data source status updates

Who owns edge case resolution and documentation

**11.2 Review Cadence**

Post-launch review (after regional go-lives)

Quarterly signal performance review

Ad hoc review triggered by infrastructure changes (e.g., Kafka go-live)

**11.3 Signal Validation Methodology**

How we determine whether signal weights are actually predictive

What data we need to validate (classification accuracy vs. downstream conversion)

Threshold for triggering weight recalibration

**11.4 Change Management**

How new signals get proposed, validated, and added to the taxonomy

How weight changes are tested before production deployment

Version control and stakeholder notification

**Rationale:** Completely absent from all previous versions. Without governance, the document is a snapshot that degrades the moment it's published. With it, the document is a living system. The signal validation methodology is particularly important: you'll have real traffic data post-launch, and you need a framework for turning that data into signal model improvements.

This section defines how the signal definition model stays accurate after launch. Without governance, this document is a snapshot that degrades the moment it is published. With it, the document is a living system.

## 11.1 Ownership

Signal weight tuning and behavioral hypothesis updates: Richard Thomchick, Senior PM, Personalization & Buying Groups. Data source status updates: respective data owners as listed in Section 10, with Richard responsible for maintaining the consolidated reference table. Edge case resolution and documentation (Section 9): Richard, with input from the Testing & Optimization team for scenarios identified through A/B testing. Firmographic classification rule updates: Richard in collaboration with CRM / Sales Ops, as the D&A model's role classification coverage expands. JTBD and convergence point updates: Richard in collaboration with the Buying Groups program team, as new solution-category-specific JTBD are defined.

## 11.2 Review Cadence

Post-launch review: within two weeks of each regional go-live (AMS, EMEA, APAC). Focus: are the signal weights producing sensible classifications? Are any roles being systematically over- or under-identified? Are negative signals firing correctly? Kafka go-live review: triggered when the Kafka integration goes live (March 15). Focus: update all data source statuses in Section 10, validate that CRM role assignments are flowing to AEP correctly, confirm that the firmographic confirmation bonus is producing expected confidence upgrades. Quarterly signal performance review: recurring quarterly, starting Q2 2026. Focus: classification accuracy vs. downstream conversion, signal weight recalibration based on accumulated traffic data, new edge cases to document in Section 9. Ad hoc review: triggered by any significant infrastructure change, D&A model update, or form strategy change that affects signal availability or quality.

## 11.3 Signal Validation Methodology

Once sufficient traffic data has accumulated (target: 30 days post-regional go-live), signal weights should be validated against two criteria. First, classification accuracy: for visitors who are subsequently identified through CRM or form data, does the behavioral classification match? This is the most direct validation: compare what the behavioral model predicted against the "ground truth" of firmographic classification. Second, downstream conversion: do visitors classified as a specific role engage with role-targeted content at higher rates than visitors classified as other roles? If Champions are clicking on Economic Buyer content more than Champion content, the behavioral hypothesis may need revision. Signal weight recalibration should be triggered when classification accuracy drops below 60% for any role on a 30-day rolling basis, or when downstream conversion rates for role-targeted content show no meaningful differentiation between roles.

## 11.4 Change Management

New signals are proposed by documenting the signal in the Section 3 taxonomy format (source, integration, latency, status, owner), stating the hypothesis for which role(s) the signal indicates and why, and proposing initial weights with rationale. Proposed signals should be validated through a minimum two-week observation period before being added to production scoring. Weight changes follow the same process: state which weight is changing, document the evidence that triggered the change (classification accuracy data, conversion data, or qualitative feedback), and document the new weight with updated rationale. Weight changes should be tested through A/B testing or holdback groups where possible before full production deployment. All changes to this document are version-controlled through the changelog and communicated to stakeholders listed in the document control section: David Chen (Platform), Sneha (Forms), Raghav (Tagging), Andy, Anar, Tamer, Jeff, Katie (PM Leads), and Jessica (Testing & Optimization team).

# References

The following documents are cited in the footnotes throughout this document. They constitute the primary source material for buying group definitions, stage criteria, role classification logic, campaign cohort alignment, and program metrics. Hyperlinks to source material will be added as they become available.

1.  **Buying Groups GTM Transformation Walking Deck.** Strategic overview of the buying group GTM transformation, including TAL definition, solution category mappings, program success metrics, and the shift from lead-based to buying-group-based go-to-market. Cited in footnotes 1, 4, 5, 6, 15, 17.

2.  **Buying Group Audience Segments.** Detailed audience segmentation framework covering buying group stage criteria, campaign cohort definitions, CRM deal progression requirements, engagement scoring methodology, and AEP activation architecture. Cited in footnotes 6, 7, 8, 10, 11, 13, 14, 16.

3.  **Buying Groups FAQ.** Internal reference document defining buying group terminology, role definitions (nine total roles, five MVP), buying group composition guidelines, and the distinction between "role" (buying group member function) and "persona" (C-level executive archetype). Cited in footnotes 2, 3, 12.

4.  **Digital BG Tech & Campaign Weekly Sync Notes.** Internal meeting notes tracking implementation milestones for buying group infrastructure, including CRM go-live dates, campaign cohort activation, web personalization launch, and Kafka integration timeline. Cited in footnote 9.

5.  **IT Buying Group Program Working Deck.** IT program plan covering targeting strategy, IT buying group role-to-title mappings across three sub-solutions (AI + Data Orchestration, Autonomous Service Ops, Autonomous IT & Security), convergence points, Education and Acquisition stage JTBD by role, and content ecosystem by campaign stage. Source for IT-specific title mappings and Education-stage JTBD in Section 4.

6.  **CRM Buyer FY26 Narrative, Messaging, and Works Brief.** CRM program planning document covering messaging framework, CRM buying group role-to-title mappings for Service (CSM, FSM) and Sales (SOM) sub-solutions, JTBD by role and stage, convergence points, content ecosystem, and competitive landscape. Source for CRM-specific title mappings in Section 4 and JTBD/messaging alignment in Section 4.

# Appendix A. Signal Cross-Reference Matrix

The signal-by-signal view (transposing the role-by-role profiles from Section 5 into a matrix). Useful for signal-centric questions like "what does a pricing page view mean?" Provided as a reference complement, not the primary presentation.

The following matrix transposes the role-by-role signal profiles from Section 5 into a signal-centric view. For each signal, the matrix shows the weight assigned for each role. This is useful for answering questions like "what does a pricing page view mean across all roles?" The role-by-role profiles in Section 5 remain the primary reference; this matrix is a complement.

  –––––––––––––––––––––––––––––––––––––––––––––––––
  **Signal**                                **Champ**   **Econ**   **Infl**   **User**   **Ratif**
  ––––––––––––––––––––- –––––- ––––– ––––– ––––– –––––-
  **Case study / success story download**   +20         +3         +5         +2         +2

  **Competitive comparison page view**      +18         +5         +3         0          +2

  **Demo request submission**               +20         +8         +5         +3         0

  **3+ solution areas explored**            +15         +3         −5         −8         −10

  **ROI calculator usage**                  +8          +22        +3         0          +3

  **Pricing page view**                     +5          +15        +3         0          +5

  **Executive brief download**              +10         +12        +3         −10        +3

  **Use case page exploration**             +8          +3         +15        +8         +2

  **Product tour engagement**               +8          +3         +12        +8         +2

  **Webinar registration / attendance**     +8          +3         +15        +3         +3

  **How-to / training content**             +2          −10        +5         +18        +2

  **Community / forum engagement**          +5          −12        +5         +15        +2

  **Security whitepaper download**          +5          +3         +3         0          +20

  **Compliance / governance content**       +3          +5         +3         0          +18

  **Technical docs (10+ min)**              +3          −10        +8         +5         +12

  **FAQ / support documentation**           +2          0          +3         +12        +2
  –––––––––––––––––––––––––––––––––––––––––––––––––

# Appendix B. Confidence Scoring Examples

Worked examples showing how signal combinations produce confidence scores for realistic visitor scenarios. Carried forward from v0.9 and expanded to cover the three-layer pipeline.

The following examples illustrate how the three-layer pipeline, signal weights, and confidence model combine for realistic visitor scenarios.

**Scenario 1: High-confidence Champion (CRM + behavioral).** A visitor from Acme Corp (TAL account, Layer 1 identified) arrives via Demandbase IP match. Account BG stage for CRM is Prioritized (Layer 2). CRM has classified this contact as Champion for CRM solutions (Layer 3, Step 7: CRM role exists → HIGH confidence base). During the current session, the visitor downloads a CRM case study (+20 × 1.5x = +30) and views a competitive comparison (+18 × 1.5x = +27). Behavioral signals confirm the CRM assignment (+30 firmographic confirmation bonus). Final confidence: HIGH. Personalization: full role-specific Champion experience for CRM solutions.

**Scenario 2: Medium-confidence Economic Buyer (form + behavioral).** A visitor submits a demo request form declaring "VP of Customer Service" as their title and "Customer Service" as their department. Firmographic classification for CRM (Service) solutions: Economic Buyer (EVP/SVP/VP Customer Service matches the CRM buying group title mapping). During this session, the visitor views the pricing page (+15 × 1.5x = +22.5) and an executive brief (+12 × 1.5x = +18). Behavioral signals align with Economic Buyer. Total behavioral score: \~40.5, plus firmographic confirmation bonus (+30) = \~70.5. However, this is the first session with only two distinct behavioral signals. Signal diversity minimum for HIGH requires corroboration across signal types. Classification: Economic Buyer at MEDIUM-HIGH, serving role-influenced content with some role-specific elements. On a subsequent session with additional Economic Buyer signals, confidence upgrades to HIGH.

**Scenario 3: Low-confidence, ambiguous (behavioral only).** An anonymous visitor from a TAL account (IP matched, no CRM contact match, no form fill) views a CRM product tour (+12 for Influencer, +8 for Champion, +8 for User), downloads a case study (+20 for Champion, +5 for Influencer), and views one how-to article (+18 for User, +5 for Influencer). After one session: Champion score = 28, Influencer score = 22, User score = 26. The gap between Champion (top) and User (second) is only 2 points, below the 10-point minimum differential. Classification: ambiguous. The system falls back to solution-interest content for CRM (Fallback Level 3). If the visitor returns and the pattern clarifies (more case studies \[Champion\] or more how-to content \[User\]), the classification will resolve.

**Scenario 4: Negative signal suppression.** A visitor from a TAL account visits the careers page in their first session. Per Section 9.3, this triggers session-level exclusion: no role signals are captured for this session, and no classification is attempted. The visitor returns two days later and browses CRM solution content without visiting careers. The second session is processed normally through the identification pipeline. The career page visit does not permanently disqualify the visitor.

**Scenario 5: Cross-solution-category dual classification.** A VP of IT (form-identified) browses both ITSM and CRM content in the same session. For ITSM: firmographic classification maps VP of IT to Economic Buyer (budget authority over IT solutions). Behavioral signals during the ITSM portion of the session (pricing page view, ROI calculator) confirm. Classification: Economic Buyer for ITSM at HIGH confidence. For CRM: firmographic classification maps VP of IT to Influencer (adjacent function without CRM budget authority). Behavioral signals during the CRM portion (use case pages, product tour) are consistent with Influencer. Classification: Influencer for CRM at MEDIUM confidence. As the visitor navigates between ITSM and CRM content, the personalization experience updates to reflect the role classification for the solution area currently being browsed.

# Appendix C. Glossary

Key terms defined: buying group, buying group stage, role vs. persona, TAL, engagement score vs. confidence score, signal vs. signal weight, etc.

**Buying group:** A group of people involved in making a purchase decision together for a specific solution category. ServiceNow defines buying groups per-account per-solution-category.

**Buying group stage:** The current position of a buying group in its journey: Targeted (no engagement), Engaged (early interest), Prioritized (active momentum), or Qualified (active opportunity). Determined by the D&A model.

**Role:** A function within the buying group defined by the person's relationship to the purchase decision: Champion, Economic Buyer, Influencer, User, or Ratifier. Role is always relative to a solution category. "Role" refers to buying group members; "Persona" is reserved for C-level executive archetypes (CIO, CCO).

**TAL (Target Account List):** The 48,000 accounts jointly defined by Sales and Marketing as the focus of buying group personalization. Refreshed annually during planning with quarterly signal reviews.[^15]

**Signal:** An observable data point (behavioral, zero-party, firmographic, contextual, or negative) that provides evidence about a visitor's account, buying group stage, or role.

**Signal weight:** A numeric value (0–25 scale) representing how strongly a behavioral signal indicates a specific buying group role. Weights are testable hypotheses, not permanent values.

**Confidence score:** A cumulative score representing how certain the system is about a visitor's role classification. Mapped to four levels: HIGH (80–100), MEDIUM (50–79), LOW (25–49), UNKNOWN (\<25). Determines the personalization response via the fallback cascade.

**Engagement score:** A 0–100 score calculated by the D&A model measuring a buying group member's behavioral intensity across marketing and sales channels over the last 180 days. Distinct from confidence score (see Principle 5).[^16]

**D&A classification model:** The centralized model maintained by Data & Analytics that classifies buying group members into roles using job title, function, and solution-category relevance. The authoritative source for role assignment when available.

**Solution category:** One of ServiceNow's four solution categories: IT, CRM, Employee Experience, and Security & Risk. Employee Experience encompasses HR, Finance, and Supply Chain. Buying groups, role classifications, and signal weights are all evaluated per-solution-category.[^17]

**Fallback cascade:** The five-level degradation path that determines the personalization response when classification confidence is insufficient: role-specific → role-influenced → solution-interest → account-level → default brand experience.

**Convergence point:** A moment in the buying process where multiple roles must align for the deal to advance. Convergence points define where signal overlap between roles is expected and where behavioral disambiguation is most important.

**JTBD (Jobs to Be Done):** The specific tasks and objectives each buying group role is trying to accomplish at each stage of the buying process. JTBD are the foundation for behavioral signal interpretation: the content a visitor consumes to accomplish their job is the signal that identifies their role.

**Zero-party data:** Information a visitor explicitly and intentionally provides, such as job title, department, and solution interest submitted through a form. Distinguished from first-party data (observed behavioral data) and third-party data (enrichment from external providers).

# Changelog

**v0.1 (February 5, 2026):** Initial document structure. Preamble, scope, and section outline with editorial notes and \[CONTENT\] placeholders for all sections.

**v0.5 (February 6, 2026):** Added Section 1: seven governing principles. Added Section 2: three-layer identification pipeline. Added Section 3: complete signal taxonomy (six categories). Confirmed Demandbase as enrichment provider. Added Section 4: five MVP role definitions with three classification paths, solution-category-dependent firmographic rules with CRM title mappings, JTBD framework, convergence points, and Education stage gap callout. Added Section 5: signal-to-role mapping with JTBD-derived weights, example scenarios, and signal interaction rules. Added Section 6: identification logic (10-step pipeline specification, five-level fallback cascade). Added Section 7: confidence model (four levels, confidence-vs-engagement distinction, score calculation, signal diversity requirement). Added Section 8: signal recency and decay (4 time windows aligned with D&A model, session vs. historical interaction rules). Added Section 9: conflict resolution (data source hierarchy, five known conflict scenarios, negative signal handling with exclusion scope and hierarchy). Added Section 10: data dependencies and integration status (nine data sources with current status). Added Section 11: governance and evolution (ownership, review cadence, signal validation methodology, change management). Added Appendix A: signal cross-reference matrix. Added Appendix B: five confidence scoring example scenarios. Added Appendix C: glossary (14 terms).

**v0.6.1 (February 13, 2026):** Replaced all Phase 1/Phase 2 framing with specific capability language and dates. Kafka integration (Snowflake → AEP) for individual-level role identification now referenced as going live March 15 throughout. Updated Section 3.1 behavioral signals to reflect ePDF migration: replaced "PDF engagement time not tracked (download events only)" with available ePDF metrics (PDF loaded, download from viewer, PDF internal search, PDF print, plus page-level HTML metrics). Removed yellow highlights on previously flagged items (PDF tracking gap, Phase 2 CRM integration reference) as both have been resolved. Replaced all em-dashes with appropriate punctuation throughout the document per style guidelines. Updated Section 10 data dependencies table: CRM contact data integration path, latency, and status updated to reflect Kafka timeline; D&A/Snowflake integration path updated from Ph1/Ph2 framing to current/March 15 framing. Added References section between Section 11 and Appendix A, listing all source documents cited in footnotes (Buying Groups GTM Transformation Walking Deck, Buying Group Audience Segments, Buying Groups FAQ, Digital BG Tech & Campaign Weekly Sync Notes). Split Section 3.3 (Firmographic Signals) into two sections: Section 3.3 now covers account-level signals only (third-party enrichment, CRM account data, whitespace/solution fit); new Section 3.4 (Professional Profile Signals) covers individual-level attributes (CRM contact data, D&A role assignment, zero-party professional profile from forms). Sections 3.4 through 3.6 renumbered to 3.5 through 3.7; all cross-references updated. Resolved inline comment flagging firmographic vs. professional profile terminology; updated Economic Buyer and Ratifier notes to use "professional profile data" where individual-level attributes are meant. Added four ePDF behavioral signals (page loaded, download from viewer, internal search, print) as distinct rows in the Section 3.1 table. Added provisional ePDF weights to Section 5 role profiles: Champion (+8 download from viewer), Economic Buyer (+5 print), User (+8 internal search, +5 print for how-to content), Ratifier (+10 internal search, +5 download from viewer).

**v0.6.2 (February 13, 2026):** Multi-solution expansion of Section 4. Added sub-solution granularity advisory note explaining that IT encompasses three named solutions (Autonomous Service Ops, AI + Data Orchestration, Autonomous IT & Security) and CRM encompasses Service (CSM, FSM) and Sales (SOM), with title-to-role mappings varying across sub-solutions within each category. Added IT-specific title mappings to all five role definitions (Sections 4.1 through 4.5) sourced from the IT Buying Group Program Working Deck, with cross-solution observations for each role. Replaced Education-stage JTBD gap callout with defined JTBD for all five roles, sourced from the IT BG program and generalized across solution categories. Added convergence point reconciliation note addressing the discrepancy between the CRM program (Champion included at Final Commitment) and IT program (Champion excluded); retained the more inclusive CRM model. Added IT Buying Group Program Working Deck and CRM Buyer FY26 Narrative, Messaging, and Works Brief to the References section.

**v0.6.3 (March 1, 2026):** Cross-document consistency alignment. Updated solution category taxonomy throughout: replaced "five solution categories (IT, CRM, HR, Security & Risk, Finance)" with "four solution categories (IT, CRM, Employee Experience, Security & Risk)" in Layer 2 body text, Section 6 pipeline Step 4, and Appendix C glossary entry. Employee Experience encompasses HR, Finance, and Supply Chain per the organizational merger. Updated footnote 5 to lead with current four-category operating model while retaining the Walking Deck's original five-category lineage for traceability. Updated footnote 18 to clarify that HR and Finance & Supply Chain have been merged into Employee Experience. These changes align the Signal Definition Document with the Segmentation Framework, Measurement Plan, Playbook, and Vision & Strategy document per the cross-document consistency analysis.

[^1]: Source: Buying Groups GTM Transformation Walking Deck, slide 41.

[^2]: Source: Buying Groups FAQ (internal). "Role" refers to buying group members; "Persona" is reserved for C-level executives (CIO, CCO).

[^3]: Source: Buying Groups FAQ (internal). ServiceNow defines nine total buying group roles. Five are prioritized for launch: Champion, Economic Buyer, Influencer, User, and Ratifier. The remaining four (Executive Sponsor, Project Owner, Security Leader, Technical Validator) are planned for future phases.

[^4]: Source: Buying Groups GTM Transformation Walking Deck, slide 25. Key shifts include: from leads to buying groups, from lead volume to pipeline quality, from separate lists to unified TAL, and from sequential handoffs to unified GTM.

[^5]: Source: Buying Groups GTM Transformation Walking Deck, slides 25 and 45. The Walking Deck originally defined five solution categories: IT, CRM, HR, Security & Risk, and Finance & Supply Chain, each with specific business units mapped. NOTE: Finance & Supply Chain has been merged with HR to form the Employee Experience category. The current operating model uses four solution categories: IT, CRM, Employee Experience, and Security & Risk.

[^6]: Source: Buying Group Audience Segments, slides 7 and 31–32; Buying Groups Walking Deck, slide 31. Stage criteria: Targeted = no engagement in last 180 days; Engaged = at least 1 engagement in last 180 days; Prioritized = 2+ members or hand-raiser engaged in last 90 days, no active opportunity; Qualified = at least 1 accepted member converted into a Stage 1 opportunity.

[^7]: Source: Buying Group Audience Segments, campaign cohorts slides. Four campaign cohorts: Education (Targeted stage, \<2 BG members), Acquisition (Engaged or Prioritized, 2+ members, no active opportunity), Progression Early-to-Mature (Qualified, Stage 2–4 opportunity), and Progression Win Now (Qualified, Stage 5–7 opportunity).

[^8]: Source: Buying Group Audience Segments, slide 17. Short-term activation uses CRM as the intermediary between D&A and AEP. Cohorts assigned at Account and Buying Group level only.

[^9]: Source: Digital BG Tech & Campaign Weekly Sync Notes (internal). Implementation milestones: CRM go-live AMS (Feb 1–2), EMEA/APAC (Feb 8–9), campaign cohort go-live (Feb 6), web activation (Feb 11–12), Kafka go-live (March 15).

[^10]: Source: Buying Group Audience Segments, slide 9. February MVP classification is limited to three roles: Economic Buyer, Champion, and Influencer, based on job level, role, function, and alignment to a solution category. All others default to Unclassified.

[^11]: Source: Buying Group Audience Segments, CRM Deal Progression Requirements. New Dynamics requirements: opportunities require an attached Buying Group; Stage 3→4 requires a Champion identified; Stage 4→5 requires an Economic Buyer identified.

[^12]: Source: Buying Groups FAQ (internal). A buying group can include more than 22 people. While typically only a single Economic Buyer or Champion, there may be several Influencers, Users, or Ratifiers.

[^13]: Source: Buying Group Audience Segments, slide 10. BG Member engagement score (0–100) calculated based on persona relevance and marketing & sales engagement over the last 180 days. Aggregates to four levels: Member, Buying Group, Opportunity, and Account.

[^14]: Source: Buying Group Audience Segments, cohort criteria. Accounts with \<2 BG members default to Education cohort (BG Stage = Targeted, BG Engagement = Low, no active opportunity).

[^15]: Source: Buying Groups GTM Transformation Walking Deck, slide 10. Program success metrics: 20% Stage 2→5 conversion increase QoQ; 7%+ win rate increase YoY; 80%+ of opportunities with 2+ engaged contacts; 90%+ CRM adoption.

[^16]: Source: Buying Group Audience Segments, slide 10. BG-level High engagement: Economic Buyer is High OR 2+ members are High OR 1 High member + 1 High unclassified hand-raiser.

[^17]: Source: Buying Groups GTM Transformation Walking Deck, slides 43 and 46. Originally five solution categories with business units: IT (IT Ops, App Engine, ITAM, ITSM, Portfolio Mgmt, Platform), CRM (Field Service, Customer Service, Sales & Order Mgmt), Security & Risk, HR, and Finance & Supply Chain. HR and Finance & Supply Chain have since been merged into Employee Experience.
