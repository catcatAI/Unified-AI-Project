"""
Game Policy - L0 Reflex 層級：連續動作策略 + 視覺定位

架構：
- Visual Encoder (256-dim) -> Shared Latent Space (128-dim)
- Continuous Action Head (Diffusion Policy / MLP)
- Visual Grounding Head (Cross-Attention -> 熱力圖)
- 輸出：連續動作向量 + 離散動作 logits + 點擊熱力圖
"""

import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
        return np.asarray(
            0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3))),
            dtype=np.float32,
        )

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

        return np.asarray(heatmap, dtype=np.float32)

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        x = x - x.max()
        e = np.exp(x)
        return np.asarray(e / e.sum(), dtype=np.float32)

    def _softmax_2d(self, x: np.ndarray) -> np.ndarray:
        x = x - x.max()
        e = np.exp(x)
        return np.asarray(e / e.sum(), dtype=np.float32)

    def _pad_or_truncate(self, arr: np.ndarray, target: int) -> np.ndarray:
        if len(arr) >= target:
            return arr[:target]
        padded = np.zeros(target, dtype=np.float32)
        padded[: len(arr)] = arr
        return padded

    def get_action_dict(self, output: PolicyOutput) -> Dict[str, Any]:
        """將 PolicyOutput 轉換為 Luanti 動作字典"""
        actions: Dict[str, Any] = {}

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

    # ------------------------------------------------------------------
    # 權重持久化與訓練（R74：Xavier 隨機初始化 → 行為克隆訓練）
    # ------------------------------------------------------------------

    _TRAINABLE = (
        "W_in",
        "b_in",
        "W_h1",
        "b_h1",
        "W_h2",
        "b_h2",
        "W_cont",
        "b_cont",
        "W_disc",
        "b_disc",
        "W_mode",
        "b_mode",
    )

    def save_weights(self, path: str) -> bool:
        """保存訓練後權重（JSON；np 陣列轉 list）。失敗回 False 不拋出。"""
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "format": "game_policy_weights_v1",
                "saved_at": time.time(),
                "config": {
                    "latent_dim": self.config.latent_dim,
                    "continuous_dim": self.config.continuous_dim,
                    "discrete_dim": self.config.discrete_dim,
                    "hidden_dim": self.config.hidden_dim,
                },
                "weights": {k: np.asarray(self._params[k]).tolist() for k in self._TRAINABLE},
            }
            p.write_text(json.dumps(payload), encoding="utf-8")
            return True
        except Exception as e:
            logger.warning(f"save_weights failed: {e}")
            return False

    def load_weights(self, path: str) -> bool:
        """載入訓練權重。形狀不符（配置漂移）或檔案損壞一律回 False，保持 Xavier 現狀。"""
        try:
            p = Path(path)
            if not p.exists():
                return False
            payload = json.loads(p.read_text(encoding="utf-8"))
            if payload.get("format") != "game_policy_weights_v1":
                logger.warning("load_weights: unknown format, ignored")
                return False
            weights = payload.get("weights", {})
            for k in self._TRAINABLE:
                if k not in weights:
                    return False
                arr = np.asarray(weights[k], dtype=np.float32)
                if arr.shape != self._params[k].shape:
                    logger.warning(
                        f"load_weights: shape drift on {k}: {arr.shape} != {self._params[k].shape}"
                    )
                    return False
                self._params[k] = arr
            logger.info(f"Policy weights loaded from {path} (trained)")
            return True
        except Exception as e:
            logger.warning(f"load_weights failed: {e}")
            return False

    def _batch_forward(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """批次版前向（訓練用），回傳反傳所需的中間量。

        X: (N, latent_dim+32+32)。結構與 forward() 一致：殘差 MLP＋LayerNorm。
        """
        p = self._params
        a1 = X @ p["W_in"] + p["b_in"]
        z1 = self._gelu(a1)
        n1 = self._layer_norm(z1)
        a2 = n1 @ p["W_h1"] + p["b_h1"]
        z2 = self._gelu(a2)
        n2 = self._layer_norm(z2)
        x1 = n1 + n2 * 0.1
        a3 = x1 @ p["W_h2"] + p["b_h2"]
        z3 = self._gelu(a3)
        n3 = self._layer_norm(z3)
        x2 = x1 + n3 * 0.1
        cont_pre = x2 @ p["W_cont"] + p["b_cont"]
        cont = np.tanh(cont_pre) * self.config.action_scale
        disc_logits = x2 @ p["W_disc"] + p["b_disc"]
        mode_logits = x2 @ p["W_mode"] + p["b_mode"]
        return {
            "X": X,
            "a1": a1,
            "z1": z1,
            "n1": n1,
            "a2": a2,
            "z2": z2,
            "n2": n2,
            "x1": x1,
            "a3": a3,
            "z3": z3,
            "n3": n3,
            "x2": x2,
            "cont_pre": cont_pre,
            "cont": cont,
            "disc_logits": disc_logits,
            "mode_logits": mode_logits,
        }

    @staticmethod
    def _layer_norm_backward(dY: np.ndarray, Z: np.ndarray) -> np.ndarray:
        """LayerNorm 反傳：y=(z-μ)/σ 逐列標準化，給 dL/dy 與標準化前輸入 z。"""
        mean = Z.mean(axis=-1, keepdims=True)
        var = Z.var(axis=-1, keepdims=True)
        sigma = np.sqrt(var + 1e-6)
        yhat = (Z - mean) / sigma
        dmean = dY.mean(axis=-1, keepdims=True)
        dvar = (dY * yhat).mean(axis=-1, keepdims=True)
        return (dY - dmean - yhat * dvar) / sigma

    @staticmethod
    def _gelu_backward(dY: np.ndarray, A: np.ndarray) -> np.ndarray:
        """GELU（tanh 近似）反傳。"""
        k = np.sqrt(2.0 / np.pi)
        u = k * (A + 0.044715 * A**3)
        t = np.tanh(u)
        g = 0.5 * A * (1 + t)
        gp = 0.5 * (1 + t) + 0.5 * A * (1 - t * t) * k * (1 + 3 * 0.044715 * A**2)
        return np.asarray(dY * (g + A * gp), dtype=np.float32)

    def train_behavior_cloning(
        self,
        dataset: List[Dict[str, Any]],
        epochs: int = 20,
        lr: float = 1e-3,
        batch_size: int = 64,
        holdout_ratio: float = 0.2,
        seed: int = 7,
        min_mae_improvement: float = 0.01,
        min_acc_improvement: float = 0.02,
    ) -> Dict[str, Any]:
        """行為克隆訓練（手寫反傳，純 numpy）＋ hold-out 學習門。

        dataset 樣本格式：
            visual_latent: (latent_dim,)
            proprioception: (<=32, 自動 pad/truncate)
            intent: (32,) 可選
            continuous: (continuous_dim,) 連續動作目標（-1..1）
            discrete: int 離散動作索引
            mode: PolicyMode/str 可選

        學習門（RELEASE_CRITERIA 第 4 維：exit 1 若無學習）：
            val 上連續動作 MAE 須改善 >= min_mae_improvement，
            或離散 top-1 準確率須改善 >= min_acc_improvement；
            否則放棄訓練結果（保留原權重）並 exit 1 語意（learned=False）。
        """
        if not dataset or len(dataset) < 10:
            return {"learned": False, "reason": "dataset too small"}

        rng = np.random.default_rng(seed)
        idx = rng.permutation(len(dataset))
        n_val = max(2, int(len(dataset) * holdout_ratio))
        val_idx, tr_idx = idx[:n_val], idx[n_val:]
        if len(tr_idx) < 4:
            return {"learned": False, "reason": "train split too small"}

        def make_batch(indices):
            Xs, Yc, Yd, Ym = [], [], [], []
            for i in indices:
                s = dataset[i]
                prop = np.asarray(s.get("proprioception", np.zeros(32)), dtype=np.float32)
                prop = self._pad_or_truncate(prop, 32)
                intent = np.asarray(s.get("intent", self._intent_embedding), dtype=np.float32)
                if intent.shape[0] != 32:
                    intent = self._pad_or_truncate(intent, 32)
                Xs.append(
                    np.concatenate([np.asarray(s["visual_latent"], dtype=np.float32), prop, intent])
                )
                Yc.append(np.asarray(s["continuous"], dtype=np.float32))
                Yd.append(int(s["discrete"]))
                mode = s.get("mode")
                Ym.append(
                    PolicyMode(mode).value
                    if isinstance(mode, str)
                    else getattr(mode, "value", None)
                )
            return (
                np.stack(Xs),
                np.stack(Yc),
                np.asarray(Yd, dtype=np.int64),
                np.asarray(
                    [list(PolicyMode).index(PolicyMode(m)) if m else -1 for m in Ym], dtype=np.int64
                ),
            )

        Xtr, Yctr, Ydtr, Ymtr = make_batch(tr_idx)
        Xva, Ycva, Ydva, Ymva = make_batch(val_idx)
        c = self.config
        n_c = c.continuous_dim

        # 學習前基準（hold-out）
        base_mae, base_acc = self._evaluate_arrays(Xva, Ycva, Ydva)

        # 原始權重（學習門未過時還原用）與最佳權重（通過時採用）分開保存
        original = {k: self._params[k].copy() for k in self._TRAINABLE}
        best = {k: self._params[k].copy() for k in self._TRAINABLE}
        best_val = (base_mae, base_acc)

        for epoch in range(epochs):
            order = rng.permutation(len(tr_idx))
            for start in range(0, len(order), batch_size):
                b = order[start : start + batch_size]
                X, Ycc, Ydd, Ymm = Xtr[b], Yctr[b], Ydtr[b], Ymtr[b]
                N = X.shape[0]
                out = self._batch_forward(X)

                # --- 損失梯度 ---
                # 連續：MSE（經 tanh 反傳：dL/dcont_pre = dL/dcont * (1-tanh²)）
                dcont = 2.0 * (out["cont"] - Ycc) / (N * n_c) * c.action_scale
                dcont_pre = dcont * (1.0 - np.tanh(out["cont_pre"]) ** 2)
                # 離散：softmax CE（逐行）
                dlogits_d = self._softmax_batch(out["disc_logits"])
                dlogits_d[np.arange(N), Ydd] -= 1.0
                dlogits_d /= N
                # 模式（有標註才參與）
                mode_logits = out["mode_logits"]
                if (Ymm >= 0).any():
                    dlogits_m = self._softmax_batch(mode_logits)
                    mask = Ymm >= 0
                    dlogits_m[mask, Ymm[mask]] -= 1.0
                    dlogits_m /= N
                else:
                    dlogits_m = np.zeros_like(mode_logits)

                grads: Dict[str, np.ndarray] = {}
                dx2 = dcont_pre @ self._params["W_cont"].T
                grads["W_cont"] = out["x2"].T @ dcont_pre
                grads["b_cont"] = dcont_pre.sum(axis=0)
                dx2 += dlogits_d @ self._params["W_disc"].T
                grads["W_disc"] = out["x2"].T @ dlogits_d
                grads["b_disc"] = dlogits_d.sum(axis=0)
                dx2 += dlogits_m @ self._params["W_mode"].T
                grads["W_mode"] = out["x2"].T @ dlogits_m
                grads["b_mode"] = dlogits_m.sum(axis=0)

                # x2 = x1 + n3*0.1
                dn3 = self._layer_norm_backward(dx2 * 0.1, out["z3"])
                dx1 = dx2.copy()
                dz3 = self._gelu_backward(dn3, out["a3"])
                dx1 += dz3 @ self._params["W_h2"].T
                grads["W_h2"] = out["x1"].T @ dz3
                grads["b_h2"] = dz3.sum(axis=0)
                # x1 = n1 + n2*0.1
                dn2 = self._layer_norm_backward(dx1 * 0.1, out["z2"])
                dn1 = dx1.copy()
                dz2 = self._gelu_backward(dn2, out["a2"])
                dn1 += dz2 @ self._params["W_h1"].T
                grads["W_h1"] = out["n1"].T @ dz2
                grads["b_h1"] = dz2.sum(axis=0)
                dz1 = self._gelu_backward(self._layer_norm_backward(dn1, out["z1"]), out["a1"])
                grads["W_in"] = out["X"].T @ dz1
                grads["b_in"] = dz1.sum(axis=0)

                for k in self._TRAINABLE:
                    self._params[k] = (self._params[k] - lr * grads[k]).astype(np.float32)

            # epoch 末評 val，保留最佳
            val_mae, val_acc = self._evaluate_arrays(Xva, Ycva, Ydva)
            if (val_mae + (1.0 - val_acc)) < (best_val[0] + (1.0 - best_val[1])):
                best_val = (val_mae, val_acc)
                best = {k: self._params[k].copy() for k in self._TRAINABLE}

        mae_imp = base_mae - best_val[0]
        acc_imp = best_val[1] - base_acc
        if mae_imp >= min_mae_improvement or acc_imp >= min_acc_improvement:
            for k in self._TRAINABLE:
                self._params[k] = best[k]
            return {
                "learned": True,
                "baseline": {"val_mae": round(base_mae, 4), "val_acc": round(base_acc, 4)},
                "after": {"val_mae": round(best_val[0], 4), "val_acc": round(best_val[1], 4)},
                "improvement": {"mae": round(mae_imp, 4), "acc": round(acc_imp, 4)},
                "train_samples": int(len(tr_idx)),
                "val_samples": int(len(val_idx)),
                "epochs": epochs,
            }
        # 學習門未過：還原到訓練前權重（門未過＝一切如舊，不保留部分擬合結果）
        for k in self._TRAINABLE:
            self._params[k] = original[k]
        return {
            "learned": False,
            "reason": "holdout gate not passed",
            "baseline": {"val_mae": round(base_mae, 4), "val_acc": round(base_acc, 4)},
            "after": {"val_mae": round(best_val[0], 4), "val_acc": round(best_val[1], 4)},
            "improvement": {"mae": round(mae_imp, 4), "acc": round(acc_imp, 4)},
        }

    def _softmax_batch(self, x: np.ndarray) -> np.ndarray:
        """逐行 softmax（批次用；_softmax 僅支援 1D）。"""
        x = x - x.max(axis=-1, keepdims=True)
        e = np.exp(x)
        return e / e.sum(axis=-1, keepdims=True)

    def _evaluate_arrays(
        self, X: np.ndarray, Yc: np.ndarray, Yd: np.ndarray
    ) -> Tuple[float, float]:
        """hold-out 評測：連續動作 MAE 與離散 top-1 準確率。"""
        out = self._batch_forward(X)
        mae = float(np.abs(out["cont"] - Yc).mean())
        pred = np.asarray(out["disc_logits"]).argmax(axis=-1)
        acc = float((pred == Yd).mean())
        return mae, acc


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
        return np.asarray(alphas / alphas[0], dtype=np.float32)

    def denoise(self, noisy_action: np.ndarray, condition: np.ndarray, step: int) -> np.ndarray:
        """單步去噪 (簡化版，實際需訓練去噪網路)"""
        # 這裡只做線性插值演示
        alpha = self._noise_schedule[step]
        return np.asarray(noisy_action * alpha + condition * (1 - alpha), dtype=np.float32)

    def sample(self, condition: np.ndarray, shape: Tuple[int, ...]) -> np.ndarray:
        """從雜訊採樣動作"""
        x = np.random.randn(*shape).astype(np.float32)
        for i in range(self.steps):
            x = self.denoise(x, condition, i)
        return np.asarray(np.tanh(x), dtype=np.float32)
