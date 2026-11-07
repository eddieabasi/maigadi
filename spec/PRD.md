# PRD: maigadi v1

> **maigadi:** an on-prem AI watchman for your existing CCTV. Ask what happened in plain language, and get shift summaries and verified alerts on WhatsApp. Built on NVIDIA VSS. Footage never leaves the site.

Status: draft v0.1 (2026-11-07). Conventions: **ASSUMPTION** marks anything not verified. "VSS" means NVIDIA VSS v3.3.0 (see [VSS_BASELINE.md](VSS_BASELINE.md)).

## Decisions at a glance

| # | Decision |
|---|---|
| P1 | **Beachhead: warehouses and distribution yards in Nigeria.** Targets are FMCG distributors, 3PLs, manufacturer depots and importers' warehouses, starting in Lagos and Ogun. |
| P2 | **The buyer is the owner or MD; the product lives in WhatsApp.** The web dashboard is for installers and power users only. |
| P3 | **v1 does three jobs.** (1) Answer "what happened?" questions. (2) Send shift summaries. (3) Send VLM-verified after-hours alerts. Nothing else. |
| P4 | **No identification of people in v1.** No face recognition, no plate recognition, no audio, no individual productivity scoring. |
| P5 | **Commercial model is HaaS.** Setup fee plus a monthly subscription on a 24-month term, priced in NGN and indexed to USD. Chains of 3 or more sites may buy outright. |
| P6 | **One SKU: one Thor-class box per site, up to 16 cameras.** Larger sites are out of scope for v1. |

---

## 1. Problem

- Most businesses with CCTV **record everything and watch nothing**. Footage gets scrubbed for hours *after* a loss, if at all.
- Cameras go **silently offline** for days (power cuts, DVR faults, cut cables), and nobody notices until they need the footage.
- Owners are often **absent or run several sites**. They manage by WhatsApp and phone calls, and have no trustworthy, low-effort view of what happened overnight.
- Cloud video analytics needs **upload bandwidth** that many sites lack or can't afford (metered 4G), and sends footage off-site, which privacy-sensitive owners refuse.
- In Nigeria, **unreliable grid power and intermittent internet** break most "smart camera" products, which assume always-on power and connectivity.

## 2. Beachhead: warehouses and distribution (Nigeria)

### Why this vertical

- **Concentrated, recurring pain.** Stock pilferage (often staff and drivers colluding), loading disputes, truck detention arguments, after-hours intrusion, and guards absent or asleep. **ASSUMPTION:** validated in 15+ discovery interviews before M3.
- **The example jobs fit exactly.** "When did the delivery truck leave?", "was anyone in the stockroom after closing?" and "summarize the night shift at the loading bay" are daily warehouse questions.
- **Budget exists.** These sites already pay for 2–6 guards and a CCTV contractor. **ASSUMPTION:** a Lagos night guard costs ₦100–200k a month.
- **Standard layouts mean fast installs.** Zones repeat across sites: gate, yard, loading bay, stockroom, office, perimeter. One rule pack covers most of them.
- **Existing DVRs and NVRs** (mostly Hikvision/Dahua-class) expose per-channel RTSP streams. **ASSUMPTION:** confirmed by the site-survey tool at each pilot.
- **Transfers best abroad.** See §2.3.

### 2.1 Ideal customer profile (v1)

| Attribute | ICP |
|---|---|
| Business | FMCG distributor or sub-distributor, 3PL / contract logistics, manufacturer regional depot, importer / bonded warehouse, pharma distributor |
| Site | 1,000–10,000 m²; **8–16 cameras**; existing DVR/NVR; 1–3 shifts; generator + inverter |
| Connectivity | Fibre/fixed wireless, or a 4G router. Metered data is acceptable |
| Decision-maker | Owner/MD or operations director. Uses WhatsApp daily |
| Geography (v1) | Lagos and Ogun corridor (Apapa, Ikeja, Agbara, Ikorodu, Lekki), then Abuja, Kano, Onitsha, Port Harcourt |
| Disqualifiers | No usable DVR/RTSP; more than 16 critical cameras; wants face or plate recognition; no secure indoor spot for the box |

### 2.2 Personas

| Persona | Channel | Wants |
|---|---|---|
| **Owner / MD** (buyer) | WhatsApp | "Tell me only what matters, prove it, don't waste my time." |
| **Site / operations manager** | WhatsApp + occasional LAN dashboard | Shift handover, truck log, suppress alerts when working late |
| **Installer** (maigadi-certified partner technician) | LAN dashboard + installer CLI | Install in under 4 hours, repeatably, without calling HQ |
| **maigadi Ops** (internal) | Fleet console | Know a box is unhealthy before the customer does |

### 2.3 Which verticals transfer best

| Vertical | Transfer to other markets | Why |
|---|---|---|
| **Warehouses / logistics (beachhead)** | **High: EU, UK, US, MEA, LatAm, India** | Universal workflows (bays, gates, after-hours). Security purpose rarely targets individuals, so it fits privacy law. B2B buyers |
| Fuel stations | High in emerging markets (Ghana, Kenya, India, Indonesia, LatAm); low in EU/US | Same box and rule engine. Mature markets already have forecourt systems. **Recommended next vertical in Nigeria (v1.5)** |
| Factories | Medium–high | Safety and SOP use cases transfer, but they need more cameras and bigger hardware, and slide into employee-monitoring rules |
| Gated residential | Medium (South Africa, LatAm, India) | Strong pull to plate and face recognition means high regulatory friction. Price-sensitive buyers |
| Construction | Medium | Worst power and connectivity. Temporary sites mean high churn |
| Retail | Low | Demand centres on face recognition and shoplifter ID (BIPA-type risk). Thin margins |

## 3. Jobs to be done

1. **When something might have happened**, I want to ask in plain words and get a *proven* answer (time, camera, evidence) in under a minute, so I don't have to scrub footage or call anyone.
2. **When a shift ends**, I want a short, trustworthy summary of what happened and what didn't, so I can manage the site without being there.
3. **When something bad happens after hours**, I want a verified alert fast enough to act, without false alarms that teach me to ignore it.
4. **When my cameras stop working**, I want to know the same day, so the footage exists when I need it.
5. **When I need evidence**, I want a short clip on my phone, without my footage living on someone else's cloud.

## 4. User journeys

### 4.1 Owner on WhatsApp

**Onboarding (day 0)**

1. The installer registers the owner's number in the LAN dashboard. The cloud sends a WhatsApp utility template: *"maigadi is set up at {Site}. Reply YES to receive alerts and summaries."*
2. The owner replies YES. maigadi records opt-in, sends a 3-line privacy notice with a link, and explains what it can do with 3 example questions.
3. The first night-shift summary arrives the next morning.

**Asking (daily)**

| Owner types | maigadi replies (≤ 30 s target) |
|---|---|
| "when did the delivery truck leave yesterday?" | "A truck left the loading bay at **4:52 PM** yesterday and went out through Gate 1 at **4:55 PM** (Bay Cam 2, Gate Cam 1). It arrived at 1:18 PM, so it was on site 3 h 34 m. [E-8812] Reply CLIP E-8812 for a 20-second clip." |
| "was anyone in the stockroom after closing?" | "Yes, once. A person entered the stockroom at **9:41 PM** and left at **9:58 PM** (Stockroom Cam). The VLM check says one person was carrying cartons toward the side door. [E-8840] The stockroom camera was online all night. Reply CLIP E-8840 to see it." |
| "summarize the night shift at the loading bay" | Bay-only summary: trucks in and out with times, after-hours activity, verified alerts, camera coverage gaps. |
| "is the back gate camera working?" | "Back Gate Cam has been **offline since 2:14 AM** (no video from the DVR channel). The other 11 cameras are fine." |

Rules the agent always follows:

- It cites evidence IDs.
- It states coverage ("camera online all night" or "offline 01:00–03:10, can't confirm").
- It never guesses when there is no evidence.

**Alert (night)**

1. A person is detected in the yard at 02:14 while the site is armed. The VLM confirms: "one person climbing over the perimeter wall near the generator house."
2. WhatsApp utility template: *"⚠️ {Site}: Person in Yard (after hours) at 2:14 AM. Verified. [E-9001] Reply CLIP E-9001, MUTE 1H, or FALSE."*
3. The owner replies CLIP E-9001. The box cuts a 20 s, 480p, watermarked clip. The clip is sent and the transfer is logged. FALSE is recorded as feedback for evaluation.

**Commands** (deterministic, not the LLM): `CLIP <id>`, `MUTE <duration>`, `FALSE <id>`, `STATUS`, `STOP`, `HELP`.

### 4.2 Site manager

- Receives the shift summary at shift end (default Day 07:00–19:00, Night 19:00–07:00, configurable).
- Types `LATE until 22:00` to suppress after-hours alerts in chosen zones tonight. The owner is told, and it is audited.
- Asks for the day's truck log: "list trucks at the bay today". maigadi returns a table of arrivals, departures and dwell times.
- Uses the LAN dashboard (on site) to browse events, export a clip for a police report, and check camera health.

### 4.3 Installer

1. **Survey (before the sale closes):** run `maigadi-survey` on a laptop on the site LAN. It discovers DVRs/NVRs, checks RTSP for each channel, measures sub-stream resolution, FPS and bitrate, checks the uplink, and flags old DVR firmware. Output is a pass/fail report plus a camera list.
2. **Install (≤ 4 h target):**
   1. Mount the box and Power Kit in a lockable ventilated enclosure.
   2. Set up the managed switch: camera/DVR VLAN with no internet, plus an uplink.
   3. Set DVR sub-streams to 720p, 10 FPS, ≤ 1 Mbps.
   4. Create a read-only DVR user.
3. **Commission:**
   1. Box claims its identity from the cloud.
   2. Cameras are added from the survey list.
   3. Draw zones on snapshots using the warehouse template (Gate, Yard, Bay, Stockroom, Office, Perimeter).
   4. Set the schedule (armed hours, shifts).
   5. Choose the region policy pack. It is auto-selected from the country.
4. **Walk test:** the dashboard is in test mode. The installer walks each armed zone and sees a live confirmation per zone. Results are saved.
5. **Signage:** install the regional signage pack, photograph each sign, and upload the photos. **Commissioning can't complete without them.**
6. **Handover:** register the owner's WhatsApp number and train the manager (15 minutes).

## 5. v1 scope

**In**

- Ingest up to **16 cameras** per site from an existing DVR/NVR (RTSP) or ONVIF IP cameras.
- Always-on detection and tracking of people and vehicles (car, truck, motorbike), with zone and line events.
- **Rule pack "Warehouse v1":**
  - After-hours person in an armed zone.
  - After-hours vehicle movement.
  - Truck arrival and departure at the bay or gate (logged, not alerted).
  - Bay dwell over N minutes (optional alert).
  - Camera offline or tampered (view blocked, or a sudden scene change). **ASSUMPTION:** tamper detection via frame-diff and brightness heuristics.
- **VLM verification** of every alert before it is sent.
- **Visual memory:** a VLM caption for each significant event, plus one 10 s periodic caption per camera every 10 minutes.
- **Natural-language Q&A** over events, captions and coverage, plus on-demand VLM look-ups of specific clips.
- **Shift summaries**, per site and per zone group.
- **WhatsApp channel** (Cloud API), plus a channel adapter interface. SMS is the first add-on (v1.1).
- **Clip on request:** ≤ 20 s, 480p, watermarked, owner/manager roles only, audited.
- **LAN dashboard:** setup, zones, events, clip export, health.
- **Two LLM modes:** **Hybrid** (cloud LLM sees text only; the default) and **Sovereign** (all on-box; paid option).
- **Fleet:** health telemetry, config sync, signed OTA updates with rollback.
- **Region policy packs:** Nigeria (launch), plus EU/UK and US packs that ship disabled until legal review.

## 6. Explicit non-goals (v1)

- Face recognition, person re-identification across days, plate recognition, gait or emotion analysis.
- Audio capture or analytics. Audio is disabled on ingest.
- Replacing the DVR/NVR or acting as a VMS. The DVR stays the long-term record.
- Cloud video storage, live view on WhatsApp, or remote streaming.
- Life-safety guarantees (fire, smoke, medical). Not offered or marketed in v1.
- Individual employee productivity scoring or attendance tracking.
- PTZ control, multi-camera 3D tracking, sites over 16 cameras, multi-box sites.
- A native mobile app.
- Self-install by customers (certified installers only).

## 7. Success metrics

| Area | Metric | v1 target (paid GA) |
|---|---|---|
| Value | Owner questions per active site per week (from week 4) | ≥ 3 |
| Value | Sites opening ≥ 4 of 7 shift summaries per week | ≥ 70% |
| Alert quality | Precision of delivered alerts (true events / alerts) | ≥ 90% |
| Alert quality | False alerts per site per night | ≤ 0.5 median, ≤ 2 P90 |
| Alert quality | Recall on staged after-hours intrusion tests | ≥ 95% |
| Answer quality | Correct answers on the gold question set (see EVAL_PLAN) | ≥ 85% |
| Answer quality | Summaries that omit a verified alert | 0 |
| Latency | Event → WhatsApp delivered, P90, when online | ≤ 60 s |
| Latency | Question → answer, P90 (Hybrid / Sovereign) | ≤ 30 s / ≤ 60 s |
| Reliability | Alerts lost (never delivered) | 0. Late delivery is allowed and flagged |
| Reliability | Box availability, excluding power outages beyond the Power Kit's runtime | ≥ 99% |
| Ops | Median install time | ≤ 4 h |
| Ops | Steady-state data use per site per month (excluding clips and OTA) | ≤ 300 MB |
| Commercial | Pilot → paid conversion | ≥ 60% |
| Commercial | Logo churn | < 2% per month |
| Commercial | Hardware payback per HaaS site | ≤ 18 months |

## 8. Pricing model

### 8.1 Decision

**HaaS by default in Nigeria.** The box and Power Kit remain maigadi property. The customer pays:

- A one-time **setup and commissioning** fee.
- A **monthly subscription** on a **24-month minimum term**. Early termination pays the remaining hardware amortization.

Prices are set in **NGN, indexed to USD**: reviewed quarterly against the CBN rate, with a ±10% collar per quarter. **Outright purchase** is offered to chains with 3 or more sites, and to customers whose procurement requires it.

### 8.2 Nigeria price list

Prices assume ₦1,550 per $1. **ASSUMPTION:** the FX rate; verify at launch.

| Item | NGN | ≈ USD | Notes |
|---|---|---|---|
| Setup and commissioning (HaaS) | ₦900,000 one-time | $580 | Survey, install, Power Kit fitting, VLAN switch, zones, signage, training |
| **Watchman 8** (≤ 8 cameras) | ₦550,000 / month | $355 | 24-month term |
| **Watchman 16** (≤ 16 cameras) | ₦700,000 / month | $450 | 24-month term |
| Sovereign mode add-on (no cloud LLM) | +₦80,000 / month | $50 | Fewer cameras per box. See HARDWARE |
| Outright hardware (box + Power Kit + switch) | cost + 15% (≈ ₦11.3M) | ≈ $7,300 | Chains ≥ 3 sites |
| Outright software subscription | ₦310,000 / month (16 cams) | $200 | 12-month term |
| Paid pilot (60 days) | ₦250,000 / month, setup at cost | $160 | Converts to a 24-month HaaS term |

### 8.3 Unit economics (Watchman 16, HaaS)

All inputs are **ASSUMPTIONS** until the first five sites are installed.

| Line | Value |
|---|---|
| Capex per site | ~$6,350: Thor industrial box $5,000 landed, 4 TB SSD $300, Power Kit $700, switch + cabling $200, lockable enclosure $150 |
| Monthly cost to serve, Hybrid on `claude-opus-5-5` | ~$118 (detail below) |
| Monthly contribution | $450 − $118 = **$332** |
| Payback | ($6,350 − $580 setup) / $332 ≈ **17 months** |

Monthly cost-to-serve breakdown:

- Cloud LLM: ~$38 at 10 questions a day; range $23–68. See [ARCHITECTURE.md §6.4](ARCHITECTURE.md#64-model-choice-and-cost) for the per-model maths. Sonnet 5.5 ≈ $19, Haiku 5.5 ≈ $1.
- Cloud infrastructure share: $8.
- WhatsApp: ≤ $5.
- Backup 4G data: $10.
- Support and field visits: $40.
- Replacement reserve: $15.

The LLM model tier is the biggest variable cost lever. It is an open question for you (see RISKS_AND_OPEN_QUESTIONS).

### 8.4 How pricing adapts by region

Use one formula everywhere and publish a price book per region:

```
monthly_price = max( cost_floor × (1 + target_margin),  value_anchor × capture_rate )
cost_floor    = hardware_amortization(term) + cost_to_serve(region)
value_anchor  = local monthly cost of one night guard (or one hour/day of a security operator)
capture_rate  = 0.5 – 1.5, set from pilot willingness-to-pay
```

| Region | Default model | Indicative (Watchman 16) | Notes |
|---|---|---|---|
| Nigeria / West Africa | HaaS, 24-month | ₦700k/mo | FX-indexed. Power Kit included |
| East Africa, South Africa | HaaS | Local-currency equivalent | Same SKU |
| EU / UK | Outright or HaaS | €690/mo HaaS, or ~€8.5k + €240/mo | DPIA pack included. Power Kit optional |
| US | Outright or HaaS | $790/mo HaaS | State-law pack. Power Kit optional |
| India / SE Asia | HaaS, lean tier (v2) | Lower | Needs the Orin "lean" SKU (see HARDWARE) |

All indicative prices are **ASSUMPTIONS** to be tested in each region's pilots.
