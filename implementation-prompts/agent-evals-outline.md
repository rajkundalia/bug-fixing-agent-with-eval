# AI Agent Evals — Medium Post Outline

*Working title ideas:*
- "Demystifying Evals for AI Agents: A Practical Guide"
- "How to Actually Evaluate an AI Agent (Not Just Its Output)"
- "Beyond Accuracy: A Framework for Evaluating AI Agents"

*Sources read: Anthropic, IBM, McKinsey QuantumBlack, Databricks, DeepEval, AWS, NVIDIA, Ida Silfverskiold*

---

## 1. Introduction
- Why evals matter more for agents than for plain LLM calls (multi-step, tool use, cumulative failure modes)
- What this post covers vs. what it doesn't (scope: practical framework + sample project, not a benchmark leaderboard roundup)
- Scoping note (important, sets reader expectations): most of what's called "agent evaluation" today is really *task* evaluation — bounded, human-initiated work with a defined start/end. That's the honest scope of this piece, not a limitation to apologize for. The more autonomous/open-ended a system becomes (self-initiating, continuous, no discrete task boundary), the more evaluation has to shift from a pre-launch test suite toward continuous, live production monitoring — from "did it pass the test" to "is it still behaving well," indefinitely. This piece is built for the bounded-task case, which is also where most real deployments live today.
- Terminology note: vocabulary is inconsistent across vendors/sources — e.g. "faithfulness" vs. "groundedness," "task completion" vs. "goal success" often mean the same thing under different names. Flagged upfront so readers aren't confused when they go compare this piece against primary sources (DeepEval, RAGAS, Databricks, etc. don't all use the same terms for the same concept)

## 2. Foundational Distinctions
### 2.1 Single-turn vs. multi-turn evals
- Single-turn: one prompt → one output → grade it (classic NLP eval)
- Multi-turn: full conversation/trajectory, continuity, drift across turns
- Nuance: multi-turn (conversational) vs. multi-step (agentic/tool-call chain within one turn) — related but distinct
- Brief historical callback: BLEU/ROUGE as early single-turn, surface-overlap metrics — useful for translation/summarization with fixed references, but blind to meaning/paraphrase; motivates the shift to semantic (LLM-judge) evaluation

### 2.2 Capability evals vs. regression evals
- Capability = hard/unsolved tasks, expect low pass rate, shows where to improve
- Regression = known-good tasks, expect ~100%, safety net against breakage
- How a task graduates from capability → regression once mastered

## 3. Designing an Agent Eval: The Right Questions
- Define success (binary vs. partial credit, can two humans agree?)
  - Technique: define tasks as **intent + constraints** (e.g., "update this record through this API within two tool calls") — turns implicit production requirements (efficiency, cost, safety) into explicit, gradeable rules; grade outcome and constraint separately (don't conflate "wrong answer" with "took too many calls" into one pass/fail) so you know which one is failing
  - Caution: constraints can become the wrong optimization target (Goodhart's law) — e.g. an agent skipping a legit verification step just to stay under a call budget; use constraints as diagnostic/reported-alongside metrics during capability-eval stage, save hard gating for regression evals once the constraint is confirmed realistic; also re-check "is the task fair" — a valid edge case might legitimately need more calls
- What am I testing (capability vs regression, single vs multi-turn, component vs end-to-end)
- Who/what grades it (deterministic vs. LLM judge vs. human)
- Is the task itself fair (ambiguity, reference solutions, testing both directions of a behavior)
- Environment realism (clean state, same harness as production)
- Handling non-determinism (pass@k vs pass^k, number of trials)
- Am I measuring what I think (reading transcripts, judge gameability, rubric specificity)
  - Core principle: grade the **trajectory**, not just the final answer — a correct answer can hide a bad process (lucky guess, unnecessary destructive tool call, correct data misreported in the final response) and a wrong answer can hide a sound process (bad/stale data, ambiguous task); grading final output alone loses the "why," which is what you need to actually fix the agent
  - Named tension worth surfacing: outcome-first grading (Anthropic — grade what was produced, don't rigidly require one exact path, since multiple valid paths can exist) vs. process-first grading (NVIDIA/DeepEval — trajectory & tool-call precision as first-class scored signals); practical resolution: use outcome as the pass/fail ground truth, always capture full trajectory as the diagnostic tool regardless of which philosophy you lean toward
- Ownership & lifecycle (who maintains it, when does it graduate, how is drift caught)

## 4. A Note on Public/Generic Benchmarks
- Landscape: MiniWoB++ (simplified web-UI tasks, now largely saturated/easy for frontier models), HLE (broad expert-level knowledge/reasoning, non-agentic), ARC-AGI-2 (abstract visual-puzzle reasoning, non-agentic), OfficeQA/MultiDoc QA (document comprehension/retrieval, non-agentic), MMLU (57-subject multiple-choice academic knowledge test, single-turn/non-agentic, now largely saturated for frontier models — good callback example for topic #1's single-turn category)
- Useful for: sanity-checking a base model's raw capability before building on it; standardized cross-model comparison
- Not sufficient because: they test general capability, not *your* agent on *your* tools/task; several aren't agentic (tool-use/trajectory) at all; public benchmarks risk contamination/overfitting; none cover safety, tool-calling correctness, cost, or drift
- Framing line: "Generic benchmarks tell you how smart the underlying model is. They don't tell you whether your agent, wired to your tools, solving your task, is any good."
- Optional: mention more realistic agentic successors (WebArena, OSWorld, Mind2Web) if naming alternatives

## 5. The Eval Workflow / Pipeline
- Collect representative data (real cases, edge cases, known failures)
- Run tests — including across different LLMs/models for comparison
- Analyze results (read failing transcripts, not just scores)
- Iterate — refine agent, refine the eval itself

### 5.1 Tooling landscape (pre-deployment vs. post-deployment — and where lines blur)
- **DeepEval** — open-source, pytest-style eval framework in Python; large built-in metric library (G-Eval, hallucination, faithfulness, tool-correctness); maps to topic #7 (rule-based + LLM-judge in code) and topic #9 (red-teaming/safety metrics)
- **Confident AI** — DeepEval's own cloud platform (same creators); adds tracing/observability on top of DeepEval — agentic execution trees (agent/llm/tool spans), production monitoring, alerts on quality degradation; correction/nuance: DeepEval isn't purely "offline testing" — via Confident AI it competes directly with Langfuse on tracing, not a clean pre/post split
- **Promptfoo** — open-source CLI, YAML-config-driven; strongest at prompt regression testing (topic #2) and security/red-teaming (topic #9); note: acquired by OpenAI (announced Mar 2026) for Frontier agent platform integration, core OSS project committed to staying MIT-licensed/model-agnostic — flag as "watch this space"
- **Langfuse** — open-source observability/tracing platform; captures production traces, attaches scores (often from an eval tool sampling production traffic); maps to topic #8 (drift) — catches what static eval suites miss after launch
- **NVIDIA NeMo Agent Toolkit** — different category from the other three: an agent orchestration/connectivity library (connects existing enterprise agents to tools/data across any framework) that ships evaluation built in, rather than a standalone eval tool bolted onto an agent; notable for a dedicated trajectory evaluator (operationalizes the "grade trajectory, not just the answer" principle from topic #3) plus built-in RAGAS metric integration (AnswerAccuracy, ResponseGroundedness, ContextRelevance — echoes topic #6.2); also includes a hyper-parameter/prompt optimizer to auto-tune configs post-eval; caveat: NVIDIA's own docs flag the Evaluation API as experimental, subject to breaking changes
- Revised framing: the eval and observability worlds are converging rather than staying in separate lanes — DeepEval/Confident AI and Langfuse increasingly overlap on tracing; Promptfoo stays more narrowly focused on regression + red-teaming at CI/PR time; NeMo Agent Toolkit represents a third lane — evaluation as a built-in feature of an orchestration platform rather than a bolt-on
- Common real-world pattern: Promptfoo as CI gate at PR time → DeepEval running scheduled evals on sampled production traces → scores/traces visualized in Confident AI or Langfuse for trend/drift visibility

## 6. What to Measure: Metric Categories
### 6.1 Tool-calling / function-calling evaluation
- Note: tool misuse is consistently cited as one of the most common — and most agent-specific — failure modes in production; unlike hallucination/reasoning errors (which exist for any LLM), tool misuse is intrinsic to what makes something an *agent* (it takes real actions)
- Tool selection — right tool for the job?
- Parameter values — correct values passed?
- Parameter type — correct data type/schema?
- Hallucinated parameters — invented values not grounded in context?
- Missing required parameters
- Extra/unexpected parameters
- Sequencing — right order when order matters?
- Silent failure handling — does the agent notice and surface a failed/empty tool response, or does it proceed as if the call succeeded? (a single bad call at step N can silently corrupt every step after it — often the most insidious failure to catch)

### 6.2 Response correctness
- Factual accuracy, groundedness/faithfulness to source
- Did it resolve the user's actual intent (not just superficially answer)?

### 6.3 Functional / operational metrics
- Core insight (asymmetry): wrong answers are self-flagging — caught by judges, users, failing tests, short loud feedback loop. Expensive-but-correct answers are not — no error, no complaint, just a bigger bill or slower response, diffused across many requests until someone notices weeks later. "Cheap wrong answers get fixed; expensive right answers can still sink the product." Judges are built to catch the loud failure; they're structurally blind to the quiet one — trace-level accounting deserves equal *regression rigor* to correctness, not just dashboard tracking (though not equal priority — correct-but-slow still beats fast-but-wrong)
- Cost (tokens/$ per task, compounds across multi-step trajectories)
- Latency (matters differently for batch vs. real-time agents)
- Error rate (crashes, loops, unrecoverable tool errors)
- Success rate / task completion (headline metric, often paired with pass@k)
- Number of turns/steps to completion — efficiency signal & leading indicator for cost/latency; also useful for spotting loops/non-convergence; caution: not simply "lower is better" (too few can mean skipped verification; normalize by task complexity; don't optimize directly for it — Goodhart's law risk)
- Practical regression discipline: track token totals and step counts on the *regression suite*, not just as capability-eval descriptive stats — set thresholds, fail the build if a model swap or prompt tweak regresses cost/steps on tasks that were already solved efficiently, even if correctness judge still passes. A model swap that gains 2% accuracy but multiplies token usage 5x should be flagged, same as a correctness regression would be
- Connects to drift (topic #8): a silent model-drift event is often invisible in correctness first but visible in trace-level accounting first — cost/step-count regression can be a leading indicator that catches drift before a user does
- Framing: correctness metrics tell you if it works; functional metrics tell you if it's worth shipping

## 7. How to Grade: Rule-Based vs. LLM-as-Judge
- Rule-based: deterministic, cheap, reproducible — best for exact-match checks (function names, types, schema, final state)
- LLM-as-judge: semantic/fuzzy judgments — best for open-ended correctness, reasoning quality, groundedness
- Worked example: apply both to function-calling (type errors/missing params = rule-based; hallucinated/contextually-appropriate params = LLM judge)
- Judge calibration caution: calibrate against human labels, watch for leniency/gaming

## 8. Drift in Agents
- Model drift (provider updates the underlying model silently)
- Data/input drift (real-world inputs diverge from what was tested)
- Behavioral/prompt drift (small accumulated changes shift overall behavior)
- Context/environment drift (dependent APIs/tools change underneath the agent)
- Why this makes evals a continuous practice, not a one-time gate
- Tie-back: regression suite as primary defense; production monitoring to catch what static evals miss

## 9. Adversarial & Robustness Testing
- Tricky/ambiguous phrasing — tests robustness, not just capability (rephrased, misspelled, underspecified inputs)
- Adversarial/malicious prompts — safety & security angle:
  - Prompt injection (malicious instructions hidden in tool outputs/docs/webpages)
    - Direct injection (a user types malicious instructions live) vs. indirect injection (malicious/unintended instructions embedded in content the agent *reads* — comments, docstrings, files, retrieved docs — with no live attacker typing anything)
    - Applies even to "controlled" agents with no live user input (e.g., a code/language migration agent) — any file it reads is untrusted content by default; also relevant as a non-malicious failure mode: does the agent correctly treat code as data to transform vs. instructions to obey?
    - Risk scales with (a) how much untrusted content the agent reads and (b) how much tool access/power it has to act on what it reads — not with whether there's a live chat interface. Narrowly-scoped, read-only/limited-write agents have smaller blast radius even if injection succeeds
  - Jailbreaks (bypassing guardrails via clever framing)
  - Goal hijacking (steering a multi-step agent off-task mid-trajectory)
  - Data exfiltration attempts (leaking system prompts, other users' data, secrets)
- Out-of-scope/refusal testing — does it correctly decline/escalate instead of acting? Ties back to "test both directions of a behavior" (topic #3)
- Why agents need this more than chatbots: tool access = real-world consequences, not just bad text
- Grading mindset shift: success = resisting/refusing, not completing — different pass/fail shape than task-completion metrics
- Often run as a separate red-team suite, sometimes owned by security rather than product

## 10. Sample Project — FINAL SCOPE

**Project: Local GitHub-issue-resolution agent**
- Small local Python repo, seeded with ~10-15 deliberately broken single-file bugs (one synthetic "issue" per scenario)
- Agent loop: inspect code → identify relevant file(s) → edit code → run tests → repeat until green (or hits attempt/turn cap)
- Framing: the eval **framework** is the real teaching artifact; the agent is the vehicle — repo structured so every article section maps to a literal file

**Repo structure (single GitHub repo, not split):**
```
agent-evals-framework/
├── agents/            # the agent under test (claude-haiku-4-5 via Anthropic API, tool definitions for read_file/edit_file/run_tests)
├── evals/
│   ├── outcome.py           # rule-based: tests pass?
│   ├── tool_correctness.py  # rule-based: correct files opened/modified vs. known-correct answer per task
│   ├── trajectory.py        # rule-based: attempt count, dead loops, turns-to-green
│   ├── fix_quality.py       # LLM-judge: genuine fix vs. workaround — compares diff against planted root cause
│   ├── efficiency.py        # rule-based: cost, latency, tool-call count
│   ├── safety.py            # rule-based: did it break unrelated/previously-passing tests
│   └── regression.py        # rule-based: same issue set re-run after every prompt/model change
├── judges/
│   └── llm_judge.py         # claude-haiku-4-5, used for task_completion.py and fix_quality.py
├── datasets/            # 10 broken-file task scenarios with known-correct answer & planted root cause
└── reports/             # tasks × evaluators results table per run

**Models (Anthropic Messages API):**
- Agent under test: `claude-haiku-4-5` (native tool-calling)
- Judge: `claude-haiku-4-5` (categorical rubric scoring for completion and fix quality)
- Sequential execution only — agent runs saved to trace/transcript first, judge scores transcripts afterward; no concurrent loading needed, fits comfortably in 16GB RAM

**Eval categories (finalized):**
| Category | What it checks | Grading method |
|---|---|---|
| Outcome | Issue fixed (tests pass) | Rule-based |
| Tool correctness | Correct file(s) opened/modified | Rule-based, vs. known-correct answer |
| Trajectory | Number of attempts, dead loops | Rule-based (from trace) |
| Trajectory | Wrong hypotheses (agent's stated reasoning was off-track) | LLM-judge |
| **Fix quality** (added — catches the workaround trap) | Genuine root-cause fix vs. gamed pass (deleted assertion, broad except, edited test not source) | LLM-judge, compares diff against planted root cause |
| Efficiency | Cost, latency, tool-call count | Rule-based (from trace) |
| Safety | Didn't break unrelated/previously-passing tests | Rule-based — run full suite, not just target test |
| Regression | Same issue set re-run after every prompt/model change | Rule-based, repeated over time/CI |

**Output**: a tasks × evaluators results table per run — e.g. "success rate 80%, but genuine-fix rate only 60%" is the kind of finding this structure surfaces, feeding directly into section 11 (Lessons Learned)

**Config-comparison harness (operationalizes topics #2 and #8 concretely)**: every run tagged by config (prompt version + toolset). Baseline vs. prompt-variant run isolates prompt-change effects; baseline vs. tool-variant run (e.g., `run_tests` removed) isolates tool-change effects. `reports/compare_configs.py` diffs results across configs — surfaces per-task regressions, task-completion score deltas, and tool-flow changes (e.g., verification step disappearing from the trajectory). This turns "regression/drift evals should catch prompt or tool changes" from a described concept into a working before/after demonstration — strong candidate for the article's most compelling concrete finding.

**Task completion, dual-layer**: `outcome.py` stays rule-based/binary (tests pass — cheap, fast, good CI gate). New: `task_completion.py` is an LLM-judge that reads the full trace plus the original task goal and returns a continuous 0-1 score with rationale — richer signal than binary pass/fail, direct worked example of topic #7's rule-based-for-gating / judge-for-nuance split.

**Tool-flow as its own metric**: `tool_flow.py` captures the sequence/shape of tool calls (not just which files got touched) — comparable across configs, catches things like "verification step disappeared" or "editing without reading first."

**Repo hosting**: public GitHub repo (not local-only) — enables reader reproducibility, natural home for regression/CI (topic #2), and a real GitHub Actions green/red check makes a strong visual for the regression-evals section of the article. Build and iterate locally first, push once the harness works end to end.
```


## 11. Lessons Learned / Pitfalls
- (Pull from sample project experience once built)
- Common candidates to expand on: ambiguous task specs, lenient judges, state leakage between trials, over-indexing on pass rate without reading transcripts

## 12. Closing
- Recap: evals as an evolving discipline, not a solved checklist
- Where to go next (links to the 8 source articles, tools mentioned: DeepEval, LangSmith, MLflow, etc.)

---

## Open items — all resolved
- [x] Sample project finalized: local GitHub-issue-resolution agent, single-repo eval framework (see section 10)
- [x] Framework/models: `claude-haiku-4-5` (agent and judge) via Anthropic API
- [x] Agent implementation: raw Anthropic Messages API tool-calling (`anthropic` library), no agent framework — chosen for transparency, minimal dependencies, and full control over trace logging for custom evaluators
- [x] Tool-naming tone: mostly framework-agnostic in main body, name tools when clearest (see intro)
- [x] Terminology note: written into introduction section
