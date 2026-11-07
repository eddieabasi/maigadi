# maigadi

**On-prem AI watchman for your existing CCTV.** Ask what happened in plain language, and get shift summaries and verified alerts on WhatsApp. Built on NVIDIA VSS. Footage never leaves the site.

> *"When did the delivery truck leave yesterday?"* · *"Was anyone in the stockroom after closing?"* · *"Summarize the night shift at the loading bay."*

## What it does

- **Answers questions about your footage** in plain language, with times, cameras and evidence. It tells you when a camera was offline instead of guessing.
- **Sends shift summaries** to WhatsApp: trucks in and out, after-hours activity, verified alerts, camera health.
- **Sends verified alerts.** A vision-language model checks every detection before your phone buzzes.

## How it works

1. A small box (NVIDIA Jetson AGX Thor) connects to your **existing DVR/NVR or IP cameras** on the local network.
2. On the box, it detects and tracks people and vehicles on every camera, verifies events with a local vision-language model, and keeps a searchable log.
3. Only **text** (alerts, summaries, answers) and clips **you explicitly request** ever leave the site.
4. The box is built for **unreliable power and intermittent, metered internet**: battery-backed, store-and-forward, self-healing.

## Principles

- Footage stays on site. No cloud video storage, no live streaming.
- No face recognition, plate recognition or audio. maigadi tracks events, not identities.
- Messaging is pluggable. WhatsApp ships first; Telegram, SMS, Slack and Teams are adapters.
- Privacy settings follow the jurisdiction of each site (Nigeria NDPA first; EU/UK/US packs ready for legal review).

## Status

**Specification phase.** Launch market: Nigeria (warehouses and distribution yards), designed to generalize globally.

| Spec | |
|---|---|
| [PRD](spec/PRD.md) | Problem, ICP, journeys, scope, metrics, pricing |
| [Architecture](spec/ARCHITECTURE.md) | Ingest, CV + VLM, index, agent + MCP tools, channels, fleet |
| [Hardware & deployment](spec/HARDWARE_AND_DEPLOYMENT.md) | Tier comparison, v1 box, site kit |
| [Reliability](spec/RELIABILITY.md) | Power, connectivity, watchdogs, OTA, fleet health |
| [Security & privacy](spec/SECURITY_AND_PRIVACY.md) | Threat model, hardening, jurisdiction policy packs |
| [Eval plan](spec/EVAL_PLAN.md) | Metrics, labelled test sets, release gates |
| [Build plan](spec/BUILD_PLAN.md) | Milestones, session-sized tasks, repo layout |
| [Risks & open questions](spec/RISKS_AND_OPEN_QUESTIONS.md) | Risk register, decisions needed |
| [VSS baseline](spec/VSS_BASELINE.md) | What NVIDIA VSS 3.3.0 gives us (verified) vs what we build |

Built on the [NVIDIA AI Blueprint for Video Search and Summarization](https://github.com/NVIDIA-AI-Blueprints/video-search-and-summarization) (v3.3.0).
