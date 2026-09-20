"""
Game Policy - L0 Reflex 層級：連續動作策略 + 視覺定位

架構：
- Visual Encoder (256-dim) -> Shared Latent Space (128-dim)
- Continuous Action Head (Diffusion Policy / MLP)
- Visual Grounding Head (Cross-Attention -> 熱力圖)
- 輸出：連續動作向量 + 離散動作 logits + 點擊熱力圖
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, List
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)


class PolicyMode(str, Enum):
    EXPLORATION = "exploration"
    EXPLOITATION = "exploitation"
    COMBAT = "combat"
    BUILDING = "building"
    FLEEING = "fleeing"


@dataclass
class PolicyConfig:
    latent_dim: int = 128
    continuous_dim: int = 16
    discrete_dim: int = 8
    hidden_dim: int = 256
    grounding_resolution: Tuple[int, int] = (32, 32)  # 熱力圖解析度
    diffusion_steps: int = 4
    use_diffusion: bool = True
    dropout: float = 0.1
    action_scale: float = 1.0


@dataclass
class PolicyOutput:
    continuous: np.ndarray  # (16,) 連續動作
    discrete_logits: np.ndarray  # (8,) 離散動作 logits
    grounding_heatmap: np.ndarray  # (H, W) 點擊/互動熱力圖
    mode: PolicyMode
    confidence: float
    latent: np.ndarray  # (128,) 潛在向量 (供上層使用)


class GamePolicy:
    """
    L0 級策略網路

    輸入：visual_latent (128) + proprioception (32) + intent_embedding (32, optional)
    輸出：continuous_action (16) + discrete_logits (8) + grounding_heatmap (32, 32)

    無 LLM 依賴，純 numpy/MLP 推理，<5ms/幀
    """

    def __init__(self, config: Optional[PolicyConfig] = None):
        self.config = config or PolicyConfig()
        self._params: Dict[str, np.ndarray] = {}
        self._initialized = False
        self._mode = PolicyMode.EXPLORATION
        self._intent_embedding = np.zeros(32, dtype=np.float32)

        # 動作維度映射
        self._action_map = {
            # 連續動作 (16 維)
            "move_forward": 0,
            "move_strafe": 1,
            "move_yaw": 2,
            "look_yaw": 3,
            "look_pitch": 4,
            "dig_yaw": 5,
            "dig_pitch": 6,
            "place_yaw": 7,
            "place_pitch": 8,
            "nav_yaw": 9,
            "nav_pitch": 10,
            "nav_forward": 11,
            "combat_yaw": 12,
            "combat_pitch": 13,
            "combat_strafe": 14,
            "build_yaw": 15,
            # 離散動作 (8 維)
            "discrete_attack": 0,
            "discrete_use": 1,
            "discrete_jump": 2,
            "discrete_sprint": 3,
            "discrete_sneak": 4,
            "discrete_inventory": 5,
            "discrete_craft_grid": 6,
            "discrete_craft_output": 7,
        }

        self._init_weights()

    def _init_weights(self):
        """初始化網路權重 (Xavier/Glorot)"""
        np.random.seed(42)  # 可復現
        c = self.config

        # 輸入投影: (128+32+32=192) -> hidden
        in_dim = c.latent_dim + 32 + 32
        self._params["W_in"] = self._xavier(in_dim, c.hidden_dim)
        self._params["b_in"] = np.zeros(c.hidden_dim, dtype=np.float32)

        # 隱藏層
        self._params["W_h1"] = self._xavier(c.hidden_dim, c.hidden_dim)
        self._params["b_h1"] = np.zeros(c.hidden_dim, dtype=np.float32)
        self._params["W_h2"] = self._xavier(c.hidden_dim, c.hidden_dim)
        self._params["b_h2"] = np.zeros(c.hidden_dim, dtype=np.float32)

        # 連續動作頭
        self._params["W_cont"] = self._xavier(c.hidden_dim, c.continuous_dim)
        self._params["b_cont"] = np.zeros(c.continuous_dim, dtype=np.float32)

        # 離散動作頭
        self._params["W_disc"] = self._xavier(c.hidden_dim, c.discrete_dim)
        self._params["b_disc"] = np.zeros(c.discrete_dim, dtype=np.float32)

        # Grounding Head: Cross-Attention
        # Query 來自 hidden, Key/Value 來自 visual features (下採樣到 32x32)
        self._params["W_q"] = self._xavier(c.hidden_dim, 64)
        self._params["W_k"] = self._xavier(256, 64)  # visual feature dim
        self._params["W_v"] = self._xavier(256, 64)
        self._params["W_g_out"] = self._xavier(64, 1)  # 輸出單通道熱力圖

        # Mode classifier
        self._params["W_mode"] = self._xavier(c.hidden_dim, len(PolicyMode))
        self._params["b_mode"] = np.zeros(len(PolicyMode), dtype=np.float32)

        self._initialized = True

    def _xavier(self, fan_in: int, fan_out: int) -> np.ndarray:
        """Xavier 初始化"""
        limit = np.sqrt(6.0 / (fan_in + fan_out))
        return np.random.uniform(-limit, limit, (fan_in, fan_out)).astype(np.float32)

    def _gelu(self, x: np.ndarray) -> np.ndarray:
        """GELU 激活函數"""
        return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))

    def _layer_norm(self, x: np.ndarray, eps: float = 1e-6) -> np.ndarray:
        """Layer Normalization"""
        mean = x.mean(axis=-1, keepdims=True)
        var = x.var(axis=-1, keepdims=True)
        return (x - mean) / np.sqrt(var + eps)

    def set_intent(self, intent_embedding: np.ndarray):
        """設定意圖嵌入 (來自 L3/L4)"""
        if intent_embedding.shape == (32,):
            self._intent_embedding = intent_embedding.astype(np.float32)

    def set_mode(self, mode: PolicyMode):
        """設定策略模式"""
        self._mode = mode

    def forward(
        self,
        visual_latent: np.ndarray,
        proprioception: np.ndarray,
        visual_features: Optional[np.ndarray] = None,
    ) -> PolicyOutput:
        """
        前向傳播

        Args:
            visual_latent: (128,) shared latent space 向量
            proprioception: (32,) 本體感覺向量
            visual_features: (H, W, 256) 視覺特徵圖 (用於 grounding)，None 時用零向量

        Returns:
            PolicyOutput
        """
        start = time.perf_counter()
        c = self.config

        # 輸入拼接
        if proprioception.shape[0] != 32:
            proprioception = self._pad_or_truncate(proprioception, 32)

        x = np.concatenate([visual_latent, proprioception, self._intent_embedding])

        # 輸入投影
        x = x @ self._params["W_in"] + self._params["b_in"]
        x = self._gelu(x)
        x = self._layer_norm(x)

        # 隱藏層 1
        h1 = x @ self._params["W_h1"] + self._params["b_h1"]
        h1 = self._gelu(h1)
        h1 = self._layer_norm(h1)

        # 殘差連接
        x = x + h1 * 0.1

        # 隱藏層 2
        h2 = x @ self._params["W_h2"] + self._params["b_h2"]
        h2 = self._gelu(h2)
        h2 = self._layer_norm(h2)

        x = x + h2 * 0.1

        # 連續動作頭
        continuous = x @ self._params["W_cont"] + self._params["b_cont"]
        continuous = np.tanh(continuous) * c.action_scale

        # 離散動作頭
        discrete_logits = x @ self._params["W_disc"] + self._params["b_disc"]

        # Grounding Head (Cross-Attention)
        if visual_features is not None:
            grounding = self._compute_grounding(x, visual_features)
        else:
            grounding = np.zeros(c.grounding_resolution, dtype=np.float32)

        # Mode 分類
        mode_logits = x @ self._params["W_mode"] + self._params["b_mode"]
        mode_probs = self._softmax(mode_logits)
        pred_mode = PolicyMode(list(PolicyMode)[np.argmax(mode_probs)])

        # 信心度
        confidence = float(mode_probs.max())

        elapsed = (time.perf_counter() - start) * 1000
        if elapsed > 10:
            logger.warning(f"Policy forward slow: {elapsed:.1f}ms")

        return PolicyOutput(
            continuous=continuous.astype(np.float32),
            discrete_logits=discrete_logits.astype(np.float32),
            grounding_heatmap=grounding.astype(np.float32),
            mode=pred_mode,
            confidence=confidence,
            latent=x.astype(np.float32),
        )

    def _compute_grounding(self, hidden: np.ndarray, visual_features: np.ndarray) -> np.ndarray:
        """
        Cross-Attention Grounding

        hidden: (hidden_dim,) -> Query
        visual_features: (H, W, 256) -> Key, Value
        """
        h, w, feat_dim = visual_features.shape
        gh, gw = self.config.grounding_resolution

        # 下採樣 visual features 到 grounding 解析度
        if (h, w) != (gh, gw):
            # 簡單平均池化
            scale_h, scale_w = h // gh, w // gw
            vf_ds = visual_features.reshape(gh, scale_h, gw, scale_w, feat_dim)
            vf_ds = vf_ds.mean(axis=(1, 3))  # (gh, gw, 256)
        else:
            vf_ds = visual_features

        # Query from hidden
        q = hidden @ self._params["W_q"]  # (64,)

        # Key, Value from visual
        k = vf_ds @ self._params["W_k"]  # (gh, gw, 64)
        v = vf_ds @ self._params["W_v"]  # (gh, gw, 64)

        # Attention: q @ k^T
        # q: (64,), k: (gh, gw, 64) -> attn: (gh, gw)
        attn = np.einsum("d,hwd->hw", q, k) / np.sqrt(64)
        attn = self._softmax_2d(attn)

        # Weighted sum of values
        out = np.einsum("hw,hwd->d", attn, v)  # (64,)

        # Output projection to heatmap
        heatmap = out @ self._params["W_g_out"].squeeze(-1)  # (gh, gw) 不對，這裡要重新設計

        # 正確做法：每個位置獨立計算
        # 簡化：用 attention map 直接作為 heatmap
        heatmap = attn

        # 正規化到 [0, 1]
        if heatmap.max() > heatmap.min():
            heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())

        return heatmap.astype(np.float32)

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        x = x - x.max()
        e = np.exp(x)
        return e / e.sum()

    def _softmax_2d(self, x: np.ndarray) -> np.ndarray:
        x = x - x.max()
        e = np.exp(x)
        return e / e.sum()

    def _pad_or_truncate(self, arr: np.ndarray, target: int) -> np.ndarray:
        if len(arr) >= target:
            return arr[:target]
        padded = np.zeros(target, dtype=np.float32)
        padded[: len(arr)] = arr
        return padded

    def get_action_dict(self, output: PolicyOutput) -> Dict[str, Any]:
        """將 PolicyOutput 轉換為 Luanti 動作字典"""
        actions = {}

        # 連續動作解碼
        cont = output.continuous

        # 移動
        move_forward = float(np.clip(cont[0], -1, 1))
        move_strafe = float(np.clip(cont[1], -1, 1))
        move_yaw = float(np.clip(cont[2], -1, 1))

        if abs(move_forward) > 0.1 or abs(move_strafe) > 0.1 or abs(move_yaw) > 0.1:
            actions["move"] = {"forward": move_forward, "strafe": move_strafe, "yaw": move_yaw}

        # 視線
        look_yaw = float(cont[3])
        look_pitch = float(cont[4])
        if abs(look_yaw) > 0.05 or abs(look_pitch) > 0.05:
            actions["look"] = {"yaw_delta": look_yaw, "pitch_delta": look_pitch}

        # 離散動作 (sigmoid + threshold)
        disc_probs = 1 / (1 + np.exp(-output.discrete_logits))

        if disc_probs[0] > 0.5:  # attack
            actions["dig"] = True
        if disc_probs[1] > 0.5:  # use
            actions["place"] = True
        if disc_probs[2] > 0.5:  # jump
            if "move" not in actions:
                actions["move"] = {}
            actions["move"]["jump"] = True
        if disc_probs[3] > 0.5:  # sprint
            if "move" not in actions:
                actions["move"] = {}
            actions["move"]["sprint"] = True
        if disc_probs[4] > 0.5:  # sneak
            if "move" not in actions:
                actions["move"] = {}
            actions["move"]["sneak"] = True

        return actions

    def get_grounding_click(
        self, output: PolicyOutput, inverse_map: np.ndarray
    ) -> Optional[Tuple[int, int]]:
        """
        從熱力圖獲取最佳點擊位置並映射回原圖座標

        Returns:
            (orig_x, orig_y) 或 None
        """
        heatmap = output.grounding_heatmap
        if heatmap.max() < 0.3:  # 信心度太低
            return None

        # 找最大值位置
        y, x = np.unravel_index(heatmap.argmax(), heatmap.shape)

        # 映射回原圖
        out_h, out_w = inverse_map.shape[:2]
        x = np.clip(x, 0, out_w - 1)
        y = np.clip(y, 0, out_h - 1)
        orig_x, orig_y = inverse_map[y, x]

        return int(orig_x), int(orig_y)


class DiffusionPolicyHead:
    """
    Diffusion Policy 頭 (可選，更平滑的動作生成)

    使用 DDPM 風格的去噪過程，從雜訊生成動作
    """

    def __init__(self, config: PolicyConfig):
        self.config = config
        self.steps = config.diffusion_steps
        self._noise_schedule = self._cosine_schedule(self.steps)

    def _cosine_schedule(self, steps: int) -> np.ndarray:
        """Cosine noise schedule"""
        t = np.linspace(0, 1, steps + 1)
        alphas = np.cos((t + 0.008) / 1.008 * np.pi / 2) ** 2
        return alphas / alphas[0]

    def denoise(self, noisy_action: np.ndarray, condition: np.ndarray, step: int) -> np.ndarray:
        """單步去噪 (簡化版，實際需訓練去噪網路)"""
        # 這裡只做線性插值演示
        alpha = self._noise_schedule[step]
        return noisy_action * alpha + condition * (1 - alpha)

    def sample(self, condition: np.ndarray, shape: Tuple[int, ...]) -> np.ndarray:
        """從雜訊採樣動作"""
        x = np.random.randn(*shape).astype(np.float32)
        for i in range(self.steps):
            x = self.denoise(x, condition, i)
        return np.tanh(x)
