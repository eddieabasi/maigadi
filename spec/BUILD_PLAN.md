# Build Plan

Status: draft v0.1 (2026-11-07). The build is done with **Claude Code**. Each task below is sized for **one Claude Code session**: one clear goal, tests included, ending in a commit. Session size is S (≈ 1 h), M (≈ 2–3 h) or L (≈ half a day; split it if it runs over).

## Decisions at a glance

| # | Decision |
|---|---|
| B1 | **Monorepo, Python 3.13, `uv` workspace.** VSS agent packages need Python ≥ 3.13; we match, so VSS libraries can be imported if ever needed |
| B2 | **VSS is consumed as pinned containers plus vendored deploy configs**, not as a fork. `third_party/vss` is a git submodule pinned to tag `v3.3.0`, used for configs, protobufs and skills |
| B3 | **Dev loop:** one Jetson AGX Thor dev kit (lab box) plus x86 laptops with fakes. Recorded streams are replayed via VSS NVStreamer. Every service has a fake for its upstream |
| B4 | **Milestones are gated by measurements, not dates.** M0 is a hard feasibility gate on capacity |
| B5 | **Cloud stack:** FastAPI services on AWS (IoT Core, ECS Fargate, RDS Postgres, S3), defined in OpenTofu. Dev uses Mosquitto + docker-compose locally |

## Milestones

| Milestone | Goal | Exit criteria | Indicative duration |
|---|---|---|---|
| **M0 Feasibility** | Prove the box can do the job | 16 cams @ 5 FPS on Thor, alert verification P90 ≤ 20 s, offline boot works; or a fallback camera cap is decided | 3 weeks |
| **M1 Demo** | End-to-end on recorded footage, over WhatsApp | The 3 example questions answered correctly; verified alert on phone ≤ 60 s; shift summary delivered | 4 weeks |
| **M2 Site alpha** | One friendly warehouse, live 24/7 | 14 consecutive days; alert precision ≥ 0.85; zero lost alerts; owner asks ≥ 3×/week | 4 weeks |
| **M3 Pilot** | 3–5 paid-pilot sites, hardened | RELIABILITY §7 tests pass; EVAL targets met on ≥ 3 sites; ≥ 60% intent to convert | 8 weeks |
| **M4 Paid v1** | GA in Nigeria | 10 paying sites; billing live; legal pack approved; external pen test closed | 6 weeks |

---

## M0: Feasibility

| ID | Task | Size | Depends | Acceptance |
|---|---|---|---|---|
| T0.1 | Repo skeleton: `uv` workspace, package layout (below), ruff + mypy + pytest, pre-commit, GitHub Actions CI, `third_party/vss` submodule at `v3.3.0` | S | – | CI green on an empty package; `uv run pytest` works |
| T0.2 | Thor bootstrap script (`edge/deploy/bootstrap.sh`, idempotent): verify JetPack 7.2 / driver 595.78; pin Docker 28.x; NVIDIA CTK; VSS sysctls; page-cache cleaner as a **systemd unit**; `nvpmodel -m 0` + `jetson_clocks` unit | M | T0.1 | Fresh dev kit to VSS-ready in one run; a re-run is a no-op |
| T0.3 | Bring up the VSS 3.3.0 **alerts profile** on Thor with the `vss-build-vision-ai` skill. Export the resolved compose to `edge/deploy/vss/`, pinned by **digest**, with local model weights. Prove it works offline: unplug WAN, reboot, confirm it runs with `--pull never` | M | T0.2 | Offline cold boot reaches healthy; resolved compose committed |
| T0.4a | CV capacity benchmark: NVStreamer replays N = 8/12/16 cameras at 720p 10 FPS. Tune RT-CV `interval` for 5 FPS effective. Record FPS per stream, Kafka lag, unified memory, temperature | M | T0.3 | Report `spec/benchmarks/m0-cv.md` with a go/no-go per N |
| T0.4b | VLM capacity benchmark: Alert Bridge verification throughput at 1/5/10 concurrent alerts with CR3 Nano BF16, while periodic captioning runs (96/h) and CV runs at the chosen N. Repeat with the Sovereign LLM loaded | M | T0.4a | Report `m0-vlm.md`; camera caps for Hybrid and Sovereign fixed |
| T0.5 | `maigadi-survey` CLI: ONVIF discovery; vendor RTSP templates (Hikvision, Dahua, Uniview, generic); `ffprobe` stream params; bitrate sampling; DVR vendor P2P detection (passive DNS/connection check); default-credential warning; JSON + HTML report | M | T0.1 | Passes against 2 real DVRs (or a DVR plus a simulator); report renders |
| T0.6 | MCP spike: connect an `mcp` 2.x client to VSS VA-MCP (`get_incidents`). Document compatibility | S | T0.3 | Tool list + one call succeed, or a documented pin |

## M1: Demo

| ID | Task | Size | Depends | Acceptance |
|---|---|---|---|---|
| T1.1 | `shared/schemas`: pydantic v2 models for Event, Caption, Coverage, SystemState, OutboundMessage, InboundEvent, SiteConfig, RulePack, PolicyPack; JSON Schema export | S | T0.1 | Round-trip tests; schema files generated |
| T1.2 | On-box Postgres 16 + pgvector service; Alembic migrations for every table in ARCHITECTURE §3.5; FTS + HNSW indexes | M | T1.1 | Migrations up and down; seed fixtures load |
| T1.3 | Indexer: Kafka consumers (Behavior Analytics events/incidents, `mdx-vlm-incidents`) → Postgres; protobuf decode via `third_party/vss/libs/nvschema`; idempotent upserts; track aggregation | M | T1.2, T0.3 | Replaying a recorded topic twice yields identical rows |
| T1.4 | Coverage monitor: VIOS stream status + per-camera frame-rate watchdog → `coverage` intervals | M | T1.2 | Unplug-camera test produces a correct interval |
| T1.5 | Rules gate: armed schedule, holidays, `LATE` override, cooldown, dwell, nightly budget; Alert Bridge HTTP client; `rule_packs/warehouse-v1.yaml` | M | T1.3 | Table-driven tests for schedule edge cases (midnight crossing, timezone) |
| T1.6 | Warehouse alert prompts (`alert_type_config.json`) seeded via `PUT /api/v1/verification/config/{alert_type}`; versioned with the rule pack | S | T1.5 | Seeding is idempotent; prompt versions visible |
| T1.7a | Visual-memory scheduler: periodic and event captions; structured caption prompt; writes `captions` | M | T1.2 | 16 cameras × 6/h sustained on the lab box |
| T1.7b | VLM budget arbiter (P0–P3 priority queue, shedding hooks) + CPU embeddings (MiniLM, 384-d) | M | T1.7a | Load test: P1 latency held under P3 flood |
| T1.8a | `site-mcp` read tools: `get_site_context`, `search_events`, `search_captions`, `get_event`, `count`, `get_coverage`, `list_alerts` (wraps VA-MCP); site scoping enforced server-side | L | T1.2 | Contract tests per tool with fixtures |
| T1.8b | `resolve_time_range` deterministic parser (site tz, shifts, "after closing", "last night" asked after midnight) + `ask_vlm` (≤ 60 s clip via VIOS, P1 budget) | M | T1.8a | Property tests for the parser; `ask_vlm` timeout honoured |
| T1.9 | Watchman agent: provider interface (`AnthropicProvider` via gateway, `OpenAICompatProvider`), MCP client, step/time/VLM budgets, egress filter, prompt contract, structured result `{answer, citations[], coverage_note, suggested_actions[]}` | L | T1.8b | Unit tests with mocked providers; egress filter rejects any non-text |
| T1.10 | Agent-only eval harness (fixtures) + 50 seed gold questions; compares model tiers on accuracy, latency and cost | M | T1.9 | Report table printed; CI job wired |
| T1.11 | Channel interface (`ChannelAdapter`, `OutboundMessage` rendering) + WhatsApp Cloud API adapter (signature verification, templates, free-form, media) + fake adapter | M | T1.1 | Contract tests; sandbox number works |
| T1.12 | Cloud relay MVP: webhook endpoint, static user/site map, deterministic command grammar (`CLIP`, `MUTE`, `FALSE`, `LATE`, `STATUS`, `STOP`, `HELP`), MQTT bridge (Mosquitto in dev) | L | T1.11 | E2E with the fake adapter: question in, answer out |
| T1.13 | `maigadi-node` v0: MQTT client (inbox/outbox), outbox table and delivery state machine, heartbeat | M | T1.2 | Kill the broker for 10 min: zero loss, correct order on reconnect |
| T1.14 | Notifier: alert and summary-notice rendering into `OutboundMessage`; recipients by role | S | T1.13 | Golden-file tests of rendered messages |
| T1.15 | Summarizer: SQL facts block + LLM narrative + validator (every verified alert id present) + template fallback | M | T1.9 | A missing-alert narrative is rejected; fallback renders |
| T1.16 | LLM gateway MVP (cloud): device auth (dev token), Anthropic Messages call, server-side egress re-check, per-site budget, usage metering | M | T1.9 | Budget exceeded → graceful agent message |
| T1.17 | Demo kit: staged warehouse recordings via NVStreamer; scripted demo runbook | S | all above | The demo runs in 10 minutes from a cold start |

## M2: Site alpha

| ID | Task | Size | Depends | Acceptance |
|---|---|---|---|---|
| T2.1a | LAN dashboard v0 (FastAPI + HTMX, behind Caddy TLS): local accounts + TOTP, event browser, clip export, health page | L | T1.2 | Auth required on every route; clip export audited |
| T2.1b | Zone and tripwire editor on snapshots → site config → Behavior Analytics dynamic config | M | T2.1a | Drawn zone produces ROI events on replay |
| T2.2 | Config sync: control-plane desired config → device shadow → box apply (BA, VIOS, rules, recipients) → reported state | M | T1.12 | Config change reaches the box within 1 min online; applied after an offline period |
| T2.3 | Camera onboarding via VIOS API using survey output; encrypted credential vault | M | T0.5 | 16 cameras added in under 5 min; no credentials in logs |
| T2.4 | Power module: BMS reader (Modbus RTU/USB), state machine, load-shedding hooks, ordered shutdown, dying gasp | L | T1.13 | Pull-the-plug rig: 20 cycles clean |
| T2.5 | Boot orchestration: systemd units, health-gated start order, warm-up policy (unverified P0), safe mode | M | T2.4 | Boot-to-CV-alerts ≤ 5 min measured |
| T2.6 | Pipeline liveness + remediation ladder | M | T2.5 | Fault injection walks the ladder correctly |
| T2.7 | Canary self-test via NVStreamer `cam-canary` | M | T2.6 | Detects a broken VLM within one cycle |
| T2.8 | `CLIP` command path: cut ≤ 20 s, 480p, watermark, transient S3, WhatsApp media, delete ≤ 24 h, PIN step-up, audit | M | T1.12 | Clip arrives; S3 object gone after delivery; audit row present |
| T2.9 | Users and roles in the control plane: opt-in template flow, PIN (argon2id), role checks in relay and `site-mcp` | M | T1.12 | Role matrix tests from SECURITY §A3 |
| T2.10 | Telemetry: metrics exporter, batched upload, Grafana fleet dashboards v0 | M | T1.13 | Dashboard shows the lab box and alpha site |
| T2.11 | Installer walk-test mode | S | T2.1b | Each armed zone shows a live confirmation |
| T2.12 | Commissioning checklist + signage photo gate + `ng-ndpa` policy-pack enforcement (retention jobs, feature flags) | M | T2.2 | Commissioning blocked without signage; retention jobs delete on schedule |

## M3: Pilot

| ID | Task | Size | Depends | Acceptance |
|---|---|---|---|---|
| T3.1 | maigadi OS golden-image pipeline + staging-bench burn-in script (TensorRT engines built on device) | L | T0.2 | Image flashes and passes burn-in unattended |
| T3.2 | Device identity: on-device keygen, enrollment at staging, AWS IoT Core provisioning, 90-day rotation, mTLS on MQTT and gateway | M | T3.1 | Revoked cert is locked out within 5 min |
| T3.3a | Release manifest schema + cosign signing in CI + SBOM attach | M | T0.1 | Unsigned or tampered manifest is rejected by the box |
| T3.3b | Box updater: windowed resumable download, verify, preflight, apply, health gate (canary + agent smoke), automatic rollback | L | T3.3a, T2.7 | Broken-image update rolls back ≤ 15 min |
| T3.3c | Ring controller in the control plane + auto-halt rules | M | T3.3b | Simulated regression halts the rollout |
| T3.4 | Network hardening: nftables allowlist, Docker network isolation, LUKS + key-sealing decision implemented | M | T3.1 | External scan of the box shows only 443 on the management VLAN |
| T3.5 | Audit log: hash chain, segment shipping, Object Lock bucket, owner export | M | T1.2 | Tampering with a row breaks chain verification |
| T3.6 | CVE pipeline: Syft SBOM, Grype + Trivy, `pip-audit`, VSS digest tracker report | S | T3.3a | CI fails on a critical CVE in maigadi images |
| T3.7 | Fleet: offline classification, ops alert rules, owner "site dark" messages, monthly reliability report | M | T2.10 | Each classification path tested with synthetic heartbeats |
| T3.8 | Support break-glass: `ALLOW SUPPORT 2H` → ephemeral Tailscale key, ACL tags, session recording, auto-expire | M | T2.9 | Access ends at expiry; audit complete |
| T3.9 | Sovereign mode profile (Nemotron 3.5 Lightning local) + provider switch + capacity re-test | M | T0.4b, T1.9 | Gold set accuracy within 5 pts of Hybrid, or the gap documented |
| T3.10 | Eval mode on box + CVAT/Label Studio deployment; build Corpus A and B; first stratified report | L | T2.1a | EVAL_PLAN §1 metrics reported per stratum |
| T3.11 | Nightly replay E2E harness + OpenTelemetry latency spans across box and cloud | M | T3.10 | P50/P90/P99 report generated nightly |
| T3.12 | Chaos suite: smart-relay power-pull rig, network flapper, disk filler, clock jumper | M | T2.4 | RELIABILITY §7 table automated |
| T3.13 | Rate limits (relay, agent), prompt-injection test set (scene text + user), output filter | S | T1.12 | Injection set: 0 unsafe actions |
| T3.14 | Command aliases (Pidgin), localisation framework for templates and copy | S | T1.12 | Alias tests; template per locale |

## M4: Paid v1

| ID | Task | Size | Depends | Acceptance |
|---|---|---|---|---|
| T4.1 | Billing: subscriptions in NGN (local payment provider, e.g. Paystack, **ASSUMPTION**), invoices, FX index job, dunning | M | T2.9 | Test-mode subscription lifecycle passes |
| T4.2 | Regional stack in OpenTofu; backups; disaster-recovery runbook; restore drill | L | – | Stack recreated from zero in a fresh account |
| T4.3 | SMS fallback adapter (v1.1 stretch), e.g. Africa's Talking or Termii (**ASSUMPTION**) | S | T1.11 | P0 fallback after 5 min in a test |
| T4.4 | DSAR export with blur of other people | M | T2.1a | Export blurs all non-requester persons in the test clips |
| T4.5 | Installer program: certification checklist, survey/commission UX polish, field guide | M | T2.12 | A new installer completes a site in ≤ 4 h |
| T4.6 | Legal integration: DPA, terms, notices, policy pack `legal_review: approved` gate | S | ⚖️ | GA blocked until approved |
| T4.7 | GA readiness: internal `/security-review`, external pen test, incident-response tabletop | M | all | No open high or critical findings |

---

## Proposed repo structure

```
maigadi/
├── README.md
├── CLAUDE.md
├── pyproject.toml              # uv workspace root
├── spec/                       # this spec (source of truth for intent)
├── shared/
│   ├── schemas/                # pydantic models + generated JSON Schema
│   ├── policy_packs/           # ng-ndpa, eu-gdpr, uk-gdpr, us-* (YAML, versioned)
│   └── rule_packs/             # warehouse-v1 (zones, events → alert types, prompts)
├── edge/                       # runs on the box
│   ├── node/                   # maigadi-node: MQTT, outbox, power, watchdogs, OTA, config sync
│   ├── indexer/                # Kafka → Postgres
│   ├── rules_gate/
│   ├── visual_memory/          # caption scheduler + VLM arbiter + embeddings
│   ├── site_mcp/               # MCP server (read-only tools)
│   ├── agent/                  # watchman agent loop + providers + egress filter
│   ├── summarizer/
│   ├── notifier/
│   ├── dashboard/              # LAN dashboard (FastAPI + HTMX)
│   └── deploy/
│       ├── vss/                # resolved VSS 3.3.0 compose, pinned by digest
│       ├── compose.maigadi.yml # our overlay
│       ├── hw/AGX-THOR.env     # sizing (memory fractions, FPS, caps)
│       ├── vendors/            # DVR/NVR RTSP URL templates
│       ├── os/                 # maigadi OS image build, systemd units, nftables
│       └── bootstrap.sh
├── cloud/
│   ├── relay/                  # webhooks, command grammar, router
│   ├── channels/               # adapters: whatsapp/, sms/, telegram/, slack/, teams/, fake/
│   ├── control_plane/          # tenants, sites, users, config, releases, rings
│   ├── llm_gateway/
│   ├── fleet/                  # health ingestion, classification, ops alerting
│   └── infra/                  # OpenTofu modules (regional stack)
├── tools/
│   ├── survey/                 # maigadi-survey CLI
│   ├── eval/                   # agent-only harness, replay E2E, judges, reports
│   └── chaos/                  # power/network/disk/clock fault rigs
├── tests/                      # cross-package integration tests
└── third_party/
    └── vss/                    # git submodule @ v3.3.0 (configs, nvschema, skills)
```

## Reuse from VSS vs build ourselves

| Area | Reuse from VSS (v3.3.0) | Build ourselves |
|---|---|---|
| Ingest and recording | **VIOS** container, sensor/record/replay/storage APIs, ONVIF discovery, aging policy | Vendor RTSP templates, survey tool, credential vault, coverage monitor |
| Perception | **RT-CV** (RT-DETR + tracker), **Behavior Analytics** (ROI, tripwire, restricted-area incidents) | Rule packs, zone templates, schedule-aware rules gate |
| Verification | **Alerts MS / Alert Bridge**, runtime prompt config API, Kafka `mdx-vlm-incidents` | Warehouse prompts, gate-to-bridge client, unverified-alert policy |
| VLM | **RT-VLM** serving Cosmos3 Nano BF16 | VLM budget arbiter, periodic/event caption scheduler, structured caption prompts |
| Data access | **VA-MCP** (`get_incidents`, `get_incident`) | Postgres index, `site-mcp`, hybrid retrieval, coverage model |
| Agent | Reference only (`vss_agents` tools such as `video_understanding` request shapes) | Watchman agent, providers, egress filter, summarizer |
| Schemas | `libs/nvschema` protobufs; `tools/message-broker-consumers` as reference | maigadi canonical schemas |
| Test and eval | **NVStreamer** (RTSP from files), `vss-evaluate-caption-accuracy`, `rtvi-vlm-perf-testing`, `vss-benchmark-vlm-qa`, `spatialai-data-utils` evaluators | Gold sets, replay E2E harness, stratified reports |
| Deploy tooling | `vss-build-vision-ai` skill and `vss` CLI (dev-time only) | maigadi OS, offline compose, OTA, fleet |
| Not used | VSS Agent + UI, search profile (RT-Embed + Cosmos-Embed1), LVS, MV3DT/3D, NemoClaw/OpenClaw harnesses | – |

**Licensing check (M0, ⚖️):**

- The VSS repo is Apache-2.0, plus the NVIDIA Asset License for data.
- The VSS README states that an **NVIDIA AI Enterprise licence is required to host NIM locally**. This affects Sovereign mode, which uses the Lightning NIM.
- The licence terms for RT-VLM / Cosmos3 weights in commercial edge deployment must be confirmed. See RISKS.
