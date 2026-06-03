"""
Neuro Auto Selector — [auto] LLM Mode for Angela AI
=====================================================
Automatically selects LLM backend, model, and parameters based on:
- Phase 1: Hardware capability score (SystemHardwareProbe)
- Phase 2: System real-time load → time budget
- Phase 3: Task complexity (intent, message length)
- Phase 4: 8D state matrix correction (alpha.energy, epsilon.precision, theta.novelty, etc.)
- Phase 5: Backend + model selection
- Phase 6: Decision recording & learning
"""

import time
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from core.system.config.magic_numbers import batch_value, llm_param

logger = logging.getLogger(__name__)

# =============================================================================
# Data Types
# =============================================================================


class HardwareTier(str, Enum):
    EXTREME = "extreme"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CRITICAL = "critical"


class AutoBackendChoice(str, Enum):
    NEUROBLENDER = "neuroblender"
    LLAMA_CPP = "llamacpp"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


@dataclass
class AutoDecision:
    """Decision result from NeuroAutoSelector"""

    backend: AutoBackendChoice = AutoBackendChoice.NEUROBLENDER
    model: str = ""
    time_budget_ms: int = 30000
    use_thinking: bool = False
    temperature: float = llm_param("neuro_selector_temp", 0.7)
    max_tokens: int = int(llm_param("neuro_selector_tokens", 512))
    context_window: int = int(batch_value("neuro_context", 4096))
    reason: str = ""
    hw_score: float = 0.0
    load_factor: float = 1.0
    task_demand: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict format."""
        return asdict(self)

    @classmethod
    def neuroblender_fallback(cls, reason: str = "") -> "AutoDecision":
        """Execute the neuroblender fallback operation."""
        return cls(
            backend=AutoBackendChoice.NEUROBLENDER,
            reason=reason or "No available LLM backend, falling back to NeuroBlender",
        )


@dataclass
class TaskBudget:
    demand_score: float = 0.0
    needs_reasoning: bool = False
    min_quality: bool = False
    preferred_context_window: int = int(batch_value("neuro_preferred_context", 4096))


# =============================================================================
# Intent Cost Map (config-driven, with defaults)
# =============================================================================

DEFAULT_INTENT_COST = {
    "math": 0.9,
    "code": 0.8,
    "task": 0.7,
    "reasoning": 0.6,
    "general": 0.4,
    "smalltalk": 0.2,
    "emotion": 0.3,
}

DEFAULT_TIME_BUDGET_TABLE = {
    HardwareTier.EXTREME: 60000,
    HardwareTier.HIGH: 30000,
    HardwareTier.MEDIUM: 20000,
    HardwareTier.LOW: 10000,
    HardwareTier.CRITICAL: 3000,
}

DEFAULT_LOCAL_MODEL_THRESHOLDS = [
    {"min_ram_gb": 16, "min_vram_gb": 8, "recommend": "deepseek-r1:latest"},
    {"min_ram_gb": 8, "min_vram_gb": 4, "recommend": "qwen2.5-coder:latest"},
    {"min_ram_gb": 4, "min_vram_gb": 0, "recommend": "phi:latest"},
]

DEFAULT_CLOUD_PRIORITY = ["openai", "anthropic", "google"]


# =============================================================================
# HardwareAnalyzer
# =============================================================================


class HardwareAnalyzer:
    """Phase 1: Detect and score hardware capability."""

    def __init__(self):
        self._probe = None

    def _get_probe(self) -> str:
        """Get probe."""
        if self._probe is None:
            from shared.utils.hardware_detector import SystemHardwareProbe

            self._probe = SystemHardwareProbe()
        return self._probe

    def analyze(self) -> Tuple[float, HardwareTier, Dict[str, Any]]:
        """
        Returns (score 0-100, tier, details dict).
        """
        probe = self._get_probe()
        profile = probe.detect()

        # Score: 0-100 based on RAM, VRAM, cores, GPU
        score = profile.ai_capability_score

        # Determine tier from score
        if score > 80:
            tier = HardwareTier.EXTREME
        elif score > 60:
            tier = HardwareTier.HIGH
        elif score > 40:
            tier = HardwareTier.MEDIUM
        elif score > 20:
            tier = HardwareTier.LOW
        else:
            tier = HardwareTier.CRITICAL

        details = {
            "ram_total_gb": profile.ram_total_gb,
            "ram_available_gb": profile.ram_available_gb,
            "vram_mb": profile.vram_mb,
            "cpu_cores_logical": profile.cpu_cores_logical,
            "accelerator_type": profile.accelerator_type.value,
            "accelerator_name": profile.accelerator_name,
            "performance_tier": profile.performance_tier,
            "is_laptop": profile.is_laptop,
        }

        logger.info(
            f"[HardwareAnalyzer] Score={score:.1f}, Tier={tier.value}, "
            f"RAM={profile.ram_total_gb:.1f}GB, VRAM={profile.vram_mb}MB, "
            f"GPU={profile.accelerator_name}"
        )
        return score, tier, details


# =============================================================================
# BudgetScheduler
# =============================================================================


class BudgetScheduler:
    """Phase 2: Calculate available time budget from hardware + system load."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._resource_service = None

    def _get_resource_service(self) -> str:
        """Get resource service."""
        if self._resource_service is None:
            from services.resource_awareness_service import ResourceAwarenessService

            self._resource_service = ResourceAwarenessService()
        return self._resource_service

    def _get_time_budget_table(self) -> Dict[str, int]:
        """Get time budget table."""
        cfg = self.config.get("time_budget_table", {})
        return {
            HardwareTier.EXTREME.value: cfg.get("extreme", DEFAULT_TIME_BUDGET_TABLE[HardwareTier.EXTREME]),
            HardwareTier.HIGH.value: cfg.get("high", DEFAULT_TIME_BUDGET_TABLE[HardwareTier.HIGH]),
            HardwareTier.MEDIUM.value: cfg.get("medium", DEFAULT_TIME_BUDGET_TABLE[HardwareTier.MEDIUM]),
            HardwareTier.LOW.value: cfg.get("low", DEFAULT_TIME_BUDGET_TABLE[HardwareTier.LOW]),
            HardwareTier.CRITICAL.value: cfg.get("critical", DEFAULT_TIME_BUDGET_TABLE[HardwareTier.CRITICAL]),
        }

    def schedule(self, hw_score: float, tier: HardwareTier, energy: float = 0.5) -> int:
        """
        Calculate available time budget in milliseconds.
        Args:
            hw_score: hardware score 0-100
            tier: hardware tier
            energy: alpha.energy from state matrix (0-1)
        Returns:
            time budget in ms
        """
        table = self._get_time_budget_table()
        raw_budget = table.get(tier.value, 30000)

        # Apply system load factor
        load_factor = 1.0
        try:
            svc = self._get_resource_service()
            load_factor = svc.get_throttling_factor()
            self._load_factor = load_factor
        except Exception:
            logger.warning("Failed to get resource throttling factor, using 1.0", exc_info=True)
            self._load_factor = 1.0

        budget = int(raw_budget * load_factor)

        # 8D energy correction
        if energy < 0.3:
            budget = int(budget * 0.6)
        elif energy > 0.7:
            budget = int(budget * 1.1)

        # Clamp
        min_budget = self.config.get("min_time_budget_ms", 5000)
        max_budget = self.config.get("max_time_budget_ms", 60000)
        budget = max(min_budget, min(budget, max_budget))

        logger.debug(
            f"[BudgetScheduler] raw={raw_budget}ms, load={load_factor:.2f}, "
            f"energy={energy:.2f} → budget={budget}ms"
        )
        return budget


# =============================================================================
# StateInterpreter
# =============================================================================


class StateInterpreter:
    """Phase 4: Read 8D state matrix and return correction factors."""

    def __init__(self):
        self._state_matrix = None
        self._state_adapter = None

    def _ensure_loaded(self) -> None:
        """Ensure loaded."""
        if self._state_matrix is None:
            try:
                from core.engine.state_matrix import StateMatrix4D

                self._state_matrix = StateMatrix4D()
            except Exception:
                logger.warning("[StateInterpreter] StateMatrix4D not available", exc_info=True)

    def get_energy(self) -> float:
        """Get alpha.energy from state matrix."""
        self._ensure_loaded()
        if self._state_matrix is None:
            return 0.5
        try:
            state = self._state_matrix.get_state("alpha")
            if state and "energy" in state:
                return float(state["energy"])
        except Exception as e:
            logger.warning(f"Failed to get alpha energy from state matrix: {e}", exc_info=True)
        return 0.5

    def get_state_dict(self) -> Dict[str, float]:
        """
        Return a flat dict of key state values for decision correction.
        Keys: alpha_energy, epsilon_precision, delta_happiness, theta_novelty,
              theta_negativity, eta_success_rate
        """
        self._ensure_loaded()
        result: Dict[str, float] = {}

        if self._state_matrix is None:
            return {
                "alpha_energy": 0.5,
                "epsilon_precision": 0.5,
                "delta_happiness": 0.5,
                "theta_novelty": 0.3,
                "theta_negativity": 0.3,
                "eta_success_rate": 0.85,
            }

        try:
            state = self._state_matrix.get_state()
            if "alpha" in state:
                result["alpha_energy"] = float(state["alpha"].get("energy", 0.5))
            if "epsilon" in state:
                result["epsilon_precision"] = float(state["epsilon"].get("precision", 0.5))
            if "delta" in state:
                result["delta_happiness"] = float(state["delta"].get("happiness", 0.5))
            if "theta" in state:
                result["theta_novelty"] = float(state["theta"].get("novelty", 0.3))
                result["theta_negativity"] = float(state["theta"].get("negativity", 0.3))
            # η 不在 StateMatrix4D 中，需從 export_for_llm() 取得
            try:
                full = self._state_matrix.export_for_llm()
                eta_data = full.get("eta", {})
                result["eta_success_rate"] = float(eta_data.get("success_rate", 0.85))
            except Exception as e:
                logger.warning(f"Failed to get eta success_rate from export_for_llm: {e}", exc_info=True)
        except Exception as e:
            logger.warning(f"Failed to get state dict from state matrix: {e}", exc_info=True)

        # Fill defaults for missing keys
        for key in ["alpha_energy", "epsilon_precision", "delta_happiness"]:
            result.setdefault(key, 0.5)
        for key in ["theta_novelty", "theta_negativity"]:
            result.setdefault(key, 0.3)
        result.setdefault("eta_success_rate", 0.85)

        return result

    def apply_correction(
        self, budget: int, task: TaskBudget, state: Dict[str, float]
    ) -> AutoDecision:
        """
        Apply 8D state corrections to produce a refined decision.
        """
        decision = AutoDecision(
            time_budget_ms=budget,
            use_thinking=task.needs_reasoning,
            temperature=llm_param("neuro_selector_temp", 0.7),
            max_tokens=int(llm_param("neuro_selector_tokens", 512)),
            context_window=task.preferred_context_window,
        )

        energy = state.get("alpha_energy", 0.5)
        precision = state.get("epsilon_precision", 0.5)
        happiness = state.get("delta_happiness", 0.5)
        novelty = state.get("theta_novelty", 0.3)
        negativity = state.get("theta_negativity", 0.3)
        success_rate = state.get("eta_success_rate", 0.85)

        # epsilon.precision high → force thinking, lower temperature
        if precision > 0.7:
            decision.use_thinking = True
            decision.temperature = llm_param("neuro_precise_temp", 0.3)

        # delta.happiness low → shorter, comfort-oriented
        if happiness < 0.35:
            decision.max_tokens = int(llm_param("neuro_precise_tokens", 256))
            decision.temperature = llm_param("neuro_comfort_temp", 0.8)
            decision.reason = "low_happiness_comfort_mode"

        # alpha.energy low → reduce resource consumption
        if energy < 0.3:
            decision.time_budget_ms = min(budget, 10000)
            decision.use_thinking = False
            decision.reason = "low_energy_economy_mode"

        # theta.novelty high → prefer cloud strong model
        if novelty > 0.7:
            decision.reason = "high_novelty_quality_mode"

        # theta.negativity high → careful, precise
        if negativity > 0.6:
            decision.use_thinking = True
            decision.temperature = llm_param("neuro_careful_temp", 0.4)

        # eta.success_rate low → be conservative
        if success_rate < 0.6:
            decision.time_budget_ms = min(decision.time_budget_ms, 15000)
            decision.max_tokens = min(decision.max_tokens, 256)

        return decision


# =============================================================================
# LearnRecorder
# =============================================================================


class LearnRecorder:
    """Phase 6: Record auto decisions for learning."""

    def __init__(self):
        self._config_loader = None
        self._pending: List[Dict[str, Any]] = []

    def _get_config_loader(self) -> str:
        """Get config loader."""
        if self._config_loader is None:
            try:
                from core.config_loader import get_angela_config

                self._config_loader = get_angela_config()
            except Exception as e:
                logger.warning(f"Failed to load config_loader: {e}", exc_info=True)
        return self._config_loader

    def record(self, decision: AutoDecision, actual_ms: float, success: bool) -> None:
        """Record one auto decision result."""
        record = {
            "timestamp": time.time(),
            "hw_score": decision.hw_score,
            "load_factor": decision.load_factor,
            "task_demand": decision.task_demand,
            "backend": decision.backend.value,
            "model": decision.model,
            "use_thinking": decision.use_thinking,
            "budget_ms": decision.time_budget_ms,
            "actual_ms": actual_ms,
            "success": success,
        }
        self._pending.append(record)
        logger.debug(f"[LearnRecorder] Recorded: {record['backend']}/{record['model']} success={success}")

        if len(self._pending) >= 100:
            self._flush()

    def _flush(self) -> None:
        """Flush buffered records to learned_routes.yaml via config_loader."""
        cfg = self._get_config_loader()
        if cfg is None or not self._pending:
            return
        try:
            for record in self._pending:
                cfg.learn("route_success" if record["success"] else "route_fail", record)
            logger.info(f"[LearnRecorder] Flushed {len(self._pending)} records")
            self._pending.clear()
        except Exception:
            logger.warning("[LearnRecorder] Flush failed, will retry later", exc_info=True)

    def flush_sync(self) -> None:
        """Force flush (called on shutdown)."""
        self._flush()


# =============================================================================
# NeuroAutoSelector (Main)
# =============================================================================


class NeuroAutoSelector:
    """
    [auto] LLM mode selector — decides backend, model, and parameters.

    Pipeline:
        Phase 1: HardwareAnalyzer → score + tier
        Phase 2: BudgetScheduler → time budget
        Phase 3: TaskAnalysis → demand_score
        Phase 4: StateInterpreter → apply_correction()
        Phase 5: Model selection (local vs cloud)
        Phase 6: LearnRecorder → record decision
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.hardware = HardwareAnalyzer()
        self.budget_scheduler = BudgetScheduler(self.config.get("auto_mode", {}))
        self.state_interpreter = StateInterpreter()
        self.recorder = LearnRecorder()

        # Cached hardware info (refreshed periodically)
        self._hw_score: float = 0.0
        self._hw_tier: HardwareTier = HardwareTier.MEDIUM
        self._hw_details: Dict[str, Any] = {}
        self._last_hw_time: float = 0

    # ── Public API ──────────────────────────────────────────────────────────

    async def decide(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> AutoDecision:
        """
        Run full [auto] pipeline to select LLM configuration.

        Args:
            context: Dict with optional keys:
                - intent: str (e.g. "math", "code", "general")
                - complexity: float (0-1)
                - user_message: str
                - force_backend: str (optional override)
                - energy: float (optional override for alpha.energy)

        Returns:
            AutoDecision with backend, model, params
        """
        ctx = context or {}

        # Phase 1: Hardware
        hw_score, hw_tier, hw_details = self._get_hardware()
        self._hw_score = hw_score
        self._hw_tier = hw_tier
        self._hw_details = hw_details

        # Phase 2: Time budget
        energy = ctx.get("energy") or self.state_interpreter.get_energy()
        budget = self.budget_scheduler.schedule(hw_score, hw_tier, energy)

        # Phase 3: Task analysis
        task = self._analyze_task(ctx)

        # Phase 4: State correction
        state = self.state_interpreter.get_state_dict()
        decision = self.state_interpreter.apply_correction(budget, task, state)
        decision.hw_score = hw_score
        decision.task_demand = task.demand_score
        decision.load_factor = getattr(self.budget_scheduler, "_load_factor", 1.0)

        # Phase 5: Model selection
        if decision.time_budget_ms < self.config.get("auto_mode", {}).get("min_time_budget_ms", 5000):
            return AutoDecision.neuroblender_fallback(
                f"Time budget too low ({decision.time_budget_ms}ms < 5000ms)"
            )

        await self._select_model(decision, hw_score, hw_details, task, state, ctx)

        logger.info(
            f"[NeuroAutoSelector] → {decision.backend.value}/{decision.model} "
            f"(budget={decision.time_budget_ms}ms, thinking={decision.use_thinking}, "
            f"temp={decision.temperature}, hw={hw_score:.0f}, demand={task.demand_score:.2f})"
        )
        return decision

    # ── Phase 1: Hardware ───────────────────────────────────────────────────

    def _get_hardware(self) -> Tuple[float, HardwareTier, Dict[str, Any]]:
        """Get hardware."""
        now = time.time()
        if now - self._last_hw_time > 30.0:  # Refresh every 30s max
            score, tier, details = self.hardware.analyze()
            self._hw_score = score
            self._hw_tier = tier
            self._hw_details = details
            self._last_hw_time = now
        return self._hw_score, self._hw_tier, self._hw_details

    def refresh_hardware(self) -> None:
        """Force hardware re-detection."""
        self._last_hw_time = 0

    # ── Phase 3: Task Analysis ──────────────────────────────────────────────

    def _analyze_task(self, context: Dict[str, Any]) -> TaskBudget:
        """Analyze task."""
        intent = context.get("intent", "general")
        complexity = context.get("complexity", 0.5)
        user_message = context.get("user_message", "")

        # Load intent cost map from config
        intent_cost_map = (
            self.config.get("auto_mode", {}).get("intent_cost", {})
            or DEFAULT_INTENT_COST
        )
        intent_cost = intent_cost_map.get(intent, 0.4)

        # Message length cost
        msg_len_cost = min(len(user_message) / 2000, 1.0) * 0.2

        # Total demand score
        demand = min(intent_cost + complexity * 0.3 + msg_len_cost, 1.0)

        return TaskBudget(
            demand_score=demand,
            needs_reasoning=demand > 0.6 or intent in ("math", "reasoning"),
            min_quality=intent_cost > 0.4,
            preferred_context_window=8192 if demand > 0.7 else 4096,
        )

    # ── Phase 5: Model Selection ────────────────────────────────────────────

    async def _select_model(
        self,
        decision: AutoDecision,
        hw_score: float,
        hw_details: Dict[str, Any],
        task: TaskBudget,
        state: Dict[str, float],
        context: Dict[str, Any],
    ) -> None:
        """
        Select backend and model based on all prior analysis.
        Priority:
          1. Force override (from context)
          2. Cloud if novelty > 0.7 (quality mode)
          3. Local if hardware capable
          4. Cloud fallback
          5. NeuroBlender if all else fails
        """
        # Priority 1: Force override
        force_backend = context.get("force_backend")
        if force_backend:
            self._apply_force_backend(decision, force_backend)
            return

        # Priority 2: Check available backends
        available = await self._get_available_backends()

        if not available:
            decision.backend = AutoBackendChoice.NEUROBLENDER
            decision.reason = "no_available_backends"
            return

        # Priority 3: Check state-driven cloud preference
        novelty = state.get("theta_novelty", 0.3)
        use_cloud = novelty > 0.7

        # Priority 4: Check local capability
        local_capable = self._is_local_capable(hw_details)

        # Priority 5: Decide
        if use_cloud and any(b in available for b in ("openai", "anthropic", "google")):
            self._select_cloud(decision, available, task)
        elif local_capable and AutoBackendChoice.OLLAMA in available:
            self._select_local(decision, hw_details, task)
        elif AutoBackendChoice.OLLAMA in available:
            self._select_local(decision, hw_details, task)
        elif any(b in available for b in ("openai", "anthropic", "google")):
            self._select_cloud(decision, available, task)
        elif AutoBackendChoice.LLAMA_CPP in available:
            decision.backend = AutoBackendChoice.LLAMA_CPP
            decision.model = "llama-3-8b-instruct"
            decision.reason = "llamacpp_fallback"
        else:
            decision.backend = AutoBackendChoice.NEUROBLENDER
            decision.reason = "no_compatible_backend"

    def _apply_force_backend(self, decision: AutoDecision, force: str) -> None:
        """Handle force_backend override."""
        force = force.lower().replace("-", "_")
        if force in ("neuroblender", "none"):
            decision.backend = AutoBackendChoice.NEUROBLENDER
        elif force in ("llamacpp", "llama_cpp"):
            decision.backend = AutoBackendChoice.LLAMA_CPP
            decision.model = "llama-3-8b-instruct"
        elif force in ("ollama",):
            decision.backend = AutoBackendChoice.OLLAMA
            decision.model = self._recommend_ollama_model(self._hw_details)
        elif force in ("openai",):
            decision.backend = AutoBackendChoice.OPENAI
            decision.model = "gpt-4o-mini"
        elif force in ("anthropic",):
            decision.backend = AutoBackendChoice.ANTHROPIC
            decision.model = "claude-3-sonnet"
        decision.reason = f"force_backend:{force}"

    def _is_local_capable(self, hw_details: Dict[str, Any]) -> bool:
        """Check if hardware can run local LLM decently."""
        ram = hw_details.get("ram_total_gb", 0)
        vram = hw_details.get("vram_mb", 0)
        accelerator = hw_details.get("accelerator_type", "none")
        return ram >= 4 and (vram >= 2048 or accelerator != "none")

    def _select_local(
        self, decision: AutoDecision, hw_details: Dict[str, Any], task: TaskBudget
    ) -> None:
        """Select local Ollama model."""
        decision.backend = AutoBackendChoice.OLLAMA
        decision.model = self._recommend_ollama_model(hw_details)

        if task.needs_reasoning:
            # Try to use reasoning model
            ram = hw_details.get("ram_total_gb", 0)
            if ram >= 16:
                decision.model = "deepseek-r1:latest"
            decision.reason = "local_reasoning"
        else:
            decision.reason = "local_general"

    def _select_cloud(
        self, decision: AutoDecision, available: List[AutoBackendChoice], task: TaskBudget
    ) -> None:
        """Select cloud backend by priority."""
        priority = DEFAULT_CLOUD_PRIORITY
        for name in priority:
            for avail in available:
                if name == avail.value:
                    decision.backend = avail
                    break
            if decision.backend != AutoBackendChoice.OLLAMA:
                break

        if decision.backend == AutoBackendChoice.OPENAI:
            decision.model = "gpt-4o-mini"
            if task.needs_reasoning:
                decision.model = "gpt-4o"
        elif decision.backend == AutoBackendChoice.ANTHROPIC:
            decision.model = "claude-3-sonnet"
            if task.needs_reasoning:
                decision.model = "claude-3-opus"
        elif decision.backend == AutoBackendChoice.GOOGLE:
            decision.model = "gemini-pro"

        decision.reason = f"cloud_{decision.backend.value}"

    def _recommend_ollama_model(self, hw_details: Dict[str, Any]) -> str:
        """Recommend Ollama model based on available RAM."""
        ram = hw_details.get("ram_available_gb", hw_details.get("ram_total_gb", 4))
        vram_mb = hw_details.get("vram_mb", 0)

        thresholds = (
            self.config.get("auto_mode", {}).get("local_model_ram_thresholds")
            or DEFAULT_LOCAL_MODEL_THRESHOLDS
        )

        for entry in thresholds:
            if ram >= entry["min_ram_gb"] and vram_mb >= entry["min_vram_gb"] * 1024:
                return entry["recommend"]

        return "phi:latest"

    async def _get_available_backends(self) -> List[AutoBackendChoice]:
        """
        Check which LLM backends are available.
        Uses lazy import of AngelaLLMService to avoid circular dependency.
        """
        available = []
        try:
            from services.angela_llm_service import get_llm_service

            svc = await get_llm_service()
            if not svc._initialized:
                return []

            for backend_type, backend_obj in svc.backends.items():
                try:
                    if await backend_obj.check_health():
                        name = backend_type.value.lower().replace("-", "_")
                        try:
                            available.append(AutoBackendChoice(name))
                        except ValueError:
                            logger.warning("Invalid AutoBackendChoice name", exc_info=True)
                except Exception:
                    logger.warning("Failed to check backend health for %s", backend_type, exc_info=True)
                    continue
        except Exception as e:
            logger.warning(f"Failed to list available providers: {e}", exc_info=True)
        return available

    # ── Phase 6: Recording ─────────────────────────────────────────────────

    def record_result(self, decision: AutoDecision, actual_ms: float, success: bool) -> None:
        """Record result for learning."""
        self.recorder.record(decision, actual_ms, success)

    def flush_records(self) -> None:
        """Flush pending learn records."""
        self.recorder.flush_sync()
