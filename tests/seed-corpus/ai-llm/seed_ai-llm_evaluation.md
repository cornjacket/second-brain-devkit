---
tags: [seed, ai-llm]
---

# Evaluating LLM output

Evaluating generative output is hard because open-ended completions rarely have one gold answer, so n-gram overlap metrics like BLEU and ROUGE correlate weakly with quality. Intrinsic measures such as perplexity report how surprised the model is by held-out tokens but say nothing about factuality or instruction-following. Practical evals lean on standardized benchmarks — MMLU, HellaSwag, GSM8K, TruthfulQA, HumanEval — alongside human preference rating and LLM-as-judge panels that score responses against a rubric, though judges carry position and verbosity biases that must be controlled with pairwise comparisons. A curated, labeled eval set with clear rubrics turns silent regressions into measurable deltas across checkpoints and prompt revisions. Adversarial red-team cases and out-of-distribution inputs expose failure modes that averaged leaderboard scores mask, and contamination checks guard against benchmark answers leaking into the pretraining corpus.
