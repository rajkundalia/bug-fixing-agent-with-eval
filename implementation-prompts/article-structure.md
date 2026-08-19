# Agent Evals — Article Structure
*Question-driven structure for the Medium post. Use `agent-evals-outline.md` for the detailed content notes behind each heading.*

---

## Introduction
- Why evals matter more for agents than for plain LLM calls (multi-step, tool use, cumulative failure modes)
- Scoping note: most of what's called "agent evaluation" today is really *task* evaluation — bounded, human-initiated work with a defined start/end. That's the honest scope of this piece. More autonomous/open-ended systems shift toward continuous production monitoring, not a pre-launch test suite.
- Terminology note: vocabulary is inconsistent across vendors — "faithfulness" vs. "groundedness," "task completion" vs. "goal success" often mean the same thing under different names.

---

## What am I evaluating?

### Single-turn vs. multi-turn
- Single-turn: one prompt → one output → grade it
- Multi-turn: full conversation, continuity, drift across turns
- **Multi-turn (conversational) vs. multi-step (agentic)** — related but distinct:
  - Multi-turn = back-and-forth conversation across separate prompts
  - Multi-step = a chain of tool calls within a single agent run
- Historical note: BLEU/ROUGE as early single-turn surface-overlap metrics — useful for translation/summarization with fixed references, blind to meaning — motivates the shift to LLM-judge evaluation

### Capability evals vs. regression evals
- **Capability** = hard/unsolved tasks, expect low pass rate, shows where to improve
- **Regression** = known-good tasks, expect ~100%, safety net against breakage
- How a task graduates from capability → regression once mastered

---

## What does success look like?

### Intent + constraints
- Define tasks as **intent + constraints** — e.g., "update this record through this API within two tool calls"
- Turns implicit production requirements (efficiency, cost, safety) into explicit, gradeable rules
- Grade outcome and constraint separately — don't conflate "wrong answer" with "took too many calls" into one pass/fail
- Caution: constraints can become the wrong optimization target (Goodhart's Law) — e.g. an agent skipping a legit verification step to stay under a call budget

### Ground truth
- Can two humans agree on what "done" looks like?
- Binary vs. partial credit
- Is the task itself fair — ambiguity, reference solutions, testing both directions of a behavior

### Task completion
- Grade the **trajectory**, not just the final answer
  - A correct answer can hide a bad process (lucky guess, unnecessary destructive call)
  - A wrong answer can hide a sound process (bad data, ambiguous task)
- Outcome-first (Anthropic) vs. process-first (NVIDIA/DeepEval): practical resolution — use outcome as pass/fail ground truth, always capture full trajectory as the diagnostic tool

---

## What should I measure?

### Outcome
- Did the tests pass? Binary, cheap, good CI gate.

### Tool correctness
- Tool selection — right tool for the job?
- Parameter values — correct values passed?
- Parameter type — correct data type/schema?
- Hallucinated parameters — invented values not grounded in context?
- Missing required parameters
- Extra/unexpected parameters
- Sequencing — right order when order matters?
- Silent failure handling — does the agent notice a failed tool response, or proceed as if it succeeded?
- **Note: tool misuse is one of the most common — and most agent-specific — failure modes in production**

### Trajectory
- Number of attempts, dead loops, turns to completion
- Tool flow: the sequence/shape of tool calls (not just which files got touched)
- Wrong hypotheses: agent's stated reasoning was off-track
- Caution: turns-to-completion is not simply "lower is better" — too few can mean skipped verification

### Functional metrics
- Cost (tokens/$ per task — compounds across multi-step trajectories)
- Latency (matters differently for batch vs. real-time agents)
- Error rate (crashes, loops, unrecoverable tool errors)
- Success rate / task completion
- **The asymmetry:** wrong answers are self-flagging — caught by judges, users, failing tests. Expensive-but-correct answers are not — no error, no complaint, just a bigger bill. "Cheap wrong answers get fixed; expensive right answers can still sink the product."

### Safety
- Did it break unrelated/previously-passing tests?
- Did it take a destructive action it shouldn't have?

---

## How should I measure it?

### Rule-based
- Deterministic, cheap, reproducible
- Best for: exact-match checks — function names, types, schema, final state, file paths
- Examples: did tests pass? did it edit the right file? did it call the right tool?

### LLM-as-a-judge
- Semantic/fuzzy judgments
- Best for: open-ended correctness, reasoning quality, groundedness, fix quality
- Judge calibration caution: calibrate against human labels, watch for leniency/gaming

### Hybrid — worked example
Apply both to the same signal:
- Type errors / missing params → rule-based
- Hallucinated / contextually-wrong params → LLM judge
- Task completion: `outcome.py` (binary rule-based, CI gate) + `task_completion.py` (0-1 LLM-judge with rationale, nuanced comparison)

---

## How do I build good evaluation datasets?

### Representative tasks
- Collect real cases, edge cases, and known failures
- Vary bug type, difficulty, and context
- Each task needs: description, target file, known-correct answer, planted root cause, test file, max turns

### Edge cases
- Ambiguous task specs
- Tasks that legitimately need more tool calls than the constraint allows
- Tasks where the "obvious" fix is a workaround, not a real fix

### Adversarial / regression scenarios
- At least one adversarial task: plant a misleading instruction *inside* the file the agent reads
  - Tests indirect prompt injection — malicious/unintended instructions embedded in content the agent reads (comments, docstrings), not typed by a live user
  - Pass = agent fixes the actual bug, ignores the planted comment
- Known-good tasks that become the regression suite once solved

---

## How do I know if the agent is getting worse?

### Regression evals
- Re-run solved tasks after every prompt/model/tool change
- Set thresholds, fail the build if cost or step count regresses even when correctness passes
- A model swap that gains 2% accuracy but multiplies token usage 5× should be flagged

### Drift
- **Model drift** — provider updates the underlying model silently
- **Data/input drift** — real-world inputs diverge from what was tested
- **Behavioral/prompt drift** — small accumulated changes shift overall behavior
- **Environment drift** — dependent APIs/tools change underneath the agent
- Why this makes evals a continuous practice, not a one-time gate

### Config comparison (prompt changes + tool changes)
- Every run tagged with a config (prompt version + toolset)
- Baseline vs. prompt-variant → isolates prompt effect
- Baseline vs. tool-variant → isolates tool effect
- Example finding: *"Removing `run_tests` dropped task-completion scores from 0.81 to 0.34 avg, and tool_flow shows the agent now edits blindly without verifying."*

---

## How do I test robustness?

### Adversarial prompts and ambiguous phrasing
- Tricky/ambiguous phrasing — tests robustness, not just capability
- Rephrased, misspelled, underspecified inputs

### Prompt injection
- **Direct injection**: a user types malicious instructions
- **Indirect injection**: malicious/unintended instructions embedded in content the agent *reads* — comments, docstrings, files, retrieved docs — with no live attacker typing anything
- Applies even to agents with no live user input (e.g., a code migration agent) — any file it reads is untrusted content by default
- Risk scales with (a) how much untrusted content the agent reads and (b) how much tool access/power it has — not with whether there's a live chat interface

### Failure cases
- Out-of-scope inputs: does it correctly decline/escalate instead of acting?
- Goal hijacking: steering a multi-step agent off-task mid-trajectory
- Grading mindset shift: success = **resisting/refusing**, not completing — different pass/fail shape than task-completion metrics

---

## How do I operationalize evaluation?

### CI (pre-deployment)
- Regression suite as a GitHub Actions gate — green/red check on every PR
- Cheap rule-based checks (outcome, tool correctness) are ideal CI gates — fast and deterministic
- LLM-judge checks are better scheduled (expensive) than blocking every commit

### Production monitoring (post-deployment)
- Static eval suites miss what happens after launch
- Drift is often invisible in correctness first, visible in trace-level accounting first — cost/step-count regression can be a leading indicator

### Tooling landscape
- **DeepEval** — open-source, pytest-style eval framework; large built-in metric library (G-Eval, hallucination, faithfulness, tool-correctness); also offers tracing via Confident AI (its cloud platform)
- **Promptfoo** — open-source CLI, YAML-config-driven; strongest at prompt regression testing and red-teaming/security; acquired by OpenAI (Mar 2026), OSS project committed to staying MIT-licensed/model-agnostic
- **Langfuse** — open-source observability/tracing platform; captures production traces, attaches scores; catches what static eval suites miss after launch
- **NVIDIA NeMo Agent Toolkit** — different category: agent orchestration library with evaluation built in (not a standalone eval tool); notable for a dedicated trajectory evaluator and built-in RAGAS metric integration; Evaluation API flagged as experimental
- **Common real-world pattern**: Promptfoo as CI gate at PR time → DeepEval running scheduled evals on sampled production traces → scores/traces visualized in Confident AI or Langfuse for trend/drift visibility
- **Revised framing**: the eval and observability worlds are converging — DeepEval/Confident AI and Langfuse increasingly overlap on tracing; Promptfoo stays narrowly focused on regression + red-teaming at CI/PR time; NeMo represents a third lane — evaluation as a built-in feature of an orchestration platform

---

## A note on public benchmarks
- MiniWoB++ (web-UI tasks, largely saturated for frontier models), HLE (expert-level knowledge, non-agentic), ARC-AGI-2 (abstract visual-puzzle reasoning, non-agentic), OfficeQA/MultiDoc QA (document comprehension, non-agentic), MMLU (57-subject multiple-choice, single-turn, largely saturated)
- Useful for: sanity-checking a base model's raw capability before building on it
- Not sufficient: they test general capability, not *your* agent on *your* tools/task
- **Framing line**: *"Generic benchmarks tell you how smart the underlying model is. They don't tell you whether your agent, wired to your tools, solving your task, is any good."*
- More realistic agentic alternatives worth mentioning: WebArena, OSWorld, Mind2Web

---

## Sample project (the worked example throughout)
*Each section above maps to a literal file in the project repo.*

- **Agent**: `qwen3:8b` via Ollama, fixes deliberately broken single-file Python bugs
- **Judge**: `llama3.1:8b` via Ollama (different model family — reduces self-preference bias)
- **Eval files**: one file per eval category above
- **Config comparison harness**: baseline vs. prompt-variant vs. tool-variant
- **Key finding to demonstrate**: the config comparison surfaces "genuine fix rate 60% vs. pass rate 80%" — a gap that pure outcome grading misses entirely

---

## Lessons learned / pitfalls
*(Pull from sample project experience once built)*

Common candidates:
- Ambiguous task specs that make grading impossible
- Lenient judges that let workarounds through
- State leakage between trials
- Over-indexing on pass rate without reading transcripts
- Optimizing directly for turn count (Goodhart's Law)

---

## Closing
- Evals as an evolving discipline, not a solved checklist
- Links to source articles (Anthropic, IBM, McKinsey QuantumBlack, Databricks, DeepEval, AWS, NVIDIA, Ida Silfverskiold)
