"""
thought_volume.py --- Measure the volume of a sphere of thoughts.

The industry measures models by accuracy. We measure the SPACE BETWEEN them.

V = sqrt(det(G)) where G is the Gram matrix of embedding similarities.
- det(G) = 0: All models say the same thing. Consensus collapse. Death.
- det(G) ~ 1: Maximum divergence. Every thought orthogonal. Pure [].

Betti numbers measure the HOLES --- what NO model thought of.
The volume measures x. The holes measure [].

Usage:
    from void_intelligence.thought_volume import ThoughtSphere, measure_volume

    sphere = ThoughtSphere()
    sphere.add("Model A response about consciousness...")
    sphere.add("Model B response about consciousness...")
    sphere.add("Model C response about consciousness...")

    result = sphere.measure()
    print(result.volume)        # sqrt(det(G)) --- the x between all thoughts
    print(result.distances)     # pairwise distances --- each collision
    print(result.richest_pair)  # highest distance pair --- strongest x
    print(result.blindspot)     # what dimension has least coverage --- []
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# --- Lightweight embedding (zero deps, works everywhere) ---

def _char_frequencies(text: str, dims: int = 64) -> list[float]:
    """Character n-gram frequency embedding. No model needed. Captures texture."""
    text = text.lower().strip()
    vec = [0.0] * dims
    if not text:
        return vec

    # Unigrams (first 26 dims)
    for ch in text:
        idx = ord(ch) % min(dims, 26)
        vec[idx] += 1.0

    # Bigrams (next dims)
    for i in range(len(text) - 1):
        bigram = text[i:i+2]
        idx = 26 + (hash(bigram) % (dims - 26))
        vec[idx] += 1.0

    # Normalize
    magnitude = math.sqrt(sum(v * v for v in vec))
    if magnitude > 0:
        vec = [v / magnitude for v in vec]

    return vec


def _semantic_features(text: str) -> list[float]:
    """Extract semantic features that capture MEANING, not just characters.

    24 dimensions:
    - Vocabulary richness, sentence complexity, question density
    - Emotional valence, abstraction level, specificity
    - Domain markers (science, philosophy, emotion, technical, nature, social)
    - Structural features (lists, examples, reasoning chains)
    """
    words = text.lower().split()
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    n_words = max(len(words), 1)
    n_sentences = max(len(sentences), 1)

    unique_words = len(set(words))

    features = [
        # Vocabulary & complexity (4)
        unique_words / n_words,                                          # vocab richness
        sum(len(w) for w in words) / n_words / 10,                       # avg word length
        n_words / n_sentences / 30,                                      # sentence length
        len([w for w in words if len(w) > 8]) / n_words,                 # long word ratio

        # Questions & engagement (2)
        text.count('?') / n_sentences,                                   # question density
        text.count('!') / n_sentences,                                   # emphasis density

        # Emotional valence (3)
        len([w for w in words if w in _WARM_WORDS]) / n_words,           # warmth
        len([w for w in words if w in _COLD_WORDS]) / n_words,           # analytical
        len([w for w in words if w in _DEEP_WORDS]) / n_words,           # depth

        # Abstraction (3)
        len([w for w in words if w in _ABSTRACT]) / n_words,             # abstract
        len([w for w in words if w in _CONCRETE]) / n_words,             # concrete
        len([w for w in words if w[0].isupper()]) / n_words if words else 0,  # proper nouns

        # Domain markers (6)
        len([w for w in words if w in _SCIENCE]) / n_words,
        len([w for w in words if w in _PHILOSOPHY]) / n_words,
        len([w for w in words if w in _EMOTION]) / n_words,
        len([w for w in words if w in _TECHNICAL]) / n_words,
        len([w for w in words if w in _NATURE]) / n_words,
        len([w for w in words if w in _SOCIAL]) / n_words,

        # Structure (4)
        text.count('\n') / n_sentences,                                  # paragraph breaks
        len(re.findall(r'\d+[.)]', text)) / n_sentences,                 # numbered lists
        len(re.findall(r'for example|e\.g\.|z\.b\.|beispiel|instance', text.lower())) / n_sentences,
        len(re.findall(r'because|therefore|thus|weil|deshalb|daher', text.lower())) / n_sentences,

        # Meta (2)
        len(text) / 5000,                                                # length signal
        len(set(text.lower().split())) / max(len(text.lower().split()), 1),  # diversity
    ]

    return features


# Word sets for semantic features
_WARM_WORDS = {'love', 'liebe', 'feel', 'heart', 'warm', 'care', 'kind', 'beautiful',
               'gentle', 'hope', 'trust', 'vertrauen', 'herz', 'freude', 'glueck'}
_COLD_WORDS = {'analyze', 'calculate', 'measure', 'system', 'optimize', 'efficient',
               'function', 'parameter', 'algorithm', 'compute', 'metric', 'data'}
_DEEP_WORDS = {'consciousness', 'existence', 'meaning', 'truth', 'reality', 'paradox',
               'bewusstsein', 'existenz', 'wahrheit', 'fundamental', 'emerge', 'infinite'}
_ABSTRACT = {'concept', 'principle', 'theory', 'abstract', 'universal', 'meta',
             'paradigm', 'framework', 'pattern', 'resonance', 'dimension'}
_CONCRETE = {'hand', 'table', 'walk', 'eat', 'build', 'write', 'see', 'touch',
             'house', 'door', 'road', 'tree', 'water', 'stone', 'body'}
_SCIENCE = {'energy', 'quantum', 'entropy', 'frequency', 'field', 'atom',
            'molecule', 'force', 'wave', 'particle', 'equation', 'physics'}
_PHILOSOPHY = {'consciousness', 'being', 'existence', 'truth', 'knowledge',
               'epistemology', 'ontology', 'goedel', 'paradox', 'dialectic'}
_EMOTION = {'love', 'fear', 'joy', 'anger', 'hope', 'grief', 'wonder',
            'liebe', 'angst', 'freude', 'trauer', 'hoffnung', 'staunen'}
_TECHNICAL = {'code', 'function', 'api', 'server', 'database', 'algorithm',
              'deploy', 'module', 'class', 'method', 'runtime', 'compile'}
_NATURE = {'tree', 'river', 'mountain', 'ocean', 'rain', 'sun', 'wind',
           'forest', 'flower', 'earth', 'sky', 'seed', 'grow', 'bloom'}
_SOCIAL = {'community', 'together', 'society', 'people', 'family', 'friend',
           'gemeinschaft', 'zusammen', 'gesellschaft', 'mensch', 'familie'}


def _word_hash_vec(text: str, dims: int = 128) -> list[float]:
    """Hash each word into a fixed-dim vector. Captures vocabulary, not character shape."""
    words = re.findall(r'\b\w+\b', text.lower())
    vec = [0.0] * dims
    for w in words:
        # Hash each word to multiple dims (simulates sparse embedding)
        h1 = hash(w) % dims
        h2 = hash(w + "_2") % dims
        h3 = hash(w + "_3") % dims
        vec[h1] += 1.0
        vec[h2] += 0.5
        vec[h3] += 0.25
    # L2 normalize
    mag = math.sqrt(sum(v * v for v in vec))
    if mag > 0:
        vec = [v / mag for v in vec]
    return vec


def embed(text: str) -> list[float]:
    """Create embedding from text. Zero deps. Word-hash + semantic features.

    Prioritizes MEANING over character shape:
    - Word hashing captures vocabulary and topic (128 dims)
    - Semantic features capture texture and style (24 dims)
    - Character frequencies downweighted (32 dims)
    """
    word_vec = _word_hash_vec(text, dims=128)
    sem_vec = _semantic_features(text)
    char_vec = _char_frequencies(text, dims=32)
    combined = word_vec + sem_vec + char_vec
    # L2 normalize
    mag = math.sqrt(sum(v * v for v in combined))
    if mag > 0:
        combined = [v / mag for v in combined]
    return combined


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def gram_matrix(vectors: list[list[float]]) -> list[list[float]]:
    """Build Gram matrix G where G_ij = dot(v_i, v_j)."""
    n = len(vectors)
    G = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            G[i][j] = sum(a * b for a, b in zip(vectors[i], vectors[j]))
    return G


def determinant(matrix: list[list[float]]) -> float:
    """Compute determinant via LU decomposition. Pure Python, no numpy."""
    n = len(matrix)
    if n == 0:
        return 0.0
    if n == 1:
        return matrix[0][0]
    if n == 2:
        return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]

    # LU decomposition with partial pivoting
    M = [row[:] for row in matrix]  # copy
    sign = 1.0

    for col in range(n):
        # Pivot
        max_row = col
        max_val = abs(M[col][col])
        for row in range(col + 1, n):
            if abs(M[row][col]) > max_val:
                max_val = abs(M[row][col])
                max_row = row
        if max_row != col:
            M[col], M[max_row] = M[max_row], M[col]
            sign *= -1.0

        if abs(M[col][col]) < 1e-12:
            return 0.0

        for row in range(col + 1, n):
            factor = M[row][col] / M[col][col]
            for k in range(col, n):
                M[row][k] -= factor * M[col][k]

    det_val = sign
    for i in range(n):
        det_val *= M[i][i]

    return det_val


# --- ThoughtSphere ---

@dataclass
class ThoughtMeasurement:
    """The measurement of a sphere of thoughts."""
    volume: float                    # sqrt(det(G)) --- the total x
    det_g: float                     # raw determinant
    n_thoughts: int                  # number of points on the sphere
    n_collisions: int                # N(N-1)/2
    distances: list[tuple[int, int, float]]  # pairwise cosine distances
    richest_pair: tuple[int, int, float]     # strongest x (most different)
    weakest_pair: tuple[int, int, float]     # weakest x (most similar)
    blindspot_dims: list[int]        # dimensions with least coverage
    diversity_score: float           # 0-1, overall diversity
    alive: bool                      # is the sphere alive?

    def narrative(self) -> str:
        """Human-readable narrative of the measurement."""
        if self.n_thoughts < 2:
            return "One thought alone is silence. Add another for x."

        status = "THRIVING" if self.alive else "DORMANT"
        lines = [
            f"Thought Sphere: {self.n_thoughts} thoughts, {self.n_collisions} collisions",
            f"Volume: {self.volume:.4f} (det(G) = {self.det_g:.6f})",
            f"Diversity: {self.diversity_score:.1%}",
            f"Status: {status}",
            f"",
            f"Strongest x: thoughts {self.richest_pair[0]+1} and {self.richest_pair[1]+1} "
            f"(distance {self.richest_pair[2]:.3f})",
            f"Weakest x: thoughts {self.weakest_pair[0]+1} and {self.weakest_pair[1]+1} "
            f"(distance {self.weakest_pair[2]:.3f})",
        ]

        if self.volume < 0.001:
            lines.append("\nAll thoughts converge. The sphere has collapsed.")
            lines.append("Add a thought from a different domain, language, or perspective.")
        elif self.volume > 0.5:
            lines.append("\nThe sphere is vast. Rich []. Discovery lives here.")

        return "\n".join(lines)


class ThoughtSphere:
    """A sphere of thoughts. Add responses, measure the volume between them."""

    def __init__(self):
        self.thoughts: list[str] = []
        self.labels: list[str] = []
        self._embeddings: list[list[float]] = []

    def add(self, text: str, label: str = "") -> int:
        """Add a thought to the sphere. Returns index."""
        self.thoughts.append(text)
        self.labels.append(label or f"thought_{len(self.thoughts)}")
        self._embeddings.append(embed(text))
        return len(self.thoughts) - 1

    def measure(self) -> ThoughtMeasurement:
        """Measure the volume of the sphere. The x between all thoughts."""
        n = len(self.thoughts)

        if n < 2:
            return ThoughtMeasurement(
                volume=0.0, det_g=0.0, n_thoughts=n, n_collisions=0,
                distances=[], richest_pair=(0, 0, 0.0), weakest_pair=(0, 0, 0.0),
                blindspot_dims=[], diversity_score=0.0, alive=False,
            )

        # Gram matrix
        G = gram_matrix(self._embeddings)
        det_g = determinant(G)
        volume = math.sqrt(max(det_g, 0.0))

        # Pairwise distances (1 - cosine_similarity)
        distances = []
        for i in range(n):
            for j in range(i + 1, n):
                sim = cosine_similarity(self._embeddings[i], self._embeddings[j])
                dist = 1.0 - sim
                distances.append((i, j, dist))

        distances.sort(key=lambda x: x[2], reverse=True)
        richest = distances[0] if distances else (0, 0, 0.0)
        weakest = distances[-1] if distances else (0, 0, 0.0)

        # Diversity score: average pairwise distance
        avg_dist = sum(d[2] for d in distances) / len(distances) if distances else 0.0
        diversity = min(avg_dist * 2, 1.0)  # scale to 0-1

        # Blindspot detection: which embedding dimensions have least variance?
        dims = len(self._embeddings[0]) if self._embeddings else 0
        dim_variances = []
        for d in range(dims):
            values = [e[d] for e in self._embeddings]
            mean = sum(values) / n
            var = sum((v - mean) ** 2 for v in values) / n
            dim_variances.append((d, var))
        dim_variances.sort(key=lambda x: x[1])
        blindspot_dims = [d for d, v in dim_variances[:5]]  # top 5 blind dimensions

        alive = volume > 0.001 and diversity > 0.1

        return ThoughtMeasurement(
            volume=volume,
            det_g=det_g,
            n_thoughts=n,
            n_collisions=n * (n - 1) // 2,
            distances=distances,
            richest_pair=richest,
            weakest_pair=weakest,
            blindspot_dims=blindspot_dims,
            diversity_score=diversity,
            alive=alive,
        )

    def collide_with(self, other: "ThoughtSphere") -> ThoughtMeasurement:
        """Collide two spheres. The x of x."""
        merged = ThoughtSphere()
        for t, l in zip(self.thoughts, self.labels):
            merged.add(t, f"A:{l}")
        for t, l in zip(other.thoughts, other.labels):
            merged.add(t, f"B:{l}")
        return merged.measure()


def measure_volume(responses: list[str], labels: list[str] | None = None) -> ThoughtMeasurement:
    """Quick measurement. Give it N responses, get the volume between them."""
    sphere = ThoughtSphere()
    for i, resp in enumerate(responses):
        label = labels[i] if labels and i < len(labels) else ""
        sphere.add(resp, label)
    return sphere.measure()


def demo():
    """Show it working."""
    print("=== THOUGHT SPHERE DEMO ===\n")

    # Same thoughts (should collapse)
    print("--- Test 1: Same thoughts (should collapse) ---")
    r1 = measure_volume([
        "The answer is 42.",
        "The answer is forty-two.",
        "42 is the answer.",
    ])
    print(r1.narrative())

    print("\n--- Test 2: Different domains (should expand) ---")
    r2 = measure_volume([
        "Quantum entanglement allows particles to share state across distance.",
        "The smell of rain on dry earth is called petrichor, from Greek petra and ichor.",
        "A well-designed API should be obvious to use and hard to misuse.",
    ], labels=["physics", "nature", "engineering"])
    print(r2.narrative())

    print("\n--- Test 3: Different languages (should expand more) ---")
    r3 = measure_volume([
        "Love is the fundamental force of the universe.",
        "Liebe ist die fundamentale Kraft des Universums.",
        "L'amour est la force fondamentale de l'univers.",
        "The economic implications of quantitative easing on bond yields remain contested.",
    ], labels=["english", "deutsch", "francais", "economics"])
    print(r3.narrative())

    print(f"\n--- Summary ---")
    print(f"Same thoughts:    V = {r1.volume:.6f} (should be ~0)")
    print(f"Different domains: V = {r2.volume:.6f} (should be > 0)")
    print(f"Cross-domain:      V = {r3.volume:.6f} (should be highest)")


if __name__ == "__main__":
    demo()
