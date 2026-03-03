# Benchmarks

Raw V-Score benchmark data from March 2026.

## Files

| File | What | Models |
|------|------|--------|
| `benchmark_results.json` | Original API benchmark | 6 models via direct API |
| `benchmark_generations.json` | Cross-generation benchmark | 23 models via OpenRouter |
| `benchmark_cli_results.json` | Local CLI benchmark | 12 models via Ollama |
| `benchmark_frontier_2026.json` | Frontier subset | Top performers March 2026 |

## Running Your Own

```bash
# Full benchmark (needs API keys in .env)
void benchmark

# Local models only (no API keys needed)
void benchmark --local

# Single model
void benchmark qwen3-14b
```

## Scripts

- `benchmark_cli.py` — CLI/Ollama benchmark runner
- `benchmark_generations.py` — OpenRouter cross-generation benchmark

## Submitting Results

Found a model we haven't tested? Run `void benchmark` and submit via GitHub issue using the "Benchmark Submission" template.
