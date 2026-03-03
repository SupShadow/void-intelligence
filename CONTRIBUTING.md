# Contributing to VOID Intelligence

## The Short Version

1. Fork it
2. `pip install -e .`
3. Make your change
4. `void test` — all 30 checks must pass
5. PR with a clear description

## What We Value

**Small, focused PRs.** One change per PR. If your PR does two things, split it.

**Zero dependencies.** VOID core uses only Python stdlib. If your feature needs `numpy` or `requests`, it belongs in an optional extra, not core.

**Measured, not assumed.** Every claim about model behavior should be backed by `void benchmark` data. "I think model X is better" is not enough. "Model X has R=0.47 vs Y's R=0.12" is.

**The multiplicative formula is sacred.** V = E x W x S x B x H x R. One zero kills the product. This is by design. Don't suggest making it additive.

## What We're Looking For

- **New V-Score profiles** — Run `void benchmark` on models we haven't tested. Submit the JSON.
- **Better HexBreath keywords** — The 6-axis classifier uses keyword matching. More keywords = better accuracy.
- **Model adapters** — Wrap your favorite LLM provider as a `ModelCallable = (prompt, system) -> str`.
- **Bug fixes** — Especially in state persistence and profile scoring.
- **Examples** — Real-world use cases in `examples/`.

## What We Don't Want

- Features that add runtime dependencies to core
- "Improvements" that make the API surface larger without clear benefit
- Benchmark results without the methodology to reproduce them
- AI-generated PRs that don't pass `void test`

## Running Tests

```bash
# Quick — 30 self-checks
void test

# Or via python
python3 -m void_intelligence.cli test
```

## Code Style

- Type hints everywhere
- Docstrings on public functions
- No comments that restate the code — only explain *why*

## License

By contributing, you agree that your contributions will be licensed under MIT.
