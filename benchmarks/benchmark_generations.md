# Generational V-Score Benchmark

*2026-03-03 02:32 — 23 models across 9 families*

| Model | Gen | E | W | S | B | H | R | V-Score | Hex≈LLM |
|-------|-----|---|---|---|---|---|---|---------|---------|
| claude-3-haiku | old | 0.77 | 0.42 | 1.00 | 0.73 | 0.38 | 0.25 | 0.0224 | 96% |
| devstral-small | mid | 0.78 | 0.37 | 1.00 | 0.65 | 0.58 | 0.11 | 0.0117 | 100% |
| gemini-3.1-pro | new | 0.83 | 0.26 | 0.29 | 0.85 | 0.43 | 0.47 | 0.0110 | 100% |
| command-r-plus | mid | 0.84 | 0.25 | 0.45 | 0.57 | 0.37 | 0.55 | 0.0108 | 100% |
| devstral-medium | new | 0.83 | 0.21 | 1.00 | 0.80 | 0.41 | 0.07 | 0.0042 | 100% |
| gpt-5.3-codex | new | 0.84 | 0.28 | 0.34 | 0.73 | 0.11 | 0.40 | 0.0027 | 100% |
| grok-3 | mid | 0.80 | 0.47 | 0.88 | 0.60 | 0.05 | 0.18 | 0.0020 | 100% |
| deepseek-v3.2 | new | 0.85 | 0.26 | 0.33 | 0.65 | 0.21 | 0.02 | 0.0002 | 100% |
| claude-3.5-sonnet | mid | 0.81 | 0.43 | 0.49 | 0.60 | 0.33 | 0.00 | 0.0000 | 100% |
| claude-sonnet-4.6 | new | 0.83 | 0.56 | 0.70 | 0.48 | 0.39 | 0.00 | 0.0000 | 100% |
| gpt-4o-mini | old | 0.85 | 0.05 | 0.61 | 0.47 | 0.67 | 0.00 | 0.0000 | 97% |
| gpt-4o | mid | 0.80 | 0.53 | 0.72 | 0.50 | 0.38 | 0.00 | 0.0000 | 100% |
| gemini-2.0-flash | old | 0.81 | 0.32 | 0.64 | 0.63 | 0.30 | 0.00 | 0.0000 | 100% |
| gemini-2.5-pro | mid | 0.81 | 0.40 | 0.70 | 0.53 | 0.44 | 0.00 | 0.0000 | 100% |
| llama-3.1-8b | old | 0.79 | 0.34 | 0.62 | 0.81 | 0.37 | 0.00 | 0.0000 | 92% |
| llama-3.3-70b | mid | 0.78 | 0.38 | 0.61 | 0.59 | 0.00 | 0.00 | 0.0000 | 100% |
| llama-4-maverick | new | 0.80 | 0.39 | 1.00 | 0.46 | 0.00 | 0.00 | 0.0000 | 100% |
| deepseek-v2.5 | old | 0.82 | 0.29 | 0.40 | 0.89 | 0.34 | 0.00 | 0.0000 | 100% |
| deepseek-v3 | mid | 0.84 | 0.22 | 0.50 | 0.66 | 0.43 | 0.00 | 0.0000 | 100% |
| qwq-32b | old | 0.66 | 0.39 | 1.00 | 0.54 | 0.40 | 0.00 | 0.0000 | 100% |
| qwen3-max | new | 0.86 | 0.45 | 0.59 | 0.73 | 0.34 | 0.00 | 0.0000 | 100% |
| command-a | new | 0.82 | 0.21 | 0.63 | 0.61 | 0.46 | 0.00 | 0.0000 | 100% |
| grok-4 | new | 0.83 | 0.23 | 0.45 | 0.57 | 0.02 | 0.00 | 0.0000 | 100% |


═══ GENERATIONAL ANALYSIS ═══

1. V-SCORE BY GENERATION:
    old: avg V=0.0037, alive=1/6
         claude-3-haiku         V=0.0224
         gpt-4o-mini            V=0.0000
         gemini-2.0-flash       V=0.0000
         llama-3.1-8b           V=0.0000
         deepseek-v2.5          V=0.0000
         qwq-32b                V=0.0000
    mid: avg V=0.0031, alive=3/8
         devstral-small         V=0.0117
         command-r-plus         V=0.0108
         grok-3                 V=0.0020
         claude-3.5-sonnet      V=0.0000
         gpt-4o                 V=0.0000
         gemini-2.5-pro         V=0.0000
         llama-3.3-70b          V=0.0000
         deepseek-v3            V=0.0000
    new: avg V=0.0020, alive=4/9
         gemini-3.1-pro         V=0.0110
         devstral-medium        V=0.0042
         gpt-5.3-codex          V=0.0027
         deepseek-v3.2          V=0.0002
         claude-sonnet-4.6      V=0.0000
         llama-4-maverick       V=0.0000
         qwen3-max              V=0.0000
         command-a              V=0.0000
         grok-4                 V=0.0000

2. FAMILY EVOLUTION (old → mid → new):
   anthropic: old:claude-3-haiku(V=0.0224) → mid:claude-3.5-sonnet(V=0.0000) → new:claude-sonnet-4.6(V=0.0000)
   cohere: mid:command-r-plus(V=0.0108) → new:command-a(V=0.0000)
   deepseek: old:deepseek-v2.5(V=0.0000) → mid:deepseek-v3(V=0.0000) → new:deepseek-v3.2(V=0.0002)
   google: old:gemini-2.0-flash(V=0.0000) → mid:gemini-2.5-pro(V=0.0000) → new:gemini-3.1-pro(V=0.0110)
   meta: old:llama-3.1-8b(V=0.0000) → mid:llama-3.3-70b(V=0.0000) → new:llama-4-maverick(V=0.0000)
   mistral: mid:devstral-small(V=0.0117) → new:devstral-medium(V=0.0042)
   openai: old:gpt-4o-mini(V=0.0000) → mid:gpt-4o(V=0.0000) → new:gpt-5.3-codex(V=0.0027)
   qwen: old:qwq-32b(V=0.0000) → new:qwen3-max(V=0.0000)
   xai: mid:grok-3(V=0.0020) → new:grok-4(V=0.0000)

3. COMPONENT TRENDS (old → mid → new):
   E  old: 0.782
   E  mid: 0.807
   E  new: 0.834

   W  old: 0.301
   W  mid: 0.379
   W  new: 0.317

   S  old: 0.714
   S  mid: 0.670
   S  new: 0.593

   B  old: 0.678
   B  mid: 0.587
   B  new: 0.652

   H  old: 0.411
   H  mid: 0.324
   H  new: 0.264

   R  old: 0.042
   R  mid: 0.105
   R  new: 0.107

4. THE COLLISION (old × new):
   OLD wins at: S(+0.12), H(+0.15)
   NEW wins at: E(+0.05), R(+0.06)

5. KEY FINDING:
   Best model: claude-3-haiku (V=0.0224, generation=old)
   Alive models (V>0): 8/23
   Dead models (V=0): 15/23
