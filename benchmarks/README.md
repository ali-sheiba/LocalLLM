# Benchmarking

How we evaluate stack configurations and track which performs best.

## Scoring Categories

Each stack is scored across these dimensions:

| Category | Weight | Description |
|---|---|---|
| **Tool Calling** | High | Ability to parse and execute tool calls correctly |
| **Instruction Following** | High | Adherence to complex instructions and constraints |
| **Structural Output** | High | Producing valid JSON, XML, markdown tables, etc. |
| **Data Extraction** | Medium | Extracting structured data from unstructured text |
| **Reasoning / Math** | Medium | Logical reasoning and computation |
| **Bug Finding** | Medium | Identifying issues in code |
| **Coding (aider)** | High | Real-world coding tasks via aider benchmarks |
| **Context Utilization** | Medium | Effectiveness with long context windows |

## Running Benchmarks

1. Start the stack you want to evaluate
2. Run the benchmark suite (see `scripts/` for automated runs)
3. Save results to `benchmarks/results/<stack-name>-<date>.md`
4. Update `benchmarks/scoring.md` with the scores

## Result Format

```markdown
## <Stack Name> — <Date>

- Engine: <vLLM / llama.cpp>
- Model: <model name>
- Quantization: <quant>
- Context: <size>
- Config: <key deviations from default>

### Scores

| Category | Score | Max |
|---|---|---|
| Tool Calling | X | 20 |
| ... | ... | ... |
| **Total** | X | 150 |
```