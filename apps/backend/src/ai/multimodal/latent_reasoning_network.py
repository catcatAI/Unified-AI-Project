"""Latent reasoning network — real neural network for latent space → text.

This is the missing piece: a real neural network that takes the 64-dim
latent vector from SharedLatentSpace and produces text output.

Architecture:
  64-dim latent → MLP (128, 128) → vocabulary logits → text

This network does the REASONING that CoreNetwork was supposed to do.
CoreNetwork is just graph propagation; this is actual matrix computation
with non-linear activations.

The network is conditional: it generates text conditioned on the latent
vector, which encodes the semantic meaning of the input.
"""

import logging
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class LatentReasoningNetwork:
    """Real neural network for latent → text reasoning.

    Uses a 2-layer MLP with ReLU activations to map 64-dim latent vectors
    to vocabulary logits. This is a conditional language model: it generates
    text conditioned on the latent representation.

    Architecture:
        Input (64) → Linear → ReLU (128) → Linear → ReLU (128) → Linear → Output (vocab_size)

    Training:
        Uses cross-entropy loss with manual backpropagation (no torch dependency).
        Trained on (latent, target_text) pairs from chat interactions.
    """

    def __init__(self, latent_dim: int = 64, hidden_dim: int = 128, vocab_size: int = 1000):
        """Initialize the network.

        Args:
            latent_dim: Input dimension (from SharedLatentSpace)
            hidden_dim: Hidden layer dimension
            vocab_size: Output vocabulary size
        """
        self._latent_dim = latent_dim
        self._hidden_dim = hidden_dim
        self._vocab_size = vocab_size

        # Build vocabulary from common tokens
        self._vocab: List[str] = self._build_vocab()
        self._token_to_idx = {t: i for i, t in enumerate(self._vocab)}
        self._idx_to_token = {i: t for t, i in self._token_to_idx.items()}

        # Xavier initialization
        rng = np.random.default_rng(42)
        scale1 = 1.0 / np.sqrt(latent_dim)
        scale2 = 1.0 / np.sqrt(hidden_dim)

        # Layer 1: latent → hidden
        self._W1 = rng.normal(0, scale1, (hidden_dim, latent_dim)).astype(np.float32)
        self._b1 = np.zeros(hidden_dim, dtype=np.float32)

        # Layer 2: hidden → hidden
        self._W2 = rng.normal(0, scale2, (hidden_dim, hidden_dim)).astype(np.float32)
        self._b2 = np.zeros(hidden_dim, dtype=np.float32)

        # Layer 3: hidden → vocab
        self._W3 = rng.normal(0, scale2, (vocab_size, hidden_dim)).astype(np.float32)
        self._b3 = np.zeros(vocab_size, dtype=np.float32)

        # Training state
        self._trained = False
        self._training_data: List[Tuple[np.ndarray, str]] = []

    def _build_vocab(self) -> List[str]:
        """Build a basic vocabulary of common tokens."""
        # Common English words + Chinese basics
        words = [
            # English basics
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "shall",
            "must",
            "need",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "its",
            "our",
            "their",
            "this",
            "that",
            "these",
            "those",
            "what",
            "which",
            "who",
            "whom",
            "where",
            "when",
            "why",
            "how",
            # Common nouns
            "time",
            "year",
            "people",
            "way",
            "day",
            "man",
            "woman",
            "child",
            "world",
            "life",
            "hand",
            "part",
            "place",
            "case",
            "week",
            "company",
            "system",
            "program",
            "question",
            "work",
            "government",
            "number",
            "night",
            "point",
            "home",
            "water",
            "room",
            "mother",
            "area",
            "money",
            "story",
            "fact",
            "month",
            "lot",
            "right",
            "study",
            "book",
            "eye",
            "job",
            "word",
            "business",
            "issue",
            "side",
            "kind",
            "head",
            "house",
            "service",
            "friend",
            "father",
            "power",
            "hour",
            "game",
            "line",
            "end",
            "member",
            "law",
            "car",
            "city",
            "community",
            "name",
            "president",
            "team",
            "minute",
            "idea",
            "body",
            "back",
            "parent",
            "face",
            "others",
            "level",
            "office",
            "door",
            "health",
            "person",
            "art",
            "war",
            "history",
            "party",
            "result",
            "change",
            "morning",
            "reason",
            "research",
            "girl",
            "guy",
            "moment",
            "air",
            "teacher",
            "force",
            "education",
            # Colors
            "red",
            "blue",
            "green",
            "yellow",
            "black",
            "white",
            "orange",
            "purple",
            "pink",
            "brown",
            "gray",
            "grey",
            # Numbers
            "zero",
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
            "hundred",
            "thousand",
            # Days
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            # Common verbs
            "go",
            "come",
            "make",
            "take",
            "know",
            "get",
            "give",
            "find",
            "tell",
            "ask",
            "work",
            "seem",
            "feel",
            "try",
            "leave",
            "call",
            "keep",
            "let",
            "begin",
            "show",
            "hear",
            "play",
            "run",
            "move",
            "live",
            "believe",
            "hold",
            "bring",
            "happen",
            "write",
            "provide",
            "sit",
            "stand",
            "lose",
            "pay",
            "meet",
            "include",
            "continue",
            "set",
            "learn",
            "change",
            "lead",
            "understand",
            "watch",
            "follow",
            "stop",
            "create",
            "speak",
            "read",
            "allow",
            "add",
            "spend",
            "grow",
            "open",
            "walk",
            "win",
            "offer",
            "remember",
            "love",
            "consider",
            "appear",
            "buy",
            "wait",
            "serve",
            "die",
            "send",
            "expect",
            "build",
            "stay",
            "fall",
            "cut",
            "reach",
            "kill",
            "remain",
            # Common adjectives
            "good",
            "new",
            "first",
            "last",
            "long",
            "great",
            "little",
            "own",
            "other",
            "old",
            "right",
            "big",
            "high",
            "different",
            "small",
            "large",
            "next",
            "early",
            "young",
            "important",
            "few",
            "public",
            "bad",
            "same",
            "able",
            "free",
            "sure",
            "real",
            "full",
            "special",
            "easy",
            "clear",
            "best",
            "recent",
            "certain",
            "personal",
            "open",
            "strong",
            "possible",
            "whole",
            "short",
            "low",
            "local",
            "single",
            "hard",
            "simple",
            "fast",
            "slow",
            "hot",
            "cold",
            "warm",
            "light",
            "dark",
            "heavy",
            "beautiful",
            "happy",
            "sad",
            "angry",
            "scared",
            "tired",
            "sick",
            "healthy",
            # Common responses
            "yes",
            "no",
            "okay",
            "ok",
            "sure",
            "thanks",
            "thank",
            "please",
            "sorry",
            "hello",
            "hi",
            "hey",
            "bye",
            "goodbye",
            "well",
            "right",
            "exactly",
            "absolutely",
            "definitely",
            "probably",
            "maybe",
            "perhaps",
            "actually",
            "basically",
            "simply",
            "just",
            "also",
            "too",
            "very",
            "really",
            "quite",
            "pretty",
            "much",
            "many",
            "some",
            "any",
            "all",
            "every",
            "each",
            "both",
            "neither",
            "either",
            "none",
            # Question words
            "who",
            "what",
            "where",
            "when",
            "why",
            "how",
            "which",
            "whose",
            # Prepositions
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "from",
            "by",
            "about",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "over",
            "of",
            "and",
            "but",
            "or",
            "not",
            "no",
            "if",
            "then",
            "than",
            "so",
            "because",
            "while",
            "although",
            "though",
            "since",
            "until",
            "unless",
            "except",
            # Punctuation
            ".",
            ",",
            "!",
            "?",
            ":",
            ";",
            # Chinese basics
            "你好",
            "谢谢",
            "对不起",
            "没关系",
            "好的",
            "是的",
            "不是",
            "我",
            "你",
            "他",
            "她",
            "它",
            "我们",
            "你们",
            "他们",
            "是",
            "有",
            "在",
            "不",
            "了",
            "的",
            "和",
            "就",
            "人",
            "都",
            "什么",
            "怎么",
            "为什么",
            "哪里",
            "谁",
            "多少",
            "几",
            "今天",
            "明天",
            "昨天",
            "现在",
            "以后",
            "以前",
            "好",
            "大",
            "小",
            "多",
            "少",
            "快",
            "慢",
            "新",
            "旧",
            "喜欢",
            "想",
            "要",
            "会",
            "能",
            "可以",
            "应该",
            "必须",
            # Common phrases
            "i don't know",
            "i'm not sure",
            "that's interesting",
            "tell me more",
            "i understand",
            "good question",
            "let me think",
            "that makes sense",
            "i agree",
            "i disagree",
            "can you explain",
            "what do you mean",
            "how does that work",
            "that's a good point",
            "i see",
            "really",
            "that's amazing",
            "that's terrible",
            "i'm sorry",
            "how are you",
            "i'm fine",
            "what's up",
            "not much",
            "let's go",
            "see you later",
        ]
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for w in words:
            if w not in seen:
                seen.add(w)
                unique.append(w)
        return unique

    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    def _relu_grad(self, x: np.ndarray) -> np.ndarray:
        return (x > 0).astype(np.float32)

    def forward(self, latent: np.ndarray) -> np.ndarray:
        """Forward pass: latent → logits.

        Args:
            latent: (latent_dim,) input vector

        Returns:
            (vocab_size,) logits
        """
        # Layer 1: latent → hidden
        h1_raw = self._W1 @ latent + self._b1
        h1 = self._relu(h1_raw)

        # Layer 2: hidden → hidden
        h2_raw = self._W2 @ h1 + self._b2
        h2 = self._relu(h2_raw)

        # Layer 3: hidden → vocab
        logits = self._W3 @ h2 + self._b3
        return logits

    def _softmax(self, logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
        """Softmax with temperature."""
        scaled = logits / temperature
        shifted = scaled - np.max(scaled)
        exp = np.exp(shifted)
        return exp / np.sum(exp)

    def generate(self, latent: np.ndarray, max_tokens: int = 20, temperature: float = 0.8) -> str:
        """Generate text from a latent vector (autoregressive).

        Args:
            latent: (latent_dim,) input vector
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = greedy)

        Returns:
            Generated text string
        """
        # Autoregressive loop: each step conditions on the running hidden state.
        # We keep a persistent hidden state so generated tokens influence the
        # next, instead of the previous (broken) single-token-only behaviour.
        logits = self.forward(latent)
        probs = self._softmax(logits, temperature)

        tokens = []
        for _ in range(max_tokens):
            if temperature <= 0.0:
                idx = int(np.argmax(probs))
            else:
                idx = int(np.random.choice(len(probs), p=probs))
            token = self._idx_to_token.get(idx, "")
            if token in (".", "!", "?", ""):
                break
            tokens.append(token)
            # Re-condition on the accumulated sequence by re-projecting the
            # latent plus a small drift from the chosen token's embedding slot.
            latent = self._condition_latent(latent, idx)
            logits = self.forward(latent)
            probs = self._softmax(logits, temperature)

        if not tokens:
            # Fallback: return most probable token
            idx = int(np.argmax(probs))
            return self._idx_to_token.get(idx, "unknown")

        return " ".join(tokens)

    def _condition_latent(self, latent: np.ndarray, token_idx: int) -> np.ndarray:
        """Shift the latent vector based on the chosen token so subsequent
        generation is autoregressive rather than static.

        Uses a deterministic, trainable-free perturbation (one-hot projected
        through W3's transpose) — cheap, dependency-free, and stable.
        """
        drift = (
            self._W3[token_idx]
            if token_idx < self._W3.shape[0]
            else np.zeros(self._hidden_dim, dtype=np.float32)
        )
        # map hidden-dim drift back to latent space via W1.T, normalised
        proj = self._W1.T @ (drift * 0.1)
        return (latent + proj).astype(np.float32)

    def train_step(self, latent: np.ndarray, target_text: str, lr: float = 0.001) -> float:
        """Train on a single (latent, target) pair using sequence cross-entropy.

        Unlike the previous single-token implementation, this accumulates
        gradient over ALL target tokens (teacher-forcing on the latent), so the
        network learns to emit a full phrase, not just its first word.

        Args:
            latent: (latent_dim,) input vector
            target_text: Target text string
            lr: Learning rate

        Returns:
            Average loss value over the target tokens
        """
        # Encode target text into token indices (cap to protect vocab bounds)
        target_tokens = target_text.lower().split()
        target_indices = [self._token_to_idx.get(t, 0) for t in target_tokens[:5]]

        if not target_indices:
            return 0.0

        total_loss = 0.0
        running_latent = np.asarray(latent, dtype=np.float32).copy()
        for target_idx in target_indices:
            # Forward pass
            h1_raw = self._W1 @ running_latent + self._b1
            h1 = self._relu(h1_raw)
            h2_raw = self._W2 @ h1 + self._b2
            h2 = self._relu(h2_raw)
            logits = self._W3 @ h2 + self._b3

            # Cross-entropy loss for this target token
            probs = self._softmax(logits)
            loss = -np.log(max(probs[target_idx], 1e-10))
            total_loss += float(loss)

            # Backward pass
            d_logits = probs.copy()
            d_logits[target_idx] -= 1.0  # Gradient of cross-entropy

            d_W3 = np.outer(d_logits, h2)
            d_b3 = d_logits

            d_h2 = self._W3.T @ d_logits * self._relu_grad(h2_raw)

            d_W2 = np.outer(d_h2, h1)
            d_b2 = d_h2

            d_h1 = self._W2.T @ d_h2 * self._relu_grad(h1_raw)

            d_W1 = np.outer(d_h1, running_latent)
            d_b1 = d_h1

            # Gradient clipping
            max_norm = 5.0
            for grad in [d_W1, d_W2, d_W3]:
                norm = np.linalg.norm(grad)
                if norm > max_norm:
                    grad *= max_norm / norm

            # Update weights
            self._W1 -= lr * d_W1
            self._b1 -= lr * d_b1
            self._W2 -= lr * d_W2
            self._b2 -= lr * d_b2
            self._W3 -= lr * d_W3
            self._b3 -= lr * d_b3

            # Teacher-forcing: advance the latent using the same conditioning
            # the generator uses, so the next token is trained in context.
            running_latent = self._condition_latent(running_latent, target_idx)

        self._trained = True
        return total_loss / len(target_indices)

    # ------------------------------------------------------------------
    # Persistence (opt-in: requires the ml/CLIP tier via enable_latent_space)
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        """Persist weights + vocab to a .npz file."""
        import os

        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        np.savez(
            path,
            W1=self._W1,
            b1=self._b1,
            W2=self._W2,
            b2=self._b2,
            W3=self._W3,
            b3=self._b3,
            vocab=np.array(self._vocab, dtype=object),
            trained=np.array([self._trained]),
        )
        logger.info("LatentReasoningNetwork saved to %s", path)

    @classmethod
    def load(cls, path: str) -> "LatentReasoningNetwork":
        """Load weights + vocab from a .npz file produced by save()."""
        data = np.load(path, allow_pickle=True)
        vocab = list(data["vocab"])
        net = cls(
            latent_dim=data["W1"].shape[1], hidden_dim=data["W1"].shape[0], vocab_size=len(vocab)
        )
        net._vocab = vocab
        net._token_to_idx = {t: i for i, t in enumerate(vocab)}
        net._idx_to_token = {i: t for t, i in net._token_to_idx.items()}
        net._W1 = data["W1"].astype(np.float32)
        net._b1 = data["b1"].astype(np.float32)
        net._W2 = data["W2"].astype(np.float32)
        net._b2 = data["b2"].astype(np.float32)
        net._W3 = data["W3"].astype(np.float32)
        net._b3 = data["b3"].astype(np.float32)
        net._trained = bool(data["trained"][0]) if "trained" in data else True
        logger.info("LatentReasoningNetwork loaded from %s", path)
        return net

    def add_training_data(self, latent: np.ndarray, text: str) -> None:
        """Add a training example."""
        self._training_data.append((latent.copy(), text))
        if len(self._training_data) > 10000:
            self._training_data = self._training_data[-10000:]

    def train_batch(self, batch_size: int = 32, lr: float = 0.001) -> float:
        """Train on a batch of stored training data.

        Returns:
            Average loss
        """
        if not self._training_data:
            return 0.0

        indices = np.random.choice(
            len(self._training_data), size=min(batch_size, len(self._training_data)), replace=False
        )

        total_loss = 0.0
        for idx in indices:
            latent, text = self._training_data[idx]
            loss = self.train_step(latent, text, lr=lr)
            total_loss += loss

        return total_loss / len(indices)

    @property
    def is_trained(self) -> bool:
        return self._trained

    @property
    def vocab_size(self) -> int:
        return self._vocab_size
