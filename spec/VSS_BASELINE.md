# VSS Baseline: what we verified, what VSS gives us, what we build

**Verified against:** NVIDIA VSS **v3.3.0** (git tag `v3.3.0`, commit `44c5574`, tagged 2026-10-21) in
[github.com/NVIDIA-AI-Blueprints/video-search-and-summarization](https://github.com/NVIDIA-AI-Blueprints/video-search-and-summarization/tree/v3.3.0).
Verification date: 2026-11-07.

**Source access notes**

- `docs.nvidia.com` and `build.nvidia.com` were **not reachable** from the build environment (DNS blocked). The
  docs site is generated from the repo's `docs/` folder (Fern source), so docs claims below were verified
  against `docs/*.mdx` **at the `v3.3.0` tag**. The `develop` branch (2026-11-03) has newer numbers in places; we cite
  the tag unless noted.
- The DGX Spark playbook (`build.nvidia.com/spark/vss`) was verified via its source repo,
  [NVIDIA/dgx-spark-playbooks](https://github.com/NVIDIA/dgx-spark-playbooks/tree/main/nvidia) (commit `3088315`, 2026-10-23),
  files `nvidia/vss/README.md` and `nvidia/playbook-vss/README.md`.

Shorthand used across the spec: `VSS:<path>` = `https://github.com/NVIDIA-AI-Blueprints/video-search-and-summarization/blob/v3.3.0/<path>`.

---

## 1. Your starting assumptions, checked

| Your understanding | Status | Evidence |
|---|---|---|
| VSS combines VLMs, RAG and NIM for summarization, Q&A, search, clip retrieval, alert verification over live + recorded video | **Confirmed** | `VSS:README.md` (Overview, Agent Workflows table) |
| Top-level agent uses MCP for analytics data, incidents and vision tools | **Confirmed.** Agent is built on NeMo Agent Toolkit (NAT) `1.8.0`; Video Analytics MCP (VA-MCP) exposes `get_incidents`, `get_incident`, `get_sensor_ids`, `get_places`, `get_fov_histogram`, `get_average_speeds`, `analyze` | `VSS:services/agent/packages/vss_agents/pyproject.toml`, `VSS:services/agent/packages/vss_agents/src/vss_agents/video_analytics/README.md` |
| Supports x86 Ubuntu, DGX Spark, IGX Thor | **Confirmed, and wider:** also AGX Thor, DGX Station GB300, and (for RT-CV/RT-VLM only) Jetson AGX Orin and Orin NX 16 GB | `VSS:docs/prerequisites.mdx`, `VSS:docs/real-time-vlm.mdx` |
| Fully local "Event Reviewer" on DGX Spark, plus hybrid with remote models | **Outdated.** Event Reviewer was a VSS 2.x reference deployment (`VSS:docs/release-notes-ver-2.mdx`). The newer playbook variant (`nvidia/playbook-vss`) offers only "Standard VSS" hybrid (local VLM, remote LLM). VSS 3.3.0 itself adds a *local* LLM layout on Spark/Thor but says it is "not yet measured" and recommends a remote LLM for latency | Spark playbooks repo; `VSS:docs/edge-deployment.mdx` |
| DGX Spark playbooks pair VSS with Cosmos Reason 2 | **True for the playbook, outdated for VSS.** Playbook: "Support for VSS 3.2.0 with Cosmos Reason 2 VLM", last updated 06/17/2026. VSS 3.3.0 default VLM is **Cosmos3 Nano Reasoner** (`ngc:nim/nvidia/cosmos3-nano-reasoner:bf16-final`); default LLM is **Nemotron 3.5 Lightning 30B-A3B** | Playbook README; `VSS:README.md`; `VSS:docs/real-time-vlm.mdx` |
| Shipped "as is"; production security is the deployer's job | **Confirmed.** Pre-release images are provided "AS IS"; Known Limitations lists missing TLS between components, no authentication on Agent/MCP, DoS risks; Secure Deployment says run only inside a trusted, isolated network | `VSS:README.md`, `VSS:docs/Known-Limitations.mdx`, `VSS:docs/secure-deployment.mdx` |

## 2. Pinned versions (VSS v3.3.0)

| Component | Version | Source |
|---|---|---|
| VSS release | `3.3.0` (`VSS_VERSION`, `VSS_CONTAINER_TAG`) | `VSS:deploy/docker/containers.env` |
| NeMo Agent Toolkit | `nvidia-nat==1.8.0` pinned by VSS; latest on PyPI is `1.9.0` | `VSS:services/agent/packages/vss_agents/pyproject.toml`; [pypi.org/project/nvidia-nat](https://pypi.org/project/nvidia-nat/) |
| MCP Python SDK | VSS requires `mcp>=1.28.1`; latest on PyPI is `2.3.0` (major bump: **ASSUMPTION** that VA-MCP works with 2.x clients; test in M0) | same pyproject; [pypi.org/project/mcp](https://pypi.org/project/mcp/) |
| Default VLM (RT-VLM) | Cosmos3 Nano Reasoner, BF16 (`bf16-final`) is the tested default; "hallucinations may occur with modelopt-fp8 and nvfp4 variants" | `VSS:docs/real-time-vlm.mdx` |
| Edge-only VLM | Cosmos3 Edge, the only variant supported on Jetson Orin NX 16 GB | `VSS:docs/real-time-vlm.mdx` |
| VLM NIM container | `nvcr.io/nim/nvidia/cosmos3-reasoner:1.7` | `VSS:deploy/docker/services/nim/cosmos3-reasoner/compose.yml` |
| Default LLM NIM | `nvcr.io/nim/nvidia/nemotron-3.5-lightning-30b-a3b:2.0.9-variant`, INT4 profile `vllm-int4-tp1-pp1-32.0` on edge, capped at `NIM_GPU_MEM_FRACTION=0.3` | `VSS:deploy/docker/services/nim/nemotron-3.5-lightning-30b-a3b/compose.yml`, `VSS:skills/vss-build-vision-ai/references/edge.md` |
| Fallback small LLM | `nvidia/NVIDIA-Nemotron-Nano-9B-v2-FP8` (11.7 GB) on `nvcr.io/nvidia/vllm:26.07-py3` | same edge.md; `VSS:deploy/docker/services/nim/nvidia-nemotron-nano-9b-v2-fp8/compose.yml` |
| Jetson AGX Thor OS / driver | JetPack 7.2 (L4T r39.2), driver 595.78 | `VSS:docs/prerequisites.mdx` |
| DGX Spark OS / driver | DGX OS 7.5.0, driver 580.173.02 | `VSS:docs/prerequisites.mdx` |
| Docker / Compose | `28.3.3 <= Docker < 29.5.0`; Compose `v2.39.1+`; NVIDIA Container Toolkit `1.17.8+` | `VSS:README.md` |
| Kubernetes on edge | Not supported: "Every Tegra platform … DGX Spark … are **Docker Compose only**" | `VSS:skills/vss-build-vision-ai/references/prerequisites.md` |

## 3. Capacity numbers that drive our design (all 1080p H.264 input)

| Measurement | DGX Spark | AGX Thor | Source |
|---|---|---|---|
| RT-CV max streams @ 30 FPS (RT-DETR ResNet50) | 5 | 4 | `VSS:docs/performance-rt-cv.mdx` |
| RT-VLM continuous **alerting** streams (OSL=1, 10 s chunks, FP8) | 2 | 3 | `VSS:docs/performance-rt-vlm.mdx` |
| RT-VLM continuous **captioning** streams (OSL=100) | 1 | 1 | same |
| RT-VLM file mode, 10 s clip, captioning, concurrency 8 | 10.4 s avg, 0.77 req/s | 9.2 s avg, 0.87 req/s | same |
| Alert verification (CV → BA → VLM), RT-DETR + CR3 Nano BF16 | 1 stream: E2E avg 1.54 s, P90 2.46 s | 10 streams: E2E avg 9.11 s, P90 13.92 s | `VSS:docs/performance-alert-verification.mdx` @ `v3.3.0` |
| Same, NVFP4 | 1 stream: P90 2.22 s (`develop` adds 14 streams: P90 11.9 s) | 10 streams: P90 9.72 s | same (tag and `develop`) |

**Design consequence:** continuous VLM on every camera is impossible on a single edge box. We run **always-on CV
on every camera**, plus **event-triggered VLM** (verification, captioning of significant events), plus **low-rate
periodic captions** (one 10 s chunk per camera every 10 min), plus **on-demand VLM** when a question needs it.

Other constraints we inherit:

- Edge boxes share unified memory between CPU and GPU. VSS requires a page-cache cleaner and keeping the sum of GPU memory fractions ≤ 0.8 (`VSS:skills/vss-build-vision-ai/references/edge.md`).
- The VSS search profile on Spark and Thor needs **remote LLM and remote VLM** (`VSS:docs/prerequisites.mdx`). That breaks "footage never leaves the site", so **we do not use VSS search on the edge**.
- The LVS (long video summarization) profile is **not supported** on edge platforms (same source).
- The Alerts microservice (3.3.0) is **Kafka-only**. Redis was removed, and durable state lives in Elasticsearch (`VSS:docs/release-notes.mdx`).
- The RT-CV image is about 18 GB compressed and about 48 GB on disk (`VSS:docs/performance-rt-cv.mdx`). This matters for OTA over metered links.
- Known issue: memory pressure under concurrent summarization on Spark/Thor, and live RTSP OOM on AGX Orin with Cosmos3 Edge (`VSS:docs/release-notes.mdx`).

## 4. What VSS gives us out of the box

| Capability | VSS component | We use it? |
|---|---|---|
| Camera/DVR ingest (ONVIF-S/T discovery, RTSP), recording with aging policy, clip and snapshot extraction, Milestone adaptor, outbound webhooks | VIOS (VST) | **Yes**, as the ingest and recording layer |
| 2D detection + tracking (RT-DETR, Grounding DINO) | RT-CV (DeepStream) | **Yes** |
| Tripwire and ROI enter/exit events, restricted/confined-area and proximity incidents, FOV counts | Behavior Analytics → Kafka (`mdx-events`, incidents) | **Yes** |
| VLM verification of CV alerts, per-alert-type prompts editable at runtime, verdicts to Kafka `mdx-vlm-incidents` | Alerts microservice (Alert Bridge) | **Yes** |
| VLM serving (OpenAI-compatible), live and file captioning | RT-VLM | **Yes** (Cosmos3 Nano BF16) |
| Incident/sensor/metric queries over MCP | VA-MCP | **Yes**, consumed by our agent |
| Chat agent + web UI, report generation | VSS Agent (NAT), Agent UI | **No.** It is UI-coupled and heavy. We build a narrow agent |
| Embedding search (Cosmos-Embed1) | RT-Embed + search profile | **No** on edge (needs remote VLM). Revisit when local search ships on Thor |
| Long video summarization | LVS | **No** on edge (unsupported) |
| Deploy/operate skills for coding agents (`vss-build-vision-ai`, `vss-manage-alerts`, benchmark skills) | `skills/` | **Yes**, as dev tooling for Claude Code sessions, not at runtime |
| Caption-accuracy and Q&A benchmark harnesses | `skills/benchmarking/*` | **Yes**, in our eval plan |

## 5. What we must build

1. **Channel layer:** WhatsApp first, with pluggable adapters, delivered through a cloud relay.
2. **Watchman agent:** a narrow, provider-agnostic agent (cloud Claude or local Nemotron) with our own `site-mcp` tools.
3. **Event index:** Postgres + pgvector on the box. It is the source of truth for events, captions, coverage and the outbox.
4. **Rules gate:** site schedules (armed hours), suppression ("working late"), and per-vertical rule packs feeding Alert Bridge.
5. **Shift summarizer:** coverage-aware, citing event IDs.
6. **Visual memory scheduler:** periodic and event-triggered captioning within a VLM budget.
7. **Resilience:** power state machine, store-and-forward, watchdogs, offline boot (no NGC pulls at runtime).
8. **Fleet:** device identity, config sync, signed OTA with rollback, health telemetry. Runs on a cloud control plane.
9. **Security hardening** beyond the blueprint: segmentation, mTLS, authentication, audit, CVE pipeline.
10. **Privacy policy packs** per jurisdiction, clip-egress consent, signage kit.
11. **Installer tooling:** site survey probe, zone editor, walk test.
12. **Eval harness** on real customer footage.
