# Benchmark Scoring

`benchmarks/INDEX.md` is the generated current index for all recorded runs.

This file is retained as a migration pointer for the former manual 150-point scorecard. LocalLLM now records the native `tool-eval-bench` quality score, category scores, completion rate, safety warnings, and the c1/c2 throughput matrix in each immutable run directory.

Do not maintain a separate manual global leaderboard. A meaningful comparison requires matching benchmark protocol, model/stack configuration, hardware, and power conditions. Use `benchmarks/comparisons/` for evidence-based comparisons between compatible runs.
