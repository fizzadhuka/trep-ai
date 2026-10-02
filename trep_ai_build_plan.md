# T-Rep AI — Deep Build Plan

**Theme 2: Un-carrier for Limitless Possibility (Agentic AI)**
5 people | 12 hours | 8:30 AM – 5:00 PM (with 30 min lunch)

---

## Rubric Alignment Strategy

The judges are CFO, CLO, Chief Network Officer, and VP Product & Engineering. Every decision in this plan is made to score well on what each of them cares about.

| Rubric Dimension | Who Cares Most | How We Score It |
|---|---|---|
| Innovation / Novelty | All | No ISP or telecom has a unified agentic execution layer with live conversation listening across rep tools. Emphasize that "the rep as bridge" is the status quo we're eliminating. |
| Technical Execution | VP Engineering, CNO | Working live demo. Real LLM calls. Real-time Deepgram transcription. Streaming execution steps. Not a slideshow. |
| Business Impact / ROI | CFO | Transaction time cut from ~22 min to ~8 min. Quantify across store count. Slide with actual math. |
| Customer & Employee Experience | All | Grounded in real retail interview data — not invented pain points. Make this explicit in the pitch. |
| Feasibility / Path to Production | CNO, VP Engineering | Show a clean API contract. "We mocked the Tapestry/DASH layer — swapping in real endpoints is a configuration change, not a redesign." |
| Presentation Clarity | All | Live demo does more than any slide. Person 5 runs the demo. Person 4 has the laptop. Backup: screen recording saved. |

**Rule: every feature you build should map to at least one of these dimensions. If it doesn't, cut it.**

---

## How Deepgram Fits In

The dashboard is not a lookup tool — it's a live co-pilot. Instead of the rep typing what the customer is asking about, a microphone captures the in-store conversation in real time. Deepgram transcribes it continuously via WebSocket. The AI reads the live transcript, detects intent, and automatically surfaces the relevant plan info, promo eligibility, and bill delta — without the rep touching anything.

**The demo moment:** A scripted conversation plays out between the rep and a simulated customer. The rep never touches the keyboard. The dashboard updates in real time as topics are mentioned. That's the moment that wins the room.

**Flow:**
```
Mic (browser) → Deepgram WebSocket → Live Transcript
                                            ↓
                              Backend /intent endpoint
                                            ↓
                         Intent Agent (Claude) detects topic
                                            ↓
                    Queries mock plan/promo/device catalog
                                            ↓
                      Frontend dashboard updates inline
```

---

## Team Structure

No standalone presentation role. Presentation work is baked into the frontend track. Both frontend people own their UI domains AND share the demo/deck.

### Person 1 — AI/LLM Lead (Backend)
Owns everything that touches the language model and the Deepgram integration: prompt engineering, structured output, intent detection from live transcripts, and the endpoints that generate the customer brief, bill delta, and PAH logic.

**Stack:** Python, FastAPI, Anthropic Python SDK, Deepgram Python SDK, Pydantic for output validation.

**Deliverables:**
- `/brief` — takes a customer object, returns a structured AI-generated brief
- `/bill-delta` — takes current plan + proposed change, returns exact dollar delta with plain-language explanation
- `/pah-check` — given account + visiting user, returns what actions are permitted
- `/intent` — receives transcript chunk from frontend, returns detected topic and data to surface
- `deepgram_service.py` — backend Deepgram WebSocket handler (fallback if browser SDK has issues)
- `intent_agent.py` — LLM layer that parses transcript and maps to catalog queries
- `intent_prompt.py` — prompt template for intent detection

### Person 2 — Data & Mock Systems Lead (Backend)
Owns the fake data layer that stands in for Tapestry, DASH, trade-in systems, and promotions. Nobody builds anything until Person 2 publishes the data schema. This person is the dependency blocker in Hour 1.

**Stack:** Python, FastAPI, JSON flat files (no database needed).

**Deliverables:**
- `mock_customers.json` — 5 detailed customer profiles
- `mock_plans.json` — plan catalog with pricing tiers
- `mock_promos.json` — active promotions and eligibility rules
- `mock_devices.json` — device catalog with trade-in values
- `/customer/{id}` — returns full customer object
- `/trade-in/{device_model}` — returns trade-in value
- `/promotions?from_plan=X&to_plan=Y` — returns applicable promos
- `/execute/steps` — returns ordered step list for a given transaction type
- `calculate_new_bill(transaction)` — utility used by execution engine

### Person 3 — Execution Agent Lead (Backend)
Owns the agentic core — the orchestration engine that receives a confirmed transaction and executes each step in sequence, streaming live status to the frontend.

**Stack:** Python, FastAPI, WebSockets (or SSE as fallback), asyncio for step sequencing.

**Deliverables:**
- `/execute` WebSocket endpoint — accepts transaction payload, streams step updates
- Step definitions with realistic fake latency (0.8–2s per step)
- Error + retry scenario on Step 3
- Final bill generation at completion
- `execution_ws.py` — WebSocket handler
- `execution_service.py` — core step sequencing logic
- REST fallback: `POST /execute/simulate` for if WebSocket integration gets complex

### Person 4 — Frontend Lead (Design + Frontend)
Owns Phase 1 of the UI: customer lookup, the brief card, bill explorer, conversation listener, and the overall design system.

**Stack:** React + Vite, Tailwind CSS, shadcn/ui, Deepgram Browser SDK.

**Deliverables:**
- `CustomerLookup.jsx` — number input, submit, loading state
- `CustomerBrief.jsx` — plan summary, upgrade eligibility badge, bill total, trade-in value, open issue flag, PAH status
- `BillExplorer.jsx` — "What if I…" dropdown with instant delta display
- `PAHPanel.jsx` — conditional panel when non-PAH detected
- `ConversationListener.jsx` — mic toggle UI, live scrolling transcript, intent detection indicator
- `useDeepgram.js` — opens Deepgram WebSocket, streams mic audio, returns live transcript chunks
- Global design: T-Mobile color tokens, dark background, magenta accents

### Person 5 — Frontend + Demo Lead (Design + Frontend)
Owns Phase 2 of the UI: the execution screen and everything a judge sees during the demo. Also owns the pitch deck and runs the live demo. Does not touch the keyboard during the presentation — Person 4 has the laptop, Person 5 narrates.

**Stack:** React (same repo as Person 4), PowerPoint or Google Slides.

**Deliverables:**
- `ExecutionScreen.jsx` — confirmed transaction summary → Execute CTA → live step progress → final bill reveal
- `StepTracker.jsx` — animated step list with pending / in-progress / complete / error / retrying states
- `FinalBillCard.jsx` — clean receipt-style view of completed transaction
- `useWebSocket.js` — WebSocket connection hook for execution status streaming
- Pitch deck (6 slides)
- Demo script (written, practiced, timed)

---

## Data Schema

Person 2 publishes this in Hour 1 — everyone waits on it.

```json
{
  "account_id": "5550192",
  "primary_holder": {
    "name": "Maria Gonzalez",
    "is_present": true
  },
  "current_plan": {
    "name": "Magenta",
    "monthly_total": 85.00,
    "lines": 3
  },
  "upgrade_eligibility": {
    "eligible": true,
    "current_device": "iPhone 13 Pro",
    "months_in": 18,
    "trade_in_value": 320.00
  },
  "open_issues": [
    { "type": "billing_dispute", "description": "Overcharge from June cycle", "status": "open" }
  ],
  "authorized_users": ["Maria Gonzalez"],
  "last_interaction": "2026-06-14"
}
```

All five mock customers must follow this exact shape. No surprises mid-integration.

---

## Mock Customer Profiles

Build these five. Demo uses Profile A. Profile C triggers the PAH flow.

| ID | Name | Scenario | Key Detail |
|---|---|---|---|
| A | Maria Gonzalez | Primary demo — upgrade + trade-in + open billing dispute | IS the PAH, eligible for iPhone 16, $320 trade-in |
| B | Derek Wu | Simple plan upgrade, no trade-in | Wants Magenta MAX, no device change — clean path |
| C | Jake Patel | PAH issue — wants to add a line | NOT the PAH (mom is), triggers PAH Assist panel |
| D | Sandra Okafor | Payment issue + upgrade | Has a failed payment on file, still wants to upgrade |
| E | Tom Reyes | Already on best plan, browsing | Nothing to upgrade — brief shows this cleanly, no dead UI states |

---

## Execution Step Sequence

For a trade-in upgrade transaction (Maria, Profile A):

```
Step 1: Verifying account identity                  ~1.0s
Step 2: Confirming trade-in value ($320)            ~1.2s
Step 3: Applying upgrade promotion                  ~0.8s  ← error + retry here
Step 4: Processing plan change to Magenta MAX       ~1.5s
Step 5: Entering order into DASH                    ~1.0s
Step 6: Generating updated bill                     ~0.8s
✓ Complete — new monthly total: $107/month
```

Step 3 fails once with "Promo validation timeout" and auto-retries within 2 seconds. This demonstrates the agent handles exceptions, not just the happy path. Judges will notice.

---

## Deepgram Integration Spec

### Frontend (Person 4 owns `useDeepgram.js`)

```js
import { createClient, LiveTranscriptionEvents } from "@deepgram/sdk";

export function useDeepgram(onTranscript) {
  const start = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const deepgram = createClient(import.meta.env.VITE_DEEPGRAM_API_KEY);
    const connection = deepgram.listen.live({
      model: "nova-2",
      language: "en-US",
      smart_format: true,
      interim_results: true,
    });

    connection.on(LiveTranscriptionEvents.Transcript, (data) => {
      const transcript = data.channel.alternatives[0].transcript;
      if (transcript && data.is_final) {
        onTranscript(transcript); // send to intent layer
      }
    });

    const recorder = new MediaRecorder(stream);
    recorder.ondataavailable = (e) => connection.send(e.data);
    recorder.start(250); // send chunks every 250ms
  };

  return { start };
}
```

### Backend Intent Endpoint (Person 1 owns `/intent`)

Receives final transcript chunks from frontend and runs intent detection:

```python
@router.post("/intent")
async def detect_intent(payload: IntentRequest):
    # payload: { transcript: str, customer_id: str }
    # 1. Run LLM intent detection
    # 2. Map detected topic to catalog query
    # 3. Return relevant data to surface in dashboard
    result = await intent_agent.run(payload.transcript, payload.customer_id)
    return result  # { topic, data, display_type }
```

### Intent Agent Prompt (Person 1 owns `intent_prompt.py`)

```
You are a T-Mobile rep assistant listening to a live customer conversation.

Given this transcript chunk, identify if the customer is asking about:
- A specific plan (name it)
- A device upgrade (name the device if mentioned)
- Adding or removing a line
- A trade-in
- A promo or discount
- A billing question

If a topic is detected, return:
{
  "topic": "plan_upgrade" | "device_inquiry" | "add_line" | "trade_in" | "promo" | "billing" | "none",
  "details": { ... specific extracted details ... },
  "action": "fetch_plan" | "fetch_device" | "calculate_delta" | "fetch_promo" | "none"
}

If no relevant topic is detected, return { "topic": "none" }.
Transcript: {transcript}
```

### ConversationListener Component (Person 4 owns)

```jsx
// Shows: mic toggle | live transcript scroll | intent badge
// When intent detected: dashboard panels update automatically
// No rep input needed — fully passive
```

The intent badge updates in real time: e.g., "Detected: iPhone 16 inquiry → Magenta MAX plan" — and the BillExplorer pre-loads the relevant delta without the rep selecting anything.

### Fallback Plan for Deepgram
If Deepgram WebSocket is flaky during the demo, Person 4 adds a hidden text input that sends transcript chunks manually. The demo still works — the AI still responds — but the mic is the primary path. Test this the night before.

---

## Hour-by-Hour Plan

Net build time after 30-min lunch = 11.5 hours.

### HOUR 1 | 8:30–9:30 AM — Environment & Schema

**Everyone:** First 20 minutes all-hands. Agree on tech stack. Person 2 writes the customer schema live on a shared screen. Everyone confirms they can parse it before splitting.

**Person 1:**
- Clone repo, set up `/backend` FastAPI app with `main.py`, `routers/`, `schemas/`
- Install: `fastapi uvicorn anthropic deepgram-sdk pydantic python-dotenv`
- Create `.env` with `ANTHROPIC_API_KEY` and `DEEPGRAM_API_KEY`, confirm both clients initialize
- Write stub routes: `POST /brief`, `POST /bill-delta`, `GET /pah-check`, `POST /intent`
- Confirm a raw `client.messages.create()` call returns output

**Person 2:**
- Write `mock_customers.json` with all 5 profiles — most time-critical task of Hour 1
- Write `mock_promos.json` (3–4 promos: new phone discount, loyalty credit, bundle discount)
- Write `mock_devices.json` (trade-in values for iPhone 12/13/14/15/16 and Galaxy S23/S24)
- Write `mock_plans.json` with pricing tiers
- Build and test `GET /customer/{id}` returning a customer object
- Share full schema in team chat before the hour ends

**Person 3:**
- Research FastAPI WebSocket syntax — have a working echo WebSocket by end of hour
- Define step schema: `{ id, name, status: pending|active|complete|error|retrying, duration_ms }`
- Write `STEP_DEFINITIONS` dict mapping transaction types to ordered step lists
- Stub `WS /execute`

**Person 4:**
- `npm create vite@latest frontend -- --template react`
- Install: `tailwindcss shadcn/ui @deepgram/sdk`
- Configure T-Mobile color tokens in `tailwind.config.js`:
  - `tmobile-magenta: #E20074`, `tmobile-black: #000000`, `tmobile-berry: #861B54`, `tmobile-gray: #6A6A6A`
- Create folder structure: `components/lookup/`, `components/brief/`, `components/execute/`, `components/listener/`, `components/shared/`
- Build `CustomerLookup.jsx` — input field + submit button, no logic yet
- Install Deepgram browser SDK, confirm it imports without errors

**Person 5:**
- Open Figma, create file with T-Mobile color styles
- Draw lo-fi wireframes for 4 screens: (1) lookup + brief, (2) bill explorer, (3) execution progress, (4) conversation listener panel
- Share Figma link in team chat
- Open pitch deck, set up 6 slides with titles only

**Hour 1 exit check:** Backend runs on localhost:8000. Frontend runs on localhost:5173. Schema published. Everyone can hit `/customer/5550192` and get Maria's data. Deepgram SDK imports cleanly on both frontend and backend.

---

### HOUR 2 | 9:30–10:30 AM — First Endpoints + First Components

**Person 1:**
- Write system prompt for `/brief` (see prompt templates section below)
- Implement Pydantic `BriefResponse` model
- Test `/brief` with Maria's profile — confirm output is valid JSON
- Begin `intent_agent.py` stub — set up the LLM call structure

**Person 2:**
- Build `GET /trade-in/{device_model}` — returns `{ device, value, condition: "good" }`
- Build `GET /promotions?from_plan=X&to_plan=Y` — returns applicable promos
- Verify all 5 customer profiles load correctly
- Write "Mock API Reference" in README — list all endpoints, inputs, outputs. Pin in team chat.

**Person 3:**
- Build full WebSocket handler for `/execute` with step sequencing and error+retry logic on Step 3
- Test with `wscat` or simple HTML test page

**Person 4:**
- Build `CustomerBrief.jsx` — card layout with slots for: name, plan badge, monthly cost, upgrade badge, trade-in value, open issue pill, PAH status
- Wire to `/customer/{id}` — entering a number renders the brief (raw data for now, AI connects in Hour 5)
- Start `useDeepgram.js` hook — open mic, confirm `getUserMedia` works in browser

**Person 5:**
- Build `BillExplorer.jsx` — dropdown of plan options with delta display slot (props only, no data yet)
- Fill out pitch deck Slide 1 (The Problem) with real retail interview data:
  - ~40 customers/day per rep
  - Trade-in flow requires manual entry across 3+ systems
  - Fetch AI gives outdated info mid-interaction
  - Reps spend more time in tabs than in the conversation

**Hour 2 exit check:** Enter a customer ID, see a rendered CustomerBrief. WebSocket streams 6 steps to test client. Person 1 has working AI brief output. Mic access confirmed in browser.

---

### HOUR 3 | 10:30–11:30 AM — Bill Delta + Conversation Listener + Execution UI

**Person 1:**
- Write `/bill-delta` endpoint:
  - Input: `{ current_plan, proposed_change, customer_id }`
  - Logic: calculate new monthly total from Person 2's plan pricing data
  - LLM layer: convert delta to one plain-language sentence
  - Return: `{ delta_dollars, direction: "increase"|"decrease", explanation }`
- Write `/intent` endpoint:
  - Input: `{ transcript: str, customer_id: str }`
  - Call `intent_agent.run()` with the intent detection prompt
  - Return: `{ topic, details, action, data_to_surface }`
- Test intent detection with sample transcript strings: "I was thinking about upgrading to the iPhone 16", "how much would it cost to add another line"

**Person 2:**
- Add `mock_plans.json` with per-line pricing for all plans
- Build `calculate_new_bill(transaction)` utility function — used by Person 3's execution engine
- Support Person 3 with final bill calculation

**Person 3:**
- Polish execution WebSocket — add proper connection handling, error catching
- Add `transaction_summary` to done payload: `{ steps_completed, duration_seconds, final_bill, promo_applied }`
- Build REST fallback: `POST /execute/simulate`

**Person 4:**
- Wire `BillExplorer` to `/bill-delta` — plan selection → API call → delta renders inline
- Complete `useDeepgram.js` — connect WebSocket to Deepgram, stream mic audio, return final transcript chunks via callback
- Begin `ConversationListener.jsx` — mic toggle button, live scrolling transcript display

**Person 5:**
- Build `ExecutionScreen.jsx` — left panel: transaction summary, right panel: step tracker slot
- Build `StepTracker.jsx` — 6 steps, each with status icon: gray circle (pending) → spinner (active) → green check (complete) → red X (error) → yellow refresh (retrying)
- This component takes a steps array as props and renders state — WebSocket connects in Hour 6

**Hour 3 exit check:** Bill delta works end-to-end. Deepgram mic is streaming audio. Intent endpoint returns topic detection for sample transcripts. Execution screen UI renders with hardcoded step array.

---

### HOUR 4 | 11:30 AM–12:30 PM — PAH Feature + Conversation Listener Integration

**Person 1:**
- Build `/pah-check`:
  - Input: `{ account_id, visiting_user_name }`
  - Rule-based: check if visiting user is in `authorized_users`
  - If NOT authorized: LLM generates a friendly explanation of what CAN still be done
  - Return: `{ is_authorized, permitted_actions, restricted_actions, authorization_options }`
- Test with Profile C (Jake — not the PAH)
- Connect intent agent to mock catalog: when intent = "plan_upgrade", fetch from `mock_plans.json` and return relevant plan data

**Person 2:**
- Define `permitted_actions` list (what non-PAH can do vs. can't)
- Verify all mock endpoints are stable
- Write Postman collection with all endpoints — share with team

**Person 3:**
- Build second transaction type: `"plan_upgrade_only"` (no trade-in) — for Profile B
- Stress-test WebSocket with rapid reconnects

**Person 4:**
- Complete `ConversationListener.jsx`:
  - Mic on/off toggle with visual indicator
  - Live scrolling transcript display
  - Intent badge: updates when topic is detected (e.g., "Detected: iPhone 16 inquiry")
  - On intent detection: call `/intent`, receive data, pass to parent to update `BillExplorer` or `CustomerBrief` automatically
- Wire transcript chunks to `/intent` endpoint: every final transcript segment sent to backend
- Build `PAHPanel.jsx` — conditionally rendered when `is_authorized === false`
  - Show: what they CAN do (green list), what's restricted (grayed out), two buttons: "Request Remote Authorization" and "Have PAH Come In"

**Person 5:**
- Complete pitch deck slides 2–4:
  - Slide 2: "Today the rep is the manual bridge between every system. We made AI the bridge instead." — before/after diagram
  - Slide 4: Architecture diagram — Customer Data Layer → LLM Orchestration + Deepgram → Execution Agent → Rep UI
- Write first draft of demo script

**Hour 4 exit check:** PAH panel renders for Profile C. Conversation listener captures mic audio, displays transcript, and fires intent detection. Dashboard responds to detected intent automatically. All mock endpoints documented.

---

### HOUR 5 | 12:30–1:00 PM — LUNCH (30 min)

Hard stop. Eat.

Before closing laptops: everyone calls out their Hour 5 blockers in team chat.

---

### HOUR 5 (CONT.) | 1:00–2:00 PM — Integration Sprint

Highest-risk hour. Get the happy path working end-to-end before any polish.

**Person 1:**
- Swap `CustomerBrief` data source from raw customer object to AI-generated brief response
- Work with Person 4 to ensure frontend brief card fields map to LLM output
- Add Pydantic validation + retry logic (max 2 retries) if LLM output is inconsistent
- Verify intent → catalog query → dashboard update works for at least 2 intent types (plan upgrade, device inquiry)

**Person 2:**
- Support integration debugging — fix any schema mismatches
- Build final bill display data: `{ new_monthly_total, breakdown: [{ label, amount }] }`

**Person 3 + Person 5 (paired):**
- Connect `StepTracker` to live WebSocket
- Steps animate in real time as messages arrive
- Test error + retry scenario — confirm UI handles it (correct icon states, no crash)
- Get `FinalBillCard.jsx` rendering the completion payload

**Person 4:**
- Verify `BillExplorer` still works after any schema changes
- Connect `PAHPanel` to live `/pah-check` endpoint
- Ensure `ConversationListener` → `/intent` → dashboard update flow works end-to-end
  - Test: say "I want to upgrade to Go5G Plus" → intent detected → BillExplorer pre-loads delta automatically

**Hour 5 exit check (critical gate):** Enter Profile A's number → AI brief renders → say a plan name aloud → dashboard updates automatically → explore bill delta → click Execute → watch 6 steps complete with error+retry on Step 3 → see final bill. If this doesn't work by 2:00 PM, go to Fallback Plan.

**Fallback Plan:** If Deepgram integration is not stable, switch ConversationListener to a text input field. Rep types a short phrase ("upgrade iPhone 16"), intent fires the same way. Deepgram is the impressive layer — but the core demo still works without it.

---

### HOUR 6 | 2:00–3:00 PM — Polish + Second Demo Profile

**Person 1:**
- Run brief and bill-delta on all 5 profiles — fix any inconsistent LLM output
- Add response caching for customer brief (same customer looked up twice = cached response)
- Tune intent prompt: test with natural conversational phrases, not just clean queries

**Person 2:**
- Support integration bugs
- Verify final bill calculation is accurate for all transaction types

**Person 3:**
- Add smooth completion animation trigger: 500ms delay after `status: "done"` before `FinalBillCard` appears
- Ensure WebSocket cleans up properly after completion (no memory leaks, clean reconnect)

**Person 4:**
- UI polish on `CustomerBrief` and `BillExplorer`:
  - Upgrade eligibility: green badge ("Eligible ✓") or amber ("Not Yet")
  - Trade-in value: prominent magenta number
  - Open issue: red dot indicator on card header
  - Bill total: large, clear, center-aligned
- Polish `ConversationListener`: smooth transcript scroll, clear mic-active indicator (pulsing dot)
- Test on 1080p screen

**Person 5:**
- Complete full demo flow for Profile B (Derek — backup demo path)
- Add "Execute" confirmation modal — before execution begins: "Confirm: Upgrade Maria to Magenta MAX + iPhone 16. Trade-in: $320 applied. New monthly: $107. Proceed?" with Cancel and Confirm buttons
- This single interaction makes the product feel safe and real — judges notice when there's no confirmation step

**Hour 6 exit check:** Two demo profiles work end-to-end. PAH panel works for Profile C. Conversation listener updates dashboard from voice. UI looks like a product. Polish is 80% done.

---

### HOUR 7 | 3:00–4:00 PM — Rehearsal + Hardening

**First 30 minutes — First full demo rehearsal:**
- Person 5 narrates, Person 4 drives the laptop
- Run complete demo: Maria (Profile A) full flow including Deepgram voice detection, then show Profile C (PAH trigger)
- Time it — target 4–5 minutes for live demo
- Person 1, 2, 3: watch as judges. Note every moment that's confusing, slow, or broken.

**After rehearsal — fix only what broke the narrative:**
- Person 4: fix any UI glitches spotted
- Person 3: if WebSocket was flaky, switch to SSE or polling fallback now
- Person 1: if LLM output was confusing, tighten the prompt; if Deepgram intent was misfiring, raise the confidence threshold
- Person 5: refine demo script based on what Person 4 naturally said during the run-through

**Person 5 (while others harden) — Pitch deck Slide 5 (Business Impact):**
- Average transaction: 22 min → estimated 8 min with T-Rep AI (conservative)
- Rep serves 40 customers/day → time freed: (22–8) × 40 = 560 minutes/rep/day
- Equivalent to 9+ additional customer interactions per rep per day
- T-Mobile has ~7,000 retail stores — estimate additional revenue potential per year
- Show the formula, give a range. CFO respects transparency.

**Slide 6 (What's Next):**
1. Real Tapestry/DASH API integration via internal platform team
2. Rep feedback loop for brief accuracy and intent detection improvement
3. Pilot program: 10 stores, 60-day measurement period

**Hour 7 exit check:** One full clean rehearsal completed. Deck is 95% done. Person 5 can run the demo script without reading it.

---

### HOUR 8 | 4:00–5:00 PM — Final Rehearsal + Hard Stop

**4:00–4:30 PM — Second full run-through:**
- Simulate judge questions after the demo (see Q&A Prep below)
- If bugs surface: Person 4 or 3 fixes immediately. Person 1 and 2 watch, not code.

**4:30 PM — Code freeze:**
- No new commits. Nothing new gets built.
- Person 4: open `localhost:5173` on a second device and confirm full flow works outside your own machine
- Person 3: restart backend once — confirm clean state
- Person 2: verify all 5 profiles load cleanly
- Person 5: practice opening 30 seconds of pitch until completely natural
- Save a screen recording of the full demo as backup

**5:00 PM — Hard stop.**

---

## Priority Tiers — What to Cut If You're Behind

### Tier 1 — Non-Negotiable
If you don't have these, you don't have a product.
1. Customer number lookup → AI brief renders
2. Bill delta: explore a plan change → dollar delta appears inline
3. Execute button → step-by-step agent progress → final bill reveal

### Tier 2 — Strong to Have
4. Live Deepgram transcription → automatic dashboard updates from voice
5. Error + retry scenario in execution (shows the agent is intelligent)
6. PAH Assist panel (broadens the problem scope)
7. Confirmation modal before execution

### Tier 3 — Polish (only if Tier 1 and 2 are done)
- Multiple demo profiles working
- Smooth animations between screens
- Loading shimmer states
- Responsive layout / mobile view

### Cut Completely If Behind
- Any feature not in Tier 1 or 2
- PAH panel, if it would jeopardize Tier 1 completion
- Slide 5 math, if deck needs to be shorter — verbal explanation is fine
- Background illustrations or logo assets

**If 2+ hours behind at Hour 5's integration check:** cut PAH and Deepgram voice, simplify to one demo profile, put all saved time into making Tier 1 flawless. A perfect 3-minute demo beats a broken 8-minute one.

---

## Q&A Prep

**"How would this actually integrate with Tapestry and DASH?"**
"We built a clean API contract for the data and execution layers — the mock endpoints follow the same interface a real Tapestry integration would use. Swapping in actual endpoints is a configuration change, not an architectural one. The hard problem is the orchestration logic, which we built."

**"What's the cost per interaction?"**
"Claude Haiku runs under $0.01 per brief call. For 40 customers per rep per day, that's well under $1/rep/day. Deepgram's Nova-2 model is similarly low-cost per minute of audio. Given the transaction time savings we estimated, the ROI is strongly positive within months."

**"What if the agent makes an error during execution?"**
"Two safeguards: first, the rep reviews and confirms the full transaction before execution begins — nothing happens without human approval. Second, as you saw in the demo, the agent detects step failures and retries automatically. Every step is logged, so errors are auditable and reversible."

**"Why not just improve Fetch?"**
"Fetch is a lookup tool — it retrieves. T-Rep AI executes. Fetch still leaves the rep as the manual bridge between every downstream system. We're eliminating that role for the rep entirely."

**"The voice feature — how do you handle accuracy in a noisy store?"**
"Deepgram's Nova-2 model is built for real-world audio and handles background noise well. We also only act on final transcripts, not interim results, so a partial misread doesn't trigger anything. And if the mic picks up something wrong, the rep sees the intent badge and can override it before any action is taken."

**"What about data privacy / customer consent?"**
"The product operates entirely within T-Mobile's existing customer data infrastructure. No new data is collected — we're surfacing what already exists in the customer record. The LLM processes structured account data. For the audio layer, the conversation is streamed to Deepgram for transcription and is not stored — same model as any voice-to-text assistive tool used in enterprise settings today." *(Note: this is your answer for the CLO judge — acknowledge the concern, show you've thought about it.)*

---

## Pitch Deck Structure (6 Slides)

**Slide 1 — The Problem**
Three real data points from the retail interview. Rep is juggling Tapestry, MagentaWelcome, T-Life, DASH. Average trade-in transaction: 22+ minutes. Fetch gives outdated info. Rep is heads-down in systems instead of facing the customer.

**Slide 2 — The Insight**
One sentence: "The rep is the manual bridge between every system. We made AI the bridge instead."
Visual: before/after diagram. Before: Rep ↔ 4 separate systems. After: Rep → T-Rep AI → All systems.

**Slide 3 — Live Demo**
Just the words "Live Demo" on screen. The product speaks for itself.

**Slide 4 — How It Works**
Architecture: Deepgram (live audio) + Customer Data Layer (mocked Tapestry/DASH) → LLM Orchestration (Claude) → Execution Agent → Rep UI. Four clean boxes. No jargon.

**Slide 5 — Business Impact**
The CFO slide. Transaction time: 22 min → 8 min. Math: 560 minutes freed per rep per day. Equivalent capacity: 9+ more interactions. Projected across T-Mobile's ~7,000-store footprint. Show the formula, give a range.

**Slide 6 — What's Next**
1. Real Tapestry/DASH API integration via internal platform team
2. Rep feedback loop for AI brief and intent accuracy improvement
3. 10-store pilot, 60-day measurement period

---

## Prompt Templates

### Brief Prompt (`brief_prompt.py`)
```
You are a T-Mobile rep assistant. Given a customer account object, produce a structured brief with:
- plan_summary: one sentence describing their current plan and monthly cost
- upgrade_status: one sentence on upgrade eligibility and trade-in value
- bill_summary: plain-language breakdown of what they pay and why
- open_issues: list of open tickets with one-line status each
- pah_status: whether the person present is authorized to make changes

Return valid JSON matching the BriefResponse schema. Be concise — this is read at a glance.
Customer data: {customer}
```

### Bill Delta Prompt (`bill_delta_prompt.py`)
```
You are a T-Mobile billing assistant. Given a customer's current plan and a proposed change,
explain the bill impact in one plain-language sentence a rep can read directly to a customer.
Be specific with dollar amounts. Example: "Upgrading to Magenta MAX adds $22/month. Your new total would be $107."

Current plan: {current_plan}
Proposed change: {proposed_change}
Delta: ${delta_dollars} {direction}
```

### Intent Detection Prompt (`intent_prompt.py`)
```
You are a T-Mobile rep assistant listening to a live customer conversation.

Given this transcript chunk, identify if the customer is asking about:
- A specific plan (name it)
- A device upgrade (name the device if mentioned)
- Adding or removing a line
- A trade-in
- A promo or discount
- A billing question

Return JSON:
{
  "topic": "plan_upgrade" | "device_inquiry" | "add_line" | "trade_in" | "promo" | "billing" | "none",
  "details": { ... extracted specifics ... },
  "action": "fetch_plan" | "fetch_device" | "calculate_delta" | "fetch_promo" | "none",
  "confidence": 0.0–1.0
}

Only return a topic if confidence > 0.7. Otherwise return "none".
Transcript: {transcript}
```

---

## Pre-Hackathon Night Checklist

Do all of this the night before so Hour 1 is not eaten by setup.

- [ ] Create GitLab repo, invite all teammates, push an empty README.md
- [ ] Generate Anthropic API key, add credits, share in private DM (not in the repo)
- [ ] Generate Deepgram API key (free tier covers demo usage), share the same way
- [ ] Everyone clones the repo and confirms Git is working
- [ ] Confirm presentation laptop can run `npm run dev` (frontend) and `uvicorn main:app` (backend) simultaneously — test this the night before
- [ ] Confirm browser mic access works on the presentation laptop (check Chrome permissions)
- [ ] Person 1 confirms `pip install fastapi uvicorn anthropic deepgram-sdk pydantic python-dotenv` runs clean
- [ ] Person 4 confirms `npm create vite@latest` and Deepgram browser SDK install without errors
- [ ] Person 5 has a blank Figma file and blank deck with T-Mobile color palette loaded
- [ ] Team agrees on a communication channel (iMessage, Slack, or Discord)
- [ ] Save a Deepgram test snippet and confirm it transcribes audio before the morning
- [ ] Everyone reads this document

---

## Architecture Summary

```
[ Browser Mic ]
      ↓
[ Deepgram WebSocket ]  ←— useDeepgram.js (Person 4)
      ↓
[ Live Transcript ]
      ↓
[ /intent endpoint ]  ←— intent_agent.py + intent_prompt.py (Person 1)
      ↓
[ Mock Catalog Query ]  ←— plans.json / promos.json / devices.json (Person 2)
      ↓
[ Dashboard Auto-Update ]  ←— BillExplorer / CustomerBrief (Person 4/5)

[ Customer Phone # Input ]
      ↓
[ /customer/{id} ]  ←— mock_customers.json (Person 2)
      ↓
[ /brief ]  ←— brief_agent.py + Claude (Person 1)
      ↓
[ CustomerBrief Card ]

[ Rep Confirms Transaction ]
      ↓
[ /execute WebSocket ]  ←— execution_service.py (Person 3)
      ↓
[ StepTracker live updates ] → [ FinalBillCard ]
```

The idea is grounded in real pain. The architecture is clean. The Deepgram layer is the differentiator that makes it feel genuinely live. The demo moment — watching steps execute while a conversation plays out — is what wins the room.
