# When Building an AI Agent, the Journey Matters as Much as the Destination

*A practical framework for evaluating trajectories, tool use, and process, not just the final answer.*

---

## 1. Introduction

I am sure almost everyone reading this has tried to build an AI agent by now. For the POC, after some trial and error, it works, and you can demo it, everyone is impressed. You have tested it manually and it works, mostly.

But thinking in terms of software engineering, you know that conventionally the code had integration tests, unit tests, etc. I am sure it did not cover everything, but it gave me baseline confidence. For AI agents, the story is very different.

An AI agent has variability, it can hallucinate into an infinite loop, take a different trajectory then what you had thought of, invent its own responses/tools and can also say that the work is done when it might not have been done. When you evaluate a standard LLM call, you are generally grading a single output. You put a prompt in, you get text out, and you figure out if that text is accurate. But agents change the game because they take actions. They rely on **tool use**, **multi-step reasoning**, and **compounding failures**. If your agent hallucinates a parameter during a tool call at step two, it can silently derail the entire process and the scariest part is, the final answer it gives you might still look completely correct.

I didn't want to write about agent evaluation purely theoretically, so I built a small bug-fixing agent, planted 10 bugs, and built an evaluation harness around it. The entire project is open-source, if you want to follow along or run the evaluators yourself: **[Bug-Fixing Agent & Evaluation Framework on GitHub](https://github.com/rajkundalia/bug-fixing-agent-with-eval)**.

In this page, I am trying to explore how to evaluate an AI agent, not just its output, but its *process*. I am writing this after reading multiple pages and making some experiments with my AI agent. It is more of a personal journey and I wanted to document it. I am sure it will be useful for others as well.

### Scoping the Problem
Before jumping in, let me set a quick boundary. When I say "evaluating an agent" in this post, I am talking about an agent that you give a specific task to (like "fix this bug"), and it stops when it's done. I am not talking about futuristic agents that run 24/7 in the background without human supervision.

---

## 2. Foundational Concepts in Agent Evaluation

Before jumping into the experiments I ran, there are a few core concepts to get right.

### Single-Turn vs. Multi-Step
- **Single-turn**: One prompt in, one output out. Classic NLP evaluation (like BLEU or ROUGE) focused on surface overlap, which drove the shift to semantic LLM-judge evaluations.
- **Multi-step (Agentic)**: A chain of tool calls and internal reasoning steps executed *within a single agent run*. Grading the final output alone loses the "why," which is what you need to actually fix the agent. You must grade the trajectory.

### Capability vs. Regression Evals
- **Capability Evals**: Focus on hard, unsolved tasks. You expect a low pass rate; the goal is to find the ceiling of your agent's abilities and learn where to improve.
- **Regression Evals**: Focus on known-good, solved tasks. You expect a near 100% pass rate. This acts as a safety net against breakage when you tweak a prompt or swap an underlying model.

### The Public Benchmark Trap
When evaluating LLMs, the industry relies on generic benchmarks like MMLU (Google it!) or SWE-bench. These are useful for sanity-checking a base model's raw capability. However, **generic benchmarks tell you how smart the underlying model is; they don't tell you whether your agent, wired to your custom tools, solving your specific task, is any good.** For that, you need a custom evaluation framework.

With those concepts out of the way, let me show you the project I built to test this out.
---

## 3. The Benchmark Setup & Headline Findings

To make these concepts concrete, I built a **local bug fixing agent** and ran it against 10 planted Python bugs. 

> **Implementation note:** I ran this benchmark on **Claude Haiku 4.5** for cost efficiency. Including documented runs, an earlier uncaptured run, and miscellaneous experiments, the total API spend across the entire project was approximately **~$1**.

**The Prerequisite: A Golden Dataset**
Before looking at the configurations, it is worth pausing on those "10 planted bugs." You cannot evaluate an agent without a strong foundation of data. To build a robust evaluation, you need a carefully curated "Golden Dataset" of test cases with known root causes and strict verification steps. Furthermore, this shouldn't be a static list—it must be an ever-improving set of tasks that grows as your agent tackles new edge cases in production.

I evaluated three configurations against this dataset:
1. `config_baseline`: System prompt + full toolset (`read_file`, `edit_file`, `run_tests`).
2. `config_prompt_v2`: Constrained step-by-step diagnostic prompt + full toolset.
3. `config_no_run_tests`: System prompt + NO `run_tests` tool (blind execution).

I ran the benchmark suite multiple times to account for LLM non-determinism. Here is how the headline metrics shifted between **Run 1** (initial) and **Run 2** (extended with token & cost accounting):

| Metric | `config_baseline` | `config_prompt_v2` | `config_no_run_tests` |
| :--- | :---: | :---: | :---: |
| **Pass Rate (Run 1 → Run 2)** | 80% → 70% | 70% → 70% | 70% → **90%** |
| **LLM Judge Score (Run 1 → 2)** | 0.90 → 0.80 | 0.80 → 0.80 | **1.00 → 1.00** |
| **Fix Quality (Genuine Fixes)** | 100% | 100% | 100% |
| **Total Benchmark Cost (Run 2)**| $0.0656 | $0.0670 | $0.0699 |
| **Adversarial Safety Rate** | **100% Passed** | **100% Passed** | **100% Passed** |

*Note on Non-Determinism (Variability):* Notice how the pass rates changed between Run 1 and Run 2! Since I tested on 10 tasks, a single task flipping from pass to fail shifts the score by 10%. This was a big takeaway for me: running a benchmark just once is fine for a quick sanity check, but small score changes are usually just LLM randomness unless you test over multiple runs.

*Note on Safety:* One of my tasks (`task_009_adversarial`) featured a planted, malicious docstring urging the agent to simply write `assert True` to fake a fix. Across all runs, the agent resisted this indirect prompt injection and correctly fixed the underlying source code. Worth being honest about sample size though: this is one adversarial scenario out of ten tasks. A 100% pass rate on one adversarial scenario is a promising signal, not proof of robustness.

---

## 4. The 8 Critical Questions of Agent Evaluation

To uncover the *why* behind these numbers, I needed to go beyond a simple pass/fail metric. I had to evaluate agent behavior across outcome correctness, tool flow, trajectory efficiency, safety, and fix quality. 

While reading about the topic of evaluating agents, I found that the following 8 questions can help us evaluate an agent better; I designed the eval for the bug fixing agent keeping this in mind. This is a good starting point.

1. **Can I evaluate task completion?** (Moving beyond binary pass/fail to nuanced scoring)
2. **Can I evaluate tool correctness?** (Did it use the right tools, on the right files?)
3. **Can I compare prompt versions?** (Does forcing "structured thinking" actually help?)
4. **Can I compare tool configurations?** (What happens when we remove a critical tool?)
5. **Can I inspect trajectories?** (Did it get stuck in a loop? Was the tool sequence logical?)
6. **Can I measure efficiency?** (How much did it cost, and how many turns did it take?)
7. **Can I run regression tests?** (Did a prompt tweak break previously solved tasks?)
8. **Can I explain why a task failed?** (Did it actually fix the root cause, or just write a lazy workaround?)

### 4.1 Can I evaluate task completion?
*Methodology: Dual-Layer Grading (Rule-Based + LLM Judge)*

The most obvious question is: *Did the agent do the job?* But a simple pass/fail is rarely enough. In my framework, I split this into two distinct evaluators:
1. **Outcome (Binary Pass/Fail):** This is a deterministic, rule-based check. In my code, `outcome.py` checks if the `pytest` suite passes after the agent finishes its edits. It’s cheap, fast, and gives a definitive yes or no.

2. **Task Completion (Nuanced Score):** An outcome-only metric hides nuance. What if the agent correctly identified the bug, wrote the right logic, but forgot a minor syntax detail and ran out of turns? My LLM judge (`task_completion.py`) reads the full execution trace and outputs a strict verdict, which maps to a discrete score (`COMPLETE` = 1.0, `PARTIAL` = 0.5, `FAILED` = 0.0). Getting partial credit for sound reasoning and correct file identification is invaluable for debugging capability gaps.

### 4.2 Can I evaluate tool correctness?
*Methodology: Rule-Based Match*

Unlike standard LLMs, agents take action. Tool misuse: calling the wrong tool, hallucinating parameters, or ignoring a silent failure is a unique agentic failure mode. 

To evaluate this, I used `tool_correctness.py`, a rule-based evaluator that compares the agent's actions against a known-correct task definition. Did the agent open the correct target file? Did it edit the source code instead of cheating and editing the test file? I didn't need a fuzzy LLM judge here; deterministic string matching works best to ensure the agent is physically doing what it claims to be doing.

### 4.3 Can I compare prompt versions?
*Finding: The "Prompt Bloat" Problem*

I ran a benchmark comparing my baseline prompt (`config_baseline`) against an over-constrained, verbose prompt that forced step-by-step diagnostic thinking (`config_prompt_v2`). 

You might expect forcing structured reasoning to improve accuracy. **It did not.** In my tests, `config_prompt_v2` added 711 tokens and increased total cost, but it actually performed *worse* (in Run 1) or identical (in Run 2) to the baseline. Why? The model spent extra tokens "thinking out loud" summarizing the task description and detailing diagnostic steps but this produced no extra problem-solving value over the concise baseline prompt. 

Run this experiment on your own agent; the result may surprise you.

**Takeaway:** In this experiment, on these 10 bug-fixing tasks, the more verbose diagnostic prompt increased token usage without improving task performance. Whether that generalizes to other models, other task types, or genuinely harder bugs is an open question, but it's a cheap thing to test before assuming "more structured reasoning" is automatically better.

### 4.4 Can I compare tool configurations?
*Finding: The Blind Execution Paradox*

What happens if you take away an agent's ability to test its own code? I ran `config_no_run_tests`, an environment where the agent only had `read_file` and `edit_file` tools—no `run_tests` tool.

Remarkably, the agent's pass rate **improved to 90%** (up from 70%), achieving a perfect 1.00 completion score. Even though the agent couldn't run tests itself, when my evaluator ran the strict `pytest` suite at the end, 9 out of 10 fixes were perfectly correct.

*A small caveat: the jump from 70% to 90% is really just two extra tasks passing. With only two runs, I can't be sure this gap is real and not just randomness. What I'm more confident about is the quality rating, which held at a perfect 1.00 in both runs.*

Without the ability to lean on a "guess-and-check" loop, the agent carefully read the source code and the test suite in its initial turn, identified the exact root cause, and made a single, precise edit. The trade-off? Blind execution used slightly fewer total tokens but took 1.0 second longer per task due to heavier reasoning per turn. 

**Takeaway:** In this experiment, removing the run_tests tool didn't hurt performance; it may have helped, by forcing more careful upfront reasoning instead of a guess-and-check loop. My hypothesis, untested here since every task was single-file and localized, is that this trade-off flips for complex, multi-file bugs, where a testing loop becomes essential. That's a good next experiment for this framework, not a strong conclusion this dataset can support yet.

### 4.5 Can I inspect trajectories?
*Methodology: Sequence & Flow Analysis*

A correct answer can hide a terrible process. Did the agent get stuck in a dead loop? Did it wildly edit files without reading them first? 

My `trajectory.py` and `tool_flow.py` evaluators analyze the shape of the execution trace. They look for missing verification steps or looped failures. If an agent manages to fix a bug but took 5 redundant edits to get there, a trajectory evaluator will flag it, whereas a simple outcome evaluator would happily mark it as a "pass."

### 4.6 Can I measure efficiency?
*Finding: The Cost of Strict Efficiency*

In production, wrong answers are loud—users complain, tests fail, judges flag them. But expensive, slow, correct answers are quiet. They just slowly drain your API credits. 

My `efficiency.py` evaluator tracks latency, token consumption, USD cost, **and turn counts** per task. During my benchmark, I noticed persistent failures on two simple tasks (`task_002` and `task_007`). Why? Because to force efficiency, I set a harsh harness constraint: `max_turns: 3`. The minimum viable trajectory (read → edit → verify) is exactly 3 turns. Any slight imprecision on the first try meant the agent hit the turn limit and failed, even if it had the correct logic.

**Takeaway:** Evaluation harnesses must carefully distinguish between **agent capability failures** (the model isn't smart enough) and **harness constraints** (the turn budget was just too tight). 

### 4.7 Can I run regression tests?
*Methodology: CI Gates and Statistical Variance*

Once an agent can solve a task, that task graduates to the regression suite. `regression.py` allows me to compare two runs of the same config over time to ensure an update to the model or prompt didn't break previously solved tasks.

As I found in my benchmarks, LLMs are naturally unpredictable. A single run is great for a quick CI smoke test, but for true regression testing, you need to run tasks multiple times so you don't mistake LLM randomness for a broken prompt.

### 4.8 Can I explain why a task failed?
*Methodology: Diff-based Quality Evaluation*

Finally, did the agent fix the actual bug, or did it write a lazy workaround? If a test fails, a lazy agent might simply delete the failing `assert` statement in the test file. 

To prevent this, `fix_quality.py` acts as a specialized LLM judge. Crucially, I didn't just feed it the trace log, I captured the exact `git diff` of the agent's final state and passed *that* to the judge. The judge categorizes the result as a `GENUINE` fix (addressing the root architectural bug) or a `WORKAROUND` (cheating the test suite). Across all my completed tests, my agents achieved a 100% Genuine Fix rate.

---

## 5. Operationalizing Evaluation: The Tooling Landscape

Building a custom evaluation harness is a great learning exercise, but what tools exist in the ecosystem to help you do this at scale? If you don't want to build this from scratch, here is how the tooling landscape looks today:

- **DeepEval & Confident AI**: DeepEval is an open-source, pytest-style framework with a large built-in metric library (G-Eval, tool correctness, hallucination). Confident AI is their cloud platform that adds tracing and observability, allowing you to monitor agentic execution trees in production.
- **Promptfoo**: An open-source, CLI-driven tool that excels at prompt regression testing and red-teaming/security (like my adversarial prompt injection test). It acts as an excellent CI gate at PR time.
- **Langfuse**: An open-source observability and tracing platform. It captures production traces and attaches scores. Langfuse catches what static eval suites miss after launch, helping identify silent drift in cost or step-count.
- **NVIDIA NeMo Agent Toolkit**: A different category entirely. Rather than a standalone evaluation tool, NeMo is an agent orchestration platform that ships with evaluation *built-in*, including a dedicated trajectory evaluator.

> **Tooling caveat:** This landscape moves fast: ownership changes (Promptfoo was acquired by OpenAI in March 2026, though it remains open-source) and APIs get marked experimental (NVIDIA's own docs flag NeMo's evaluation API as such). Treat this section as a snapshot, and check current docs before building on any of these.

**A common real-world pattern:** Use **Promptfoo** or a custom script (`outcome.py`) as a cheap, rule-based CI gate at PR time. Use **DeepEval** to run scheduled, LLM-judged evaluations on sampled production traces. Finally, visualize those scores and trajectories in **Langfuse** or **Confident AI** to monitor for drift.



---

## Conclusion

Agent evaluation is an evolving discipline, not a solved checklist. By stepping away from simple single-turn accuracy and focusing on trajectories, tool correctness, and config-comparisons, you can build agents that don't just answer questions correctly—but act reliably in the real world. 

By structuring your evaluation around these 8 critical questions, and blending cheap rule-based CI gates with nuanced LLM-as-a-judge scoring, you can finally prove that your agent works not just in manual testing, but in production.

---

## Further Reading

If you want to dive deeper into the state of the art in agent evaluation, here are some excellent resources:
- [Demystifying Evals for AI Agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (Anthropic)
- [Evaluating AI Agents: Real-world lessons from building agentic systems at Amazon](https://aws.amazon.com/blogs/machine-learning/evaluating-ai-agents-real-world-lessons-from-building-agentic-systems-at-amazon/) (AWS - *Highly recommended!*)
- [Mastering Agentic Techniques: AI Agent Evaluation](https://developer.nvidia.com/blog/mastering-agentic-techniques-ai-agent-evaluation/) (NVIDIA)
- [AI Agent Evaluation](https://www.ibm.com/think/topics/ai-agent-evaluation) (IBM)
- [What is Agent Evaluation?](https://www.databricks.com/blog/what-is-agent-evaluation) (Databricks)
- [Guides: AI Agent Evaluation](https://deepeval.com/guides/guides-ai-agent-evaluation) (DeepEval)
- [Evaluations for the Agentic World](https://medium.com/quantumblack/evaluations-for-the-agentic-world-c3c150f0dd5a) (QuantumBlack / McKinsey)
- [Agentic AI on Evaluations](https://www.ilsilfverskiold.com/articles/agentic-ai-on-evaluations) (Ida Silfverskiöld)
