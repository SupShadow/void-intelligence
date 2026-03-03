# VOID Intelligence vs. Alternatives

## The Landscape

| Feature | VOID | LangChain | LlamaIndex | Raw LLM API |
|---------|:----:|:---------:|:----------:|:-----------:|
| **Zero dependencies** | yes | no (50+) | no (30+) | yes |
| **Input classification** | yes (<0.02ms) | no | no | no |
| **Experience memory** | yes (growth rings) | partial (memory modules) | partial (indices) | no |
| **Model routing by learning ability** | yes (V-Score) | no | no | no |
| **Measures model adaptiveness** | yes (V = ExWxSxBxHxR) | no | no | no |
| **State survives model swap** | yes | no | no | no |
| **Local-first** | yes | no | no | varies |
| **Bundle size** | ~100KB | ~50MB | ~30MB | n/a |
| **Setup time** | `pip install` + 3 lines | hours | hours | minutes |

## Different Problems, Different Tools

**LangChain** solves orchestration — chaining LLM calls, tools, and agents. It's plumbing. Big, flexible, lots of dependencies.

**LlamaIndex** solves retrieval — connecting LLMs to your data via indices and embeddings. It's a search engine for your documents.

**VOID Intelligence** solves *adaptiveness* — making any LLM learn from use. It's an organism layer. Wraps your existing stack. Zero dependencies.

These are not competing tools. You can use VOID *inside* a LangChain chain or *around* a LlamaIndex query.

## The Core Difference

LangChain and LlamaIndex assume all LLMs are interchangeable. VOID measures that they're not.

```
65% of frontier models are DEAD (V=0).
They ignore context injection and start from zero every call.
V-Score proves it. The multiplicative formula is brutally honest.
```

Running the same prompt through the same model via different access paths (direct API vs. Ollama vs. OpenRouter) produces different V-Scores. **The wrapper matters as much as the model.**

## When to Use VOID

- You want your LLM to get better with every interaction (not just RAG lookup)
- You want to measure which model actually learns (not trust benchmarks)
- You need input classification without an LLM call (HexBreath: <0.02ms)
- You want zero dependencies and local-first operation
- You're fine-tuning and need to find the sweet spot (delta_opt)

## When NOT to Use VOID

- You need document retrieval/RAG (use LlamaIndex)
- You need complex multi-step agent chains (use LangChain)
- You need function calling / tool use (use your LLM's native API)
- You need embeddings or vector search (use ChromaDB, pgvector, etc.)

VOID is the organism layer. It wraps everything else.
