
# StrongAfter Blackboard Solution — Evolution Map

This document synthesizes the progression of the blackboard-based text processing system using the uploaded artifacts. It highlights **where we started**, key **milestones**, **design deltas**, and **next steps** to close remaining gaps.

---

## Narrative Snapshot 

I started with a linear, two‑call LLM pipeline that was **accurate but slow** (25–30s p95). By mapping the flow and agentizing into a **blackboard** pattern, I isolated ranking and summary as the heavy steps. We then flipped ranking to **local deterministic scoring**, reserving Gemini only to add **nuance priors** on ambiguous inputs, and tightened summary with **bounded tokens and validators**. The system now emphasizes **evidence honesty**, **adaptive depth**, and **measurable quality**, targeting **≤3.5s p95** while maintaining or improving human‑rated output.

---

## Phase 0 — Starting Point (Pre‑Blackboard / Monolith)
**Representative docs**: `LADDER_DIAGRAM.md`, `PROCESS_FLOW_MAPPING.md`  
**What it looked like**
- Single synchronous pipeline: frontend → backend → **two Gemini calls** (ranking + summary) → response.
- Ranking done by a **massive prompt** against 20+ themes, summaries generated with multiple excerpts.
- No adaptive depth or gating; minimal caching.
**Observed issues**
- **p95 latency 25–30s**, dominated by LLM calls.
- Risk of hallucinated citations; inconsistent tone control.
- Limited observability beyond basic timings.

---

## Phase 1 — System Mapping & Bottleneck Identification
**Representative docs**: `BLACKBOARD_LADDER_DIAGRAM.md`, `BLACKBOARD_PATTERN_ANALYSIS.md`  
**Shift**
- Formal ladder diagrams of the whole flow, identifying **Theme Analysis** and **Summary Generation** as bottlenecks.
- Articulated early ideas for **pre‑filtering** and **prompt slimming**.
**Impact**
- Clear visibility into critical path; created shared language for refactor.

---

## Phase 2 — Blackboard Architecture & Agentization
**Representative docs**: `BLACKBOARD_IMPLEMENTATION_SUMMARY.md`  
**Shift**
- Introduced **blackboard orchestrator** with specialized agents: Ranker, Retriever (FAISS), Summarizer.
- Moved from monolithic request handler to **publish/subscribe** style orchestration.
**Impact**
- Enabled **parallelism** and **component-level** optimization.
- Prepared ground for hybrid local + remote strategies.

---

## Phase 3 — Retrieval Discipline (FAISS) & Evidence Honesty
**Representative docs**: `PROCESS_FLOW_MAPPING.md`, `BLACKBOARD_PATTERN_ANALYSIS.md`  
**Shift**
- Standardized on FAISS similarity search for excerpts; introduced cosine thresholds.
- Separated **evidence finding** from **summary writing**; citations must map to retrieved snippets.
**Impact**
- Reduced hallucinations; clearer contracts between agents.

---

## Phase 4 — Hybrid Ranking Direction (Local‑First + Nuance)
**Representative docs**: `SELF_HOSTED_MODEL_OPTIMIZATION.md`, `BLACKBOARD_IMPLEMENTATION_SUMMARY.md`  
**Shift**
- Proposed **deterministic local scoring** (BM25 + dense cosine) as source of truth.
- **Gemini used only for nuance priors** on ambiguous inputs; priors merged with local scores.
**Impact**
- Expected p95 → **2–3.5s** while maintaining quality via adaptive depth.

---

## Phase 5 — Quality & Safety Guardrails
**Representative docs**: `BLACKBOARD_PATTERN_ANALYSIS.md`  
**Shift**
- Added **confidence gates** (margin, entropy, top cosine), tone rubric, and safety escalation keywords.
- JSON‑only prompts; validators for schema, length, and citation honesty.
**Impact**
- More consistent user‑facing output; reduced error modes.

---

## Phase 6 — A/B Testing & Benchmarks
**Representative docs**: `AB_TESTING_GUIDE.md`, `AB_TEST_RESULTS.md`  
**Shift**
- Defined test methodology (control vs hybrid pipeline), metrics (win rate, p50/p95, timeout rates).
- Early results indicate **non‑inferior quality** with large latency gains (inferred from docs).
**Impact**
- Created path to **evidence‑based rollout** (canary → full).

---

## Phase 7 — Platform Readiness & Expansion
**Representative docs**: `SOFTWARE_EXPANSION_OPTIONS.md`  
**Shift**
- Options to extend to new modalities/agents; self‑hosting considerations for embeddings.
**Impact**
- Roadmap beyond text‑only; modular growth aligned with blackboard pattern.

---

## From/To Design Deltas

| Dimension | From (Start) | To (Now/Target) |
|---|---|---|
| Ranking | LLM ranks 20+ themes via large prompt | **Local deterministic** rank + **Gemini nuance priors** on low-confidence |
| Summary | Long prompt, 8–12s | **Balanced mode** (≤140 tokens), QF on escalation, hard timeouts |
| Evidence | Mixed; sometimes implicit | **FAISS‑backed**, cosine‑thresholded, citations may be empty if weak |
| Control | Linear, blocking | **Blackboard orchestration**, agents run in parallel |
| Quality | Best‑effort | **Gates + validators** (margin/entropy/cosine, tone, JSON schema) |
| Observability | Basic timings | Structured metrics + benchmark harness |
| Cost | Cloud LLM for ranking & summary | **Local‑first (near‑zero)**; cloud only on ambiguous cases |

---

## What’s Done vs. What’s Left

**Done (per docs):**
- Architecture & flow mapped with bottlenecks.
- Blackboard orchestrator pattern established.
- FAISS retrieval integrated; citation honesty principle documented.
- Hybrid strategy decided; A/B test framework outlined.

**Remaining (recommended to formalize):**
1. **Config source of truth** (`quality.yml`): thresholds (margin, entropy, top_cosine), modes (instant/balanced/QF), min_citation_cosine.
2. **Nuance priors schema & prompt** (JSON Schema + contract test).
3. **Benchmark harness** (`/bench/latency_bench.py`) with stratified dataset; commit CSVs.
4. **Metrics schema** (`/metrics` fields) and dashboards for p50/p95, fallback rate, safety hits.
5. **FAISS hygiene doc**: index type, normalization, thresholds, and recall/latency tradeoffs.
6. **Cost table** for 100k / 1M requests under 5% and 10% Gemini fallback scenarios.

---

## Immediate Next Actions 

- Ship **`quality.yml`** and wire thresholds throughout agents.
- Implement **`agent.nuance_remote`** (Gemini JSON‑only priors) + **`agent.hybrid_rank`** (merge α logic).
- Add **schema validators** for nuance + summary; fail open to deterministic fallback.
- Create **/bench** harness and capture baseline vs hybrid p50/p95 + win‑rate on a 200‑prompt set.
- Stand up **/metrics** endpoint and log the key fields per request.

---


