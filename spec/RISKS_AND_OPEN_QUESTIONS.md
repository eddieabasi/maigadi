# Risks and Open Questions

Status: draft v0.1 (2026-11-07). L = likelihood, I = impact (H/M/L). ⚖️ = needs legal input.

## Top 3 open questions (need your decision)

1. **NVIDIA licensing cost per box for commercial edge deployment.**
   - The VSS README says an **NVIDIA AI Enterprise licence is required to host NIM locally**. That hits Sovereign mode, which uses the Lightning NIM, and possibly other NIM use.
   - The commercial terms for the RT-VLM container and Cosmos3 weights on customer premises are unverified.
   - This could add hundreds to thousands of dollars per box per year and change the unit economics.
   - **Ask NVIDIA (Inception/partner channel) in M0.** Mitigation if expensive:
     - Hybrid stays the default.
     - Sovereign uses an open-weight LLM served by plain vLLM, not a NIM. The `Nemotron-Nano-9B-v2-FP8` path already uses `nvcr.io/nvidia/vllm`. Its licence still needs checking.
2. **Default cloud LLM tier.**
   - The spec defaults to `claude-opus-5-5`: ~$38 per site per month at 10 questions a day.
   - `claude-sonnet-5-5` is ~$19 and `claude-haiku-5-5` ~$1 at the same load (ARCHITECTURE §6.4).
   - Recommendation: run the M1 agent-only gold set across tiers, then choose. You may also want different tiers for Q&A and summaries.
3. **Go-to-market channel: our own installers, or partner with existing CCTV integrators?**
   - Integrators already own the customer relationship and the DVRs, and can sell and install at scale, but they take margin and vary in quality.
   - Our own team gives control but grows slowly.
   - Recommendation: our own team for M2–M3 to write the playbook, then certified integrator partners for M4+. The answer changes pricing, onboarding tooling (T4.5) and support design.

**Other open questions** (we proceed on the stated assumption until told otherwise):

| # | Question | Working assumption |
|---|---|---|
| Q4 | Industrial Thor carrier vendor, landed cost and lead time into Nigeria (duty, SONCAP certification **ASSUMPTION**) | $5,000 landed; shortlist 3 vendors in M0 |
| Q5 | Cloud region for Africa tenants | AWS `af-south-1` if IoT Core and the other needed services exist there; otherwise `eu-west-1` ⚖️ |
| Q6 | Is Tailscale acceptable to privacy-first pilot customers for break-glass support? | Yes for pilots; self-hosted Headscale at GA if not |
| Q7 | Local languages for WhatsApp templates and answers | English at v1; Pidgin, Hausa, Yoruba and Igbo in v1.1 |
| Q8 | Does the WhatsApp in-window pricing change from 2026-10-01 apply as third parties report? | Budget as if yes (≤ $5 per site per month) |
| Q9 | Payment provider and FX index clause acceptable to customers | NGN billing via a local provider; quarterly USD index with ±10% collar |
| Q10 | Pilot sites | 3 design-partner warehouses in Lagos/Ogun, 12–16 cameras each on existing DVR/NVR |

---

## Technical risks

| ID | Risk | L | I | Mitigation |
|---|---|---|---|---|
| T1 | Thor can't sustain 16 cameras with CV at 5 FPS plus VLM verification plus periodic captions | M | H | M0 hard gate (T0.4a/b). Fallbacks: 12-camera cap; RT-DETR EfficientViT; fewer periodic captions; NVFP4 VLM only if the stratified eval shows no hallucination regression (VSS warns that FP8/NVFP4 may hallucinate) |
| T2 | VLM verification is unreliable at night (IR mono, headlights, insects, rain), causing false alarms and lost trust | H | H | Stratified eval (EVAL_PLAN §2.2); hard-negative mining; persistence + dwell gating; per-alert-type prompts; weekly precision review; owner `FALSE` feedback loop; "unverified" alerts only for high-severity types |
| T3 | VSS breaking changes between minor releases (3.2 → 3.3 removed Redis from Alerts) | H | M | Pin by digest; consume VSS through thin adapters (indexer, gate client, VA-MCP wrapper); contract tests against VSS APIs; evaluate each VSS release within 30 days; never auto-upgrade |
| T4 | VSS edge layouts are "not yet measured" by NVIDIA (local LLM on Thor; Spark sizing) | M | M | Hybrid by default; measure everything in M0; Sovereign is a paid option with its own caps |
| T5 | Unified-memory OOM (shared CPU/GPU pool), especially under concurrent VLM load (known VSS issue) | M | H | Memory fractions ≤ 0.8 total; cache-cleaner systemd unit; VLM arbiter; resource guards; 7-day soak |
| T6 | Elasticsearch or Kafka corruption after an abrupt power loss | M | M | Power Kit + planned shutdown; Postgres is the source of truth; ES config re-seed job; Kafka flush settings |
| T7 | Old or weak DVRs: session limits, poor sub-streams, analog quality, vulnerable firmware | H | M | Survey tool disqualifies or flags sites; per-vendor templates; one session per camera; upsell DVR/camera refresh through partners |
| T8 | Prompt injection via scene text or user messages | M | H | Read-only tools; deterministic egress commands; untrusted-data fencing; output filter; injection test set in CI |
| T9 | OTA over metered links is impossible for heavy images (RT-CV ≈ 18 GB compressed) | H | M | Split app and heavy updates; heavy via installer USB or unmetered windows; app updates ≤ 400 MB |
| T10 | Wrong times in answers (clock drift, DVR clocks, "last night" after midnight, DST abroad) | M | H | Box is the time authority (NTP + RTC); deterministic time parser with property tests; tz database; coverage in every negative answer |
| T11 | Jetson supply and price volatility (NVIDIA raised Jetson prices by up to 101% in July 2026) | M | H | Price-adjustment clause in hardware terms; 2–3 carrier vendors; certify Spark as an alternate in v1.1; keep compose hardware-agnostic via `HARDWARE_PROFILE` |
| T12 | Heat and dust (harmattan) causing throttling or failure | M | M | Enclosure with filtered airflow; temperature telemetry; load shedding; 40 °C soak test; maintenance visit every 6 months (filter clean) |
| T13 | MCP 2.x client incompatibility with VA-MCP | L | L | Spike T0.6; pin if needed |
| T14 | Hidden data egress, e.g. a VSS container or library phoning home | L | H | Outbound allowlist on the host; egress monitoring during burn-in; no telemetry exporters enabled by default (Phoenix/OTel local only) |

## Commercial risks

| ID | Risk | L | I | Mitigation |
|---|---|---|---|---|
| C1 | ₦700k/month (≈ $450) is above willingness to pay for many Nigerian warehouses | M | H | Paid pilots test willingness to pay; Watchman 8 tier; monthly value report (incidents caught, cameras kept online); lean Orin SKU in v2; financing partners for outright purchase |
| C2 | NGN volatility erodes HaaS margins on USD-priced hardware | H | H | Quarterly USD index with collar; hedge or batch-buy hardware; 24-month minimum term with early-termination fee |
| C3 | Long enterprise sales cycles (large distributors, multinationals) | M | M | Target owner-operated distributors and 3PLs first; 60-day paid pilot → automatic conversion |
| C4 | Installer quality varies, causing bad zones, bad streams and bad first impressions | H | M | Survey tool; commissioning gates (walk test, signage, health); remote commissioning review by maigadi Ops before handover |
| C5 | WhatsApp pricing or policy changes, template rejections, number quality ratings or bans | M | H | Opt-in records; utility templates only; message budget; SMS fallback (v1.1); channel-agnostic core so moving channels is cheap |
| C6 | Competition: DVR vendors' built-in "smart" events (AcuSense/WizSense-class) and cheap cloud AI cameras | H | M | Differentiate on plain-language Q&A, verified alerts, summaries, coverage honesty and privacy; v2: ingest DVR vendor events as extra signals |
| C7 | Box theft or vandalism at site | M | M | Lockable anchored enclosure, tamper alert, LUKS, cert revocation; theft clause and insurance in HaaS terms |
| C8 | LLM, WhatsApp and support costs exceed plan | M | M | Per-site budgets in the gateway; model tiering (open question 2); self-serve `STATUS`; fleet monitoring reduces truck rolls |
| C9 | Customer blames maigadi for a missed incident | M | H | Terms: maigadi is an assistive tool, not a security guarantee or life-safety system ⚖️; coverage honesty in every answer; audit trail; recall metrics published to the customer |

## Regulatory risks

| ID | Risk | L | I | Mitigation |
|---|---|---|---|---|
| G1 | NDPA/GAID enforcement on CCTV use or on cross-border processing of text (LLM, AWS, Meta) | M | H | DPA with every customer; text-only egress; ZDR; Sovereign mode; regional `data_region`; legal opinion before GA ⚖️ |
| G2 | maigadi must register as a Data Controller/Processor of Major Importance, appoint a DPO, and file audits | H | M | Plan for it; appoint a DPO before GA; budget a DPCO audit ⚖️ |
| G3 | Employee-monitoring disputes (staff, unions) | M | M | Staff notice in commissioning; no per-person scoring; staff-presence rules opt-in and audited ⚖️ |
| G4 | EU AI Act: features that evaluate workers become Annex III high-risk (applies 2 Dec 2027) | M (EU only) | H | EU pack forbids staff-presence rules; classification opinion before any EU pilot ⚖️ |
| G5 | US biometric (BIPA/CUBI) and wiretap exposure | L | H | No biometrics and no audio, in code; state matrix before any US pilot ⚖️ |
| G6 | Import and standards for electronics and LiFePO4 batteries (dangerous-goods shipping, SONCAP **ASSUMPTION**) | M | M | Source batteries locally; customs broker; certification plan in M2 |
| G7 | Meta's processing and retention of clips sent over WhatsApp | M | M | Clips only on explicit request, short and low-res, watermarked; disclosed in privacy notice; legal review ⚖️ |
| G8 | Regulators or customers ask for face recognition "because competitors offer it" | H | M | Product principle: no identification in v1; revisit only with per-jurisdiction legal approval and an explicit opt-in architecture (v3+) |

## Operational risks

| ID | Risk | L | I | Mitigation |
|---|---|---|---|---|
| O1 | Solo-founder bus factor; knowledge in chat transcripts | H | H | Spec-first repo; CLAUDE.md conventions; runbooks in-repo; every Claude Code session ends with tests + commit |
| O2 | Field support across Lagos traffic | H | M | Remote-first diagnostics; spares pool (1 spare box per 10 sites); installer partners by zone |
| O3 | Release mistakes across the fleet | M | H | Rings + canary + automatic rollback (RELIABILITY §5) |
