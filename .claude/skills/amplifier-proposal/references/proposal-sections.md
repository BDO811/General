# Proposal Sections — Content Rules

**Naming:** every heading, label, header and footer names the partnership as
"Amplifier Health and [Partner]". Never "x", never the multiplication sign.

**Brand:** the page is rendered in the partner's extracted palette with their logo
mark in the top bar. See SKILL.md Step 2.5 and references/pdf-template.md.


## Section 01 — What We Know About [Partner]

Heading format: "What We Know About [Partner Name]" — always this exact pattern, title case.

Voice: clean, professional, declarative statements. Subject + verb + object. Active voice. No opinions, no colloquial framing, no "what caught my attention." Facts that are commercially or clinically relevant to the Amplifier fit.

Bullets should cover:
- Product description: what it does, how it is delivered
- Distribution: member/patient volume, employer or payer clients
- Clinical evidence or outcomes data if published
- Funding and valuation (if relevant and recent)
- Current leadership (CEO name)
- The specific gap or signal that Sona-2 addresses

Stat block (3 cells): choose numbers that demonstrate scale — covered lives, sessions/week, states, raise amount, valuation.

Wrong voice: "What stopped me was the behavior change stat."
Right voice: "The platform demonstrates measurable behavior change: users walk 21% more, tracked via Apple Health integration."

---

## Section 02 — The Amplifier Fit

Heading: "How Sona-2 Fits [Partner]" or similar — explain the acoustic layer and what it adds.

Bullets should cover:
- The specific audio stream where Sona-2 operates (session recording, coaching call, voice-led app interaction)
- Which biomarkers are extracted (depression severity, anxiety index, cognitive load — pick the clinically relevant subset)
- The clinical gap it fills (continuous signal between episodic surveys, comorbidity detection, treatment response monitoring)
- What changes for the member/patient: nothing. Zero UX disruption.
- What changes for the clinical team or platform: continuous acoustic biomarker timeline

---

## Section 03 — Integration Architecture

Heading: "How It Works"

Bullets should cover:
- Integration point: where in the product stack the audio is captured and sent to Sona-2
- API call pattern: session audio routed to Sona-2 V2 API post-session; JSON response with biomarker scores
- HIPAA: BAA executed at account creation; audio processed and discarded, only feature vectors retained
- Output: how and where results surface (care coordinator dashboard, clinician view, partner analytics layer)
- Zero workflow change for the end user or clinician

Hard rule: Never mention a 30-day baseline period. Sona-2 produces signal immediately from the first call.

---

## Section 04 — Commercial Structure

Heading: "Partnership Structure" or "How We Work Together"

Bullets should cover:
- Pricing model: per-member-per-month or per-session fee, billed to employer/payer or platform
- Pilot structure: cohort size (typically 200-500 members/patients), duration (60-90 days), which care modalities
- What Amplifier provides: integration support, HIPAA documentation, technical onboarding
- Optional: exclusivity window for first-mover advantage in the segment
- Optional: dataset licensing if the partner's audio data has labeling value

---

## Section 05 — Why Amplifier Health

Heading: "Why Amplifier Health"

Bullets should cover (in this order, no others):
1. Dataset moat: Sona-2 trained on 2M+ clinically-labeled real-world voice interactions — no competitor has clinical-grade labeled audio at this scale
2. Model differentiation: the only acoustic foundation model built specifically for clinical biomarker extraction
3. Regulatory runway: FDA De Novo clearance pathway underway for depression biomarker — creates sustainable clinical defensibility
4. Team: clinicians, acoustic ML engineers, and enterprise health executives with direct sector experience

Hard rule: Never include a "Competitive moat" bullet. Never name Winterlight Labs or Sonde Health.

---

## Section 06 — REMOVED

Section 06 does not exist in the Amplifier proposal format. Do not include a "Next Steps," "Timeline," or "90-Day Pathway" section. The proposal flows directly from Section 05 to the Get Started page (labeled 07).

---

## Section 07 — Get Started (Final Page)

Section label: "07  ·  GET STARTED"
H2: "Everything You Need to Build"

Dark callout box labeled "FROM AMIT MEHTA  ·  CEO, AMPLIFIER HEALTH":
"I'm looking forward to speaking with you. In the meantime, if you'd like to explore the platform, here is everything you need. Fully self-service. Fully documented. You should be up and running in under 5 minutes."

Three full-width resource boxes:
1. Label: "COMPANY AND PLATFORM OVERVIEW" / Title: "amplifierhealth.com" / Desc: "Product overview, model specs, use cases, case studies, and API partner program."
2. Label: "V2 API DOCUMENTATION" / Title: "docs.amplifierhealth.com" / Desc: "Full V2 API reference, authentication, endpoints, request/response schemas, and guides."
3. Label: "V2 DEVELOPER CONSOLE" / Title: "console.amplifierhealth.com" / Desc: "Create your account, generate API keys, run test inferences, and monitor usage."

Two half-width resource boxes side by side:
Left: Label "JSON SCHEMA" / Title "Direct JSON Schema for the V2 API, link in docs.amplifierhealth.com"
Right: Label "SWAGGER UI" / Title "Interactive API docs, test live calls from your browser"

Day-one table header: "WHAT YOU GET ON DAY ONE"
Rows:
- API Key / Immediate access to the V2 inference endpoint
- Test Audio Samples / Pre-labeled audio files to validate your integration
- Response Schema / Full JSON schema with all biomarker fields documented
- HIPAA BAA / Executed at account creation, zero PHI required
- Support / Direct technical support via partnerships@amplifierhealth.com
