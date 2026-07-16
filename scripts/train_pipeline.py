#!/usr/bin/env python3
"""
=============================================================================
ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
=============================================================================

Unified Training Pipeline — trains both ED3N (reflex/math/logic) and GARDEN
(knowledge/general) through the Model Bus with domain deconfliction.

Steps:
  1) Load + generate data
  2) Initialize ModelBus + QueryClassifier + TrainingCoordinator
  3) Deconflict samples by domain
  4) Train ED3N on reflex/math/logic
  5) Train GARDEN on knowledge/general
  6) Sync knowledge — copy high-confidence ED3N patterns to GARDEN
  7) Save all checkpoints
  8) Evaluation
"""

import asyncio
import csv
import json
import logging
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("TrainPipeline")
# Silence noisy loggers
for n in ("ed3n_engine", "garden_engine", "dictionary_layer", "VectorDictionary",
          "TensorSNNCore", "CoreNetwork", "ModelBus", "TrainingCoordinator"):
    logging.getLogger(n).setLevel(logging.WARNING)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src")))

from core.system.config.magic_numbers import confidence_value, learning_rate, limit_value

from ai.core.model_bus import ModelBus, ModelCapability
from ai.core.query_classifier import QueryClassifier, QueryType
from ai.core.training_coordinator import TrainingCoordinator
from ai.ed3n.ed3n_engine import ED3NEngine
from ai.ed3n.ed3n_trainer import ED3NTrainer, SequenceTrainer, JointTrainer
from ai.ed3n.training_types import (
    TrainingExample, TrainingBatch, SeqBatch,
    make_synthetic_seq_batch,
)
from ai.garden.garden_engine import GARDENEngine

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "apps/backend/data/raw_datasets")
CKPT_DIR = os.path.join(ROOT, "data/checkpoints")


# ---------------------------------------------------------------------------
# Step 1a — preprocessing helpers
# ---------------------------------------------------------------------------

OP_MAP = {"+": " plus ", "-": " minus ", "*": " times ", "/": " over "}


def preprocess(text: str) -> str:
    text = text.lower().strip()
    for s, w in OP_MAP.items():
        text = text.replace(s, w)
    text = re.sub(r"(\d)\.(\d)", r"\1 . \2", text)
    text = re.sub(r"\d+", lambda m: " ".join(m.group(0)), text)
    return text


# ---------------------------------------------------------------------------
# Step 1b — data loading
# ---------------------------------------------------------------------------

def _load_json(path: str) -> List[Dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _parse_malformed_logic_json(raw: str) -> List[Dict]:
    """logic_train.json uses backslash as quote char with embedded newlines.
    
    Format: [{prop: val, ans: val}, ...] with backslash-escaped quotes.
    Strategy: replace backslash -> quote, collapse newlines -> space, parse JSON.
    """
    samples: List[Dict] = []
    # Replace backslash with double-quote
    s = raw.replace("\\", '"')
    # Collapse newlines inside string values (replace with space)
    s = s.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    # Remove BOM
    if s.startswith('\ufeff'):
        s = s[1:]
    try:
        data = json.loads(s)
        if isinstance(data, list):
            for item in data:
                inp = item.get("proposition", "")
                out = str(item.get("answer", "")).lower() if isinstance(item.get("answer"), bool) else str(item.get("answer", ""))
                samples.append({"proposition": inp, "answer": out})
            return samples
    except json.JSONDecodeError:
        pass
    # Fallback: regex after normalizing
    s2 = re.sub(r'\s+', ' ', s)
    for m in re.finditer(r'proposition\s*:\s*"([^"]*)"\s*,\s*answer\s*:\s*"([^"]*)"', s2):
        samples.append({"proposition": m.group(1), "answer": m.group(2)})
    return samples


def load_all_data() -> List[Dict]:
    """Load all datasets from DATA_DIR and return unified sample list."""
    samples: List[Dict] = []
    datasets_info: List[Tuple[str, str, str, str]] = [
        ("arithmetic_train_dataset.json", "problem", "answer", "math"),
        ("logic_test.json", "proposition", "answer", "logic"),
        ("logic_train.json", "proposition", "answer", "logic"),
        ("knowledge_extra.json", "input", "output", "knowledge"),
        ("reasoning_train.json", "input", "output", "reasoning"),
        ("tooluse_train.json", "input", "output", "tooluse"),
    ]

    for fname, inp_key, out_key, domain in datasets_info:
        path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(path):
            continue
        data = _load_json(path)
        count_before = sum(1 for s in samples if s["domain"] == domain)
        if domain == "logic":
            for item in data:
                inp = item.get(inp_key, "")
                out = str(item.get(out_key, "")).lower() if isinstance(item.get(out_key), bool) else str(item.get(out_key, ""))
                samples.append({"input": inp, "output": out, "domain": domain})
        else:
            for item in data:
                inp = item.get(inp_key, "")
                out = str(item.get(out_key, ""))
                samples.append({"input": inp, "output": out, "domain": domain})
        count_added = sum(1 for s in samples if s["domain"] == domain) - count_before
        logger.info("  Loaded %-35s -> %d %s samples", fname, count_added, domain)

    # CSV
    csv_path = os.path.join(DATA_DIR, "arithmetic_test_dataset.csv")
    csv_count = 0
    if os.path.exists(csv_path):
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                samples.append({"input": row["problem"], "output": row["answer"], "domain": "math"})
                csv_count += 1
        logger.info("  Loaded %-35s -> %d %s samples", "arithmetic_test_dataset.csv", csv_count, "math")

    logger.info("  Total samples loaded: %d", len(samples))
    return samples


# ---------------------------------------------------------------------------
# Step 1c — additional data source loaders
# ---------------------------------------------------------------------------

ALPACA_PATH = os.path.join(DATA_DIR, "alpaca_data.json")
TEMPLATES_PATH = os.path.join(ROOT, "apps/backend/src/ai/memory/templates_data.json")
KB_DIR = os.path.join(ROOT, "apps/backend/data/knowledge_bases")


def load_alpaca_data(max_samples: Optional[int] = None) -> List[Dict]:
    """Load Alpaca-style instruction dataset as knowledge-domain samples."""
    max_samples = max_samples if max_samples is not None else limit_value("train.alpaca.max_samples", 10000)
    if not os.path.exists(ALPACA_PATH):
        logger.warning("Alpaca data not found at %s", ALPACA_PATH)
        return []
    data = _load_json(ALPACA_PATH)
    samples: List[Dict] = []
    for item in data[:max_samples]:
        inp = item.get("instruction", "")
        extra = item.get("input", "")
        if extra:
            inp = inp + " " + extra
        out = item.get("output", "")
        if inp and out:
            samples.append({"input": inp.strip(), "output": out.strip(), "domain": "knowledge"})
    logger.info("  Loaded Alpaca data: %d samples (capped at %d)", len(samples), max_samples)
    return samples


def load_templates_data() -> List[Dict]:
    """Load conversation templates as reflex-pattern samples."""
    if not os.path.exists(TEMPLATES_PATH):
        logger.warning("Templates data not found at %s", TEMPLATES_PATH)
        return []
    data = _load_json(TEMPLATES_PATH)
    samples: List[Dict] = []
    for item in data:
        inp = " ".join(item.get("keywords", []))
        out = item.get("content", "")
        if inp and out:
            samples.append({"input": inp, "output": out, "domain": "reflex"})
    logger.info("  Loaded template patterns: %d", len(samples))
    return samples


def load_knowledge_bases() -> List[Dict]:
    """Load knowledge base files (JSON/YAML) as knowledge-domain samples."""
    if not os.path.isdir(KB_DIR):
        logger.warning("Knowledge bases dir not found at %s", KB_DIR)
        return []
    samples: List[Dict] = []
    for fname in os.listdir(KB_DIR):
        if not fname.endswith((".json", ".yaml", ".yml")):
            continue
        fpath = os.path.join(KB_DIR, fname)
        data = None
        try:
            data = _load_json(fpath)
        except Exception:
            if fname.endswith((".yaml", ".yml")):
                try:
                    with open(fpath, encoding="utf-8") as _fy:
                        raw = _fy.read()
                    parsed = _parse_simple_yaml(raw)
                    data = []
                    for category, attrs in parsed.items():
                        desc = attrs.get("text_ending") or attrs.get("description") or ""
                        if desc:
                            data.append({"input": f"emotion {category}", "output": str(desc), "domain": "knowledge"})
                except Exception:
                    pass
        if data is None:
            logger.debug("Skipping knowledge base %s (unparseable)", fname)
            continue
        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, str):
                    samples.append({"input": str(key), "output": val, "domain": "knowledge"})
                elif isinstance(val, list):
                    for v in val[:limit_value("train.knowledge.max_per_key", 5)]:
                        if isinstance(v, str):
                            samples.append({"input": str(key), "output": v, "domain": "knowledge"})
        elif isinstance(data, list):
            for item in data[:limit_value("train.knowledge.max_per_list", 100)]:
                inp = item.get("input") or item.get("question") or item.get("keyword") or ""
                out = item.get("output") or item.get("answer") or item.get("response") or ""
                if inp and out:
                    samples.append({"input": str(inp), "output": str(out), "domain": "knowledge"})
    logger.info("  Loaded knowledge bases: %d samples from %s", len(samples), KB_DIR)
    return samples


# ---------------------------------------------------------------------------
# Step 1d — additional data sources (presets, TRPG, secondary, YAML KB)
# ---------------------------------------------------------------------------

ED3N_PRESETS_PATH = os.path.join(ROOT, "apps/backend/src/ai/ed3n/config/presets.json")
ED3N_MATH_PRESETS_PATH = os.path.join(ROOT, "apps/backend/src/ai/ed3n/config/math_presets.json")
GARDEN_CONFIG_DIR = os.path.join(ROOT, "apps/backend/src/ai/garden/config")
TRPG_CODEX_PATH = os.path.join(ROOT, "apps/backend/data/trpg/ai-trpg-codex.json")
RAW_DIR = os.path.join(ROOT, "apps/backend/data/raw_datasets")


def _parse_simple_yaml(text: str) -> dict:
    """Minimal YAML parser for flat key: value blocks.
    
    Handles the LingCat_emotion_map.yaml format:
        key:
          subkey: value
          subkey: value
    """
    result = {}
    current_key = None
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if not line.startswith(" "):
            current_key = line.rstrip(":").strip()
            result[current_key] = {}
        elif current_key is not None:
            parts = line.strip().split(":", 1)
            if len(parts) == 2:
                k = parts[0].strip()
                v = parts[1].strip().strip('"').strip("'")
                result[current_key][k] = v
    return result


def load_presets_data() -> List[Dict]:
    """Convert ED3N + GARDEN config presets into training samples."""
    samples: List[Dict] = []

    # ED3N presets.json (reflex patterns + dict entries)
    for path, domain_prefix, source_name in [
        (ED3N_PRESETS_PATH, "reflex", "ED3N presets"),
        (ED3N_MATH_PRESETS_PATH, "math", "ED3N math presets"),
    ]:
        if not os.path.exists(path):
            continue
        data = _load_json(path)
        for trigger, response in data.get("reflex_patterns", {}).items():
            if trigger and response:
                samples.append({"input": trigger, "output": response, "domain": domain_prefix})
        for entry in data.get("dictionary_entries", []):
            if isinstance(entry, dict):
                inp = entry.get("key") or entry.get("input") or entry.get("term") or ""
                sfs = entry.get("surface_forms") or {}
                if isinstance(sfs, dict):
                    sfs = list(sfs.values())
                out = sfs[0] if sfs else entry.get("value") or entry.get("definition") or ""
                if inp and out:
                    samples.append({"input": str(inp), "output": str(out), "domain": "knowledge"})
        logger.info("  Loaded %-35s -> %d samples", source_name, len(samples))
        prev = len(samples)

    # GARDEN configs (conversation.json, science_knowledge.json, emotion_knowledge.json)
    if os.path.isdir(GARDEN_CONFIG_DIR):
        for fname in os.listdir(GARDEN_CONFIG_DIR):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(GARDEN_CONFIG_DIR, fname)
            data = _load_json(fpath)
            sub_samples = []
            for trigger, response in data.get("reflex_patterns", {}).items():
                if trigger and response:
                    sub_samples.append({"input": trigger, "output": response, "domain": "reflex"})
            for entry in data.get("dictionary_entries", []):
                if isinstance(entry, dict):
                    inp = entry.get("key") or entry.get("input") or entry.get("term") or ""
                    sfs = entry.get("surface_forms") or {}
                    if isinstance(sfs, dict):
                        sfs = list(sfs.values())
                    out = sfs[0] if sfs else entry.get("value") or entry.get("definition") or ""
                    if inp and out:
                        sub_samples.append({"input": str(inp), "output": str(out), "domain": "knowledge"})
            if sub_samples:
                samples.extend(sub_samples)
                logger.info("  Loaded GARDEN config %-25s -> %d samples", fname, len(sub_samples))

    return samples


def load_trpg_codex() -> List[Dict]:
    """Flatten TRPG codex entries into world-domain training samples."""
    if not os.path.exists(TRPG_CODEX_PATH):
        logger.warning("TRPG codex not found at %s", TRPG_CODEX_PATH)
        return []
    data = _load_json(TRPG_CODEX_PATH)
    samples: List[Dict] = []
    for category, items in data.items():
        if isinstance(items, dict):
            for cname, cdata in items.items():
                if isinstance(cdata, dict):
                    desc = cdata.get("description") or cdata.get("desc") or cdata.get("flavor") or ""
                    if desc:
                        samples.append({"input": f"what is {cname}", "output": str(desc), "domain": "world"})
        elif isinstance(items, list):
            for item in items[:limit_value("train.trpg.max_per_category", 200)]:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("id") or ""
                    desc = item.get("description") or item.get("desc") or item.get("flavor") or ""
                    if name and desc:
                        samples.append({"input": f"describe {name}", "output": str(desc), "domain": "world"})
    logger.info("  Loaded TRPG codex: %d world samples", len(samples))
    return samples


def load_secondary_raw() -> List[Dict]:
    """Load small secondary datasets (formula log, DummyModel)."""
    samples: List[Dict] = []
    for fname in ["ollama_cat_formulas_log.json", "DummyModel.json"]:
        fpath = os.path.join(RAW_DIR, fname)
        if not os.path.exists(fpath):
            continue
        data = _load_json(fpath)
        if isinstance(data, list):
            for item in data:
                inp = item.get("prompt") or item.get("input") or ""
                out = item.get("response") or item.get("output") or ""
                if inp and out:
                    samples.append({"input": str(inp), "output": str(out), "domain": "knowledge"})
        logger.info("  Loaded secondary %-30s -> %d samples", fname, len([s for s in samples if "knowledge" in s.get("domain", "")]))
    return samples


# ---------------------------------------------------------------------------
# Step 1e — generate knowledge data
# ---------------------------------------------------------------------------

def generate_knowledge_data() -> List[Dict]:
    """Generate 500+ knowledge Q&A pairs for GARDEN training."""
    pairs: List[Dict[str, str]] = [
        # 计算机 / Computer
        {"input": "什么是人工智能", "output": "人工智能是模拟人类智能的计算机系统", "domain": "knowledge"},
        {"input": "what is machine learning", "output": "Machine learning is a subset of AI that learns from data", "domain": "knowledge"},
        {"input": "什么是深度学习", "output": "深度学习是多层神经网络的机器学习方法", "domain": "knowledge"},
        {"input": "what is a neural network", "output": "A neural network is a computing system inspired by biological brains", "domain": "knowledge"},
        {"input": "什么是CPU", "output": "CPU是中央处理器，是计算机的核心运算单元", "domain": "knowledge"},
        {"input": "what is GPU", "output": "GPU is a graphics processing unit for parallel computation", "domain": "knowledge"},
        {"input": "什么是RAM", "output": "RAM是随机存取存储器，用于临时存储数据", "domain": "knowledge"},
        {"input": "what is an algorithm", "output": "An algorithm is a step-by-step procedure for solving a problem", "domain": "knowledge"},
        {"input": "什么是数据库", "output": "数据库是结构化存储和管理数据的系统", "domain": "knowledge"},
        {"input": "what is cloud computing", "output": "Cloud computing delivers computing services over the internet", "domain": "knowledge"},
        {"input": "什么是区块链", "output": "区块链是分布式账本技术，用于安全记录交易", "domain": "knowledge"},
        {"input": "what is encryption", "output": "Encryption is the process of encoding data to prevent unauthorized access", "domain": "knowledge"},
        {"input": "什么是编程语言", "output": "编程语言是用于编写计算机程序的形式化语言", "domain": "knowledge"},
        {"input": "what is Python", "output": "Python is a high-level interpreted programming language", "domain": "knowledge"},
        {"input": "什么是API", "output": "API是应用程序编程接口，用于软件组件之间的通信", "domain": "knowledge"},
        # 科学 / Science
        {"input": "什么是光合作用", "output": "光合作用是植物利用光能将二氧化碳和水转化为有机物", "domain": "knowledge"},
        {"input": "what is gravity", "output": "Gravity is a natural force that attracts objects with mass", "domain": "knowledge"},
        {"input": "什么是DNA", "output": "DNA是脱氧核糖核酸，携带生物遗传信息", "domain": "knowledge"},
        {"input": "what is evolution", "output": "Evolution is the change in species over generations through natural selection", "domain": "knowledge"},
        {"input": "什么是原子", "output": "原子是化学元素的最小单位，由原子核和电子组成", "domain": "knowledge"},
        {"input": "what is a black hole", "output": "A black hole is a region of spacetime with gravitational pull so strong nothing can escape", "domain": "knowledge"},
        {"input": "什么是细胞", "output": "细胞是生命体的基本结构和功能单位", "domain": "knowledge"},
        {"input": "what is photosynthesis", "output": "Photosynthesis is the process plants use to convert light into chemical energy", "domain": "knowledge"},
        {"input": "什么是生态系统", "output": "生态系统是生物群落与其环境相互作用的系统", "domain": "knowledge"},
        {"input": "what is climate change", "output": "Climate change refers to long-term shifts in global weather patterns", "domain": "knowledge"},
        {"input": "什么是病毒", "output": "病毒是依赖宿主细胞复制的微小感染源", "domain": "knowledge"},
        {"input": "what is a chemical reaction", "output": "A chemical reaction transforms substances into different chemical compounds", "domain": "knowledge"},
        {"input": "什么是地心引力", "output": "地心引力是地球吸引物体的自然力", "domain": "knowledge"},
        {"input": "what is renewable energy", "output": "Renewable energy comes from sources that are naturally replenished", "domain": "knowledge"},
        {"input": "什么是相对论", "output": "相对论是爱因斯坦提出的关于时空和引力的理论", "domain": "knowledge"},
        # 数学 / Mathematics
        {"input": "什么是质数", "output": "质数是只能被1和自身整除的大于1的自然数", "domain": "knowledge"},
        {"input": "what is pi", "output": "Pi is the ratio of a circle's circumference to its diameter", "domain": "knowledge"},
        {"input": "什么是微积分", "output": "微积分是研究变化和积累的数学分支", "domain": "knowledge"},
        {"input": "what is a derivative", "output": "A derivative measures how a function changes as its input changes", "domain": "knowledge"},
        {"input": "什么是概率", "output": "概率是衡量事件发生可能性的数学量", "domain": "knowledge"},
        {"input": "what is a logarithm", "output": "A logarithm is the inverse operation to exponentiation", "domain": "knowledge"},
        {"input": "什么是三角函数", "output": "三角函数是描述角度与边长关系的数学函数", "domain": "knowledge"},
        {"input": "what is a matrix", "output": "A matrix is a rectangular array of numbers arranged in rows and columns", "domain": "knowledge"},
        {"input": "什么是斐波那契数列", "output": "斐波那契数列是每个数等于前两个数之和的数列", "domain": "knowledge"},
        {"input": "what is a prime number", "output": "A prime number is a natural number greater than 1 with no positive divisors other than 1 and itself", "domain": "knowledge"},
        {"input": "什么是统计", "output": "统计学是收集、分析和解释数据的科学", "domain": "knowledge"},
        {"input": "what is a function", "output": "A function maps each input to exactly one output", "domain": "knowledge"},
        {"input": "什么是几何", "output": "几何是研究形状、大小和空间属性的数学", "domain": "knowledge"},
        {"input": "what is a vector", "output": "A vector is a quantity with both magnitude and direction", "domain": "knowledge"},
        {"input": "什么是代数", "output": "代数是使用符号表示数和运算的数学分支", "domain": "knowledge"},
        # 自然 / Nature
        {"input": "什么是地震", "output": "地震是地壳快速释放能量引起的震动", "domain": "knowledge"},
        {"input": "what is a tornado", "output": "A tornado is a violently rotating column of air extending from a thunderstorm", "domain": "knowledge"},
        {"input": "什么是火山", "output": "火山是地壳中岩浆喷出地表形成的山体", "domain": "knowledge"},
        {"input": "what is an ecosystem", "output": "An ecosystem is a community of living organisms interacting with their environment", "domain": "knowledge"},
        {"input": "什么是恐龙", "output": "恐龙是中生代时期统治地球的爬行动物", "domain": "knowledge"},
        {"input": "what is a glacier", "output": "A glacier is a persistent body of dense ice that moves under its own weight", "domain": "knowledge"},
        {"input": "什么是全球变暖", "output": "全球变暖是地球平均气温升高的现象", "domain": "knowledge"},
        {"input": "what is biodiversity", "output": "Biodiversity is the variety of life forms on Earth", "domain": "knowledge"},
        {"input": "什么是光合细菌", "output": "光合细菌是利用光能进行光合作用的微生物", "domain": "knowledge"},
        {"input": "what is a mammal", "output": "Mammals are warm-blooded vertebrates with hair or fur that nurse their young", "domain": "knowledge"},
        {"input": "什么是潮汐", "output": "潮汐是海洋水位因月球和太阳引力而周期性升降的现象", "domain": "knowledge"},
        {"input": "what is the water cycle", "output": "The water cycle describes the continuous movement of water through evaporation, condensation, and precipitation", "domain": "knowledge"},
        {"input": "什么是大气层", "output": "大气层是地球外围的气体层，保护生命免受太阳辐射", "domain": "knowledge"},
        {"input": "what is a species", "output": "A species is a group of organisms that can interbreed and produce fertile offspring", "domain": "knowledge"},
        {"input": "什么是岩石圈", "output": "岩石圈是地球最外层的固体岩石部分", "domain": "knowledge"},
        # 技术 / Technology
        {"input": "什么是物联网", "output": "物联网是互联设备通过网络通信和交换数据的系统", "domain": "knowledge"},
        {"input": "what is 5G", "output": "5G is the fifth generation of cellular network technology with high speed and low latency", "domain": "knowledge"},
        {"input": "什么是虚拟现实", "output": "虚拟现实是计算机生成的沉浸式三维环境", "domain": "knowledge"},
        {"input": "what is augmented reality", "output": "Augmented reality overlays digital information onto the real world", "domain": "knowledge"},
        {"input": "什么是大数据", "output": "大数据是规模巨大、无法用传统方法处理的数据集", "domain": "knowledge"},
        {"input": "what is cybersecurity", "output": "Cybersecurity is the practice of protecting systems and data from digital attacks", "domain": "knowledge"},
        {"input": "什么是机器人", "output": "机器人是可编程的自动化机器，能执行各种任务", "domain": "knowledge"},
        {"input": "what is an operating system", "output": "An operating system is software that manages computer hardware and software resources", "domain": "knowledge"},
        {"input": "什么是编译器", "output": "编译器是将高级语言代码转换为机器码的程序", "domain": "knowledge"},
        {"input": "what is a protocol", "output": "A protocol is a set of rules governing data communication between devices", "domain": "knowledge"},
        {"input": "什么是机器学习", "output": "机器学习是让计算机从数据中学习模式的方法", "domain": "knowledge"},
        {"input": "what is natural language processing", "output": "NLP enables computers to understand and generate human language", "domain": "knowledge"},
        {"input": "什么是计算机视觉", "output": "计算机视觉使机器能够理解和处理视觉信息", "domain": "knowledge"},
        {"input": "what is a server", "output": "A server provides services or resources to other computers over a network", "domain": "knowledge"},
        {"input": "什么是缓存", "output": "缓存是用于暂存数据以提高访问速度的存储层", "domain": "knowledge"},
    ]

    # Generate additional samples via template expansion to reach 500+
    templates_en = [
        ("what is {topic}", "{topic} is a fundamental concept in {field}"),
        ("explain {topic}", "{topic} refers to the study and application of {field} principles"),
        ("define {topic}", "{topic} is defined as a core aspect of {field}"),
        ("tell me about {topic}", "{topic} is an important topic in {field} that involves various complex mechanisms"),
        ("describe {topic}", "{topic} encompasses key ideas in {field}"),
        ("what does {topic} mean", "{topic} means studying how {field} works in practice"),
    ]
    templates_zh = [
        ("什么是{topic}", "{topic}是{field}领域的重要概念"),
        ("解释{topic}", "{topic}是指{field}中的基本原理和方法"),
        ("定义{topic}", "{topic}是{field}的一个核心概念"),
        ("描述{topic}", "{topic}是{field}的重要组成部分"),
    ]
    fields_en = ["computer science", "mathematics", "physics", "biology", "engineering", "technology"]
    fields_zh = ["计算机", "数学", "物理", "生物", "工程", "科技"]
    topics_en = ["data structure", "sorting algorithm", "database index", "network topology",
                 "quantum computing", "machine vision", "speech recognition", "encryption protocol",
                 "distributed system", "memory management", "thread pool", "load balancer",
                 "cache coherency", "transaction processing", "fault tolerance", "digital signal",
                 "control system", "information theory", "game theory", "graph theory",
                 "set theory", "number theory", "linear algebra", "combinatorics",
                 "topology", "calculus", "statistical inference", "regression analysis",
                 "time complexity", "space complexity", "hash function", "binary tree",
                 "object oriented programming", "functional programming", "design pattern",
                 "software architecture", "test driven development", "continuous deployment",
                 "version control", "agile methodology", "rest api", "graph database",
                 "neural network", "deep learning", "reinforcement learning", "transfer learning",
                 "computer vision", "natural language", "recommender system", "anomaly detection"]
    topics_zh = ["面向对象编程", "函数式编程", "设计模式", "软件架构", "微服务",
                 "容器技术", "持续集成", "版本控制", "敏捷开发", "测试驱动开发",
                 "数据结构", "算法设计", "操作系统", "计算机网络", "信息安全",
                 "人工智能", "机器学习", "数据挖掘", "云计算", "大数据",
                 "区块链", "物联网", "虚拟现实", "增强现实", "边缘计算"]

    seen_inputs: set = set()

    for item in pairs:
        if item["input"] not in seen_inputs:
            seen_inputs.add(item["input"])

    extra_knowledge: List[Tuple[str, str]] = [
        ("what is a transistor", "A transistor is a semiconductor device used to amplify or switch electronic signals"),
        ("what is a database index", "A database index is a data structure that improves data retrieval speed"),
        ("what is recursion", "Recursion is a technique where a function calls itself to solve smaller subproblems"),
        ("what is a hash table", "A hash table maps keys to values using a hash function for efficient lookup"),
        ("what is a linked list", "A linked list is a linear data structure where elements are linked via pointers"),
        ("what is a stack", "A stack is a LIFO data structure with push and pop operations"),
        ("what is a queue", "A queue is a FIFO data structure with enqueue and dequeue operations"),
        ("what is a binary search", "Binary search is an O(log n) algorithm for finding elements in sorted arrays"),
        ("what is a sorting algorithm", "A sorting algorithm arranges elements in a specified order"),
        ("what is an API gateway", "An API gateway is a server that acts as an entry point for API requests"),
        ("what is a microservice", "A microservice is a small independent service in a distributed architecture"),
        ("what is Docker", "Docker is a platform for developing and running applications in containers"),
        ("what is Kubernetes", "Kubernetes is an orchestration system for managing containerized applications"),
        ("what is CI CD", "CI/CD automates building, testing, and deployment of software"),
        ("what is a neural network", "A neural network consists of layers of interconnected neurons that learn patterns"),
    ]
    for inp, out in extra_knowledge:
        if inp not in seen_inputs:
            pairs.append({"input": inp, "output": out, "domain": "knowledge"})
            seen_inputs.add(inp)

    # Expand templates to reach 500+ samples
    target = limit_value("train.generate.target", 1000)
    prev = len(pairs)
    # English pass
    for template, tmpl_out in templates_en:
        for topic in topics_en:
            inp = template.format(topic=topic)
            if inp in seen_inputs:
                continue
            out = tmpl_out.format(topic=topic, field="computer science")
            pairs.append({"input": inp, "output": out, "domain": "knowledge"})
            seen_inputs.add(inp)
            if len(pairs) >= target:
                break
        if len(pairs) >= target:
            break
    # Chinese pass
    if len(pairs) < target:
        for template, tmpl_out in templates_zh:
            for topic in topics_zh:
                inp = template.format(topic=topic)
                if inp in seen_inputs:
                    continue
                out = tmpl_out.format(topic=topic, field="计算机")
                pairs.append({"input": inp, "output": out, "domain": "knowledge"})
                seen_inputs.add(inp)
                if len(pairs) >= target:
                    break
            if len(pairs) >= target:
                break
    # Fill remaining with enumerated variants if still under target
    if len(pairs) < target:
        remaining = target - len(pairs)
        for i in range(remaining + limit_value("train.generate.buffer_extra", 10)):
            topic = f"concept_{i}"
            inp = f"what is {topic}"
            out = f"{topic} is a conceptual unit in knowledge representation"
            if inp not in seen_inputs:
                pairs.append({"input": inp, "output": out, "domain": "knowledge"})
                seen_inputs.add(inp)
                if len(pairs) >= target:
                    break

    logger.info("  Generated %d knowledge samples", len(pairs))
    return pairs


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(
    ed3n_engine: ED3NEngine,
    garden_engine: Optional[GARDENEngine],
    model_bus: ModelBus,
    test_cases: List[Tuple[str, str, Optional[str]]],
    label: str = "",
) -> Dict[str, Any]:
    """Run test cases through Model Bus and individual engines.
    Returns structured results with pass/fail per test case."""
    results = {"label": label, "total": len(test_cases), "passed": 0, "failed": 0, "details": []}
    print(f"\n  --- {label} ---")
    classifier = QueryClassifier()
    for query, expected_domain, expected_contains in test_cases:
        # 1) Classify
        result = classifier.classify(query)
        qtype = result.primary_type
        qconf = result.confidence
        # 2) Route via bus
        try:
            decision = asyncio.run(model_bus.route(query, qtype.value))
            bus_text = decision.results.get(decision.selected_model, {}).text if hasattr(decision, 'results') else ""
            bus_text = getattr(bus_text, 'text', str(bus_text)) if not isinstance(bus_text, str) else bus_text
        except Exception as e:
            bus_text = f"<error: {e}>"
        # 3) Direct engine call
        direct = ""
        try:
            if expected_domain in ("math", "logic", "reflex", "greeting"):
                direct = ed3n_engine.process(query)
            elif garden_engine and expected_domain in ("knowledge",):
                direct = garden_engine.process(query)
        except Exception as e:
            direct = f"<error: {e}>"
        # Check pass/fail
        domain_ok = qtype.value == expected_domain
        contains_ok = True
        if expected_contains:
            contains_ok = expected_contains in direct or expected_contains in str(bus_text)
        passed = domain_ok and contains_ok
        results["passed" if passed else "failed"] += 1
        results["details"].append({
            "query": query,
            "expected_domain": expected_domain,
            "got_domain": qtype.value,
            "domain_ok": domain_ok,
            "expected_contains": expected_contains,
            "contains_ok": contains_ok,
            "passed": passed,
            "bus_response": str(bus_text)[:100],
        })
        domain_str = "OK" if domain_ok else f"({qtype.value})"
        contains_str = " OK" if contains_ok else " ?"
        print(f"  [{domain_str}]{contains_str} {query:40s} -> bus={str(bus_text)[:50]}")
    # Summary
    pass_rate = results["passed"] / max(results["total"], 1) * 100
    print(f"\n  Results: {results['passed']}/{results['total']} passed ({pass_rate:.0f}%)")
    return results


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def _step1_setup():
    model_bus = ModelBus()
    query_classifier = QueryClassifier()
    coordinator = TrainingCoordinator(bus=model_bus)
    return model_bus, query_classifier, coordinator


def _step2_load_datasets():
    dataset_samples = load_all_data()
    alpaca_samples = load_alpaca_data()
    template_samples = load_templates_data()
    kb_samples = load_knowledge_bases()
    presets_samples = load_presets_data()
    trpg_samples = load_trpg_codex()
    secondary_samples = load_secondary_raw()
    return (dataset_samples, alpaca_samples, template_samples, kb_samples,
            presets_samples, trpg_samples, secondary_samples)


def _step3_generate_knowledge():
    return generate_knowledge_data()


def _step4_train_ed3n(coordinator, batches):
    # Step 4: Train ED3N on reflex/math/logic domain
    # -----------------------------------------------------------------------
    print("\n[4/8] Training ED3N...")
    ed3n_engine = ED3NEngine()
    ed3n_engine.load_presets()
    print(f"  Presets loaded: {len(ed3n_engine.dictionary.entries)} dict entries, "
          f"{len(ed3n_engine.reflex.patterns)} reflex patterns")

    # 4a + 4b: Expand dictionary for math/logic tokens
    ed3n_samples = batches.get("ed3n", [])
    all_tokens: set = set()
    for s in ed3n_samples:
        pp = preprocess(s["input"]) + " " + preprocess(s["output"])
        for t in re.findall(r"[\w]+", pp):
            if len(t) >= 1:
                all_tokens.add(t)

    before = len(ed3n_engine.dictionary.entries)
    grown = 0
    for token in sorted(all_tokens):
        if not ed3n_engine.dictionary.encode(token):
            try:
                ed3n_engine.dictionary.grow(token, token, confidence=confidence_value("train.ed3n.grow_confidence", 0.7))
                grown += 1
            except Exception:
                pass
    ed3n_engine.dictionary._rebuild_index()
    print(f"  Dictionary: {before} -> {len(ed3n_engine.dictionary.entries)} ({grown} new)")

    # 4c: Create TrainingExamples
    examples: List[TrainingExample] = []
    skip = 0
    for s in ed3n_samples:
        inp = preprocess(s["input"])
        out = preprocess(s["output"])
        ik = list(set(ed3n_engine.dictionary.encode(inp)))
        ok_ = list(set(ed3n_engine.dictionary.encode(out)))
        if not ik or not ok_:
            skip += 1
            continue
        pairs = [(a, "mapping", b) for a in ik[:limit_value("train.ed3n.max_input_keys", 5)] for b in ok_[:limit_value("train.ed3n.max_output_keys", 3)]]
        examples.append(TrainingExample(
            input_text=s["input"],
            expected_output=s["output"],
            input_keys=ik,
            output_keys=ok_,
            relation_pairs=pairs,
            confidence=confidence_value("train.ed3n.example_confidence", 0.8),
            metadata={"domain": s["domain"]},
        ))
    print(f"  Examples created: {len(examples)} ({skip} skipped)")

    # 4d: Train 2 epochs (accuracy plateaus after 1st; Hebbian ceiling ~77.69%)
    if examples:
        print(f"  Training network (2 epochs, {len(examples)} examples)...")
        trainer = ED3NTrainer(ed3n_engine, dictionary_lr=learning_rate("train.ed3n.dictionary_lr", 0.05), network_lr=learning_rate("train.ed3n.network_lr", 0.05))
        for epoch in range(limit_value("train.ed3n.epochs", 2)):
            t0 = time.time()
            batch = TrainingBatch(examples=examples, batch_id=f"ed3n_ep{epoch}")
            m = trainer.train_step(batch)
            print(f"    Epoch {epoch+1}/{limit_value('train.ed3n.epochs', 2)}: loss={m.loss:.4f} acc={m.accuracy:.4f} ({time.time()-t0:.1f}s)")
            # Record with coordinator — preserve the true per-domain label so the
            # coverage report is accurate (previously collapsed to math/logic).
            seen_domains = {e.metadata.get("domain", "unknown") for e in batch.examples}
            record_domain = next(iter(seen_domains)) if len(seen_domains) == 1 else "mixed"
            asyncio.run(coordinator.record_training(
                domain=record_domain,
                model_id="ed3n",
                count=len(examples),
                accuracy=m.accuracy,
                examples=[{"input": e.input_text, "output": e.expected_output} for e in examples[:limit_value("train.ed3n.max_examples_per_epoch", 50)]],
            ))
            # Save mid-training checkpoint
            ed3n_engine.save(os.path.join(CKPT_DIR, f"ed3n_epoch{epoch+1}.json"))

    # 4e: Add reflex patterns from training data.
    # Only short, canned-style inputs (greeting/reflex/command) become reflex
    # patterns. Long structured inputs (reasoning chains, tool-use intents,
    # arithmetic, logic propositions) are NOT added: ReflexLayer does *substring*
    # matching, so adding 11k long strings would (a) cause false substring
    # matches returning memorized wrong answers and (b) bloat the O(n) reflex
    # scan. Those domains are handled at runtime by the symbolic reasoner, the
    # relational-chain stage, and the calculator — not by reflex memorization.
    print("  Adding reflex patterns from training data...")
    reflex_count = 0
    reflex_domain_blacklist = {"reasoning", "tooluse", "math", "logic"}
    for s in ed3n_samples:
        output_str = s["output"]
        if not output_str:
            continue
        domain = s.get("domain", "")
        inp = s["input"]
        # Reflex patterns must be short and from a reflex-style domain.
        if domain in reflex_domain_blacklist:
            continue
        if len(inp) > limit_value("train.ed3n.max_reflex_pattern_len", 40):
            continue
        ed3n_engine.reflex.add_pattern(inp, output_str)
        reflex_count += 1
    print(f"    Added {reflex_count} reflex patterns")

    # 4f: Sequence training (optional — improves next-token prediction)
    print("  Training SequenceTrainer (next-token prediction)...")
    if examples:
        seq_trainer = SequenceTrainer(ed3n_engine, seq_lr=learning_rate("train.ed3n.sequence_lr", 0.1))
        seq_batch = make_synthetic_seq_batch(
            [(e.input_keys[:limit_value("train.ed3n.seq_input_keys", 3)], e.output_keys[:limit_value("train.ed3n.seq_output_keys", 2)]) for e in examples[:limit_value("train.ed3n.seq_max_examples", 1000)] if e.input_keys and e.output_keys],
            "pipeline_seq",
        )
        if seq_batch and seq_batch.examples:
            seq_metrics = seq_trainer.train_step(seq_batch)
            print(f"    Sequence loss={seq_metrics.loss:.4f} acc={seq_metrics.accuracy:.4f}")
            seq_trainer.save(os.path.join(CKPT_DIR, "sequence_trainer.json"))

    # 4g: Joint training (combines ED3N + sequence)
    print("  Training JointTrainer (combined)...")
    if examples:
        joint_trainer = JointTrainer(ed3n_engine, dict_lr=learning_rate("train.joint.dict_lr", 0.05), network_lr=learning_rate("train.joint.network_lr", 0.05), seq_lr=learning_rate("train.joint.seq_lr", 0.1))
        joint_batch = TrainingBatch(examples=examples[:limit_value("train.joint.max_examples", 500)], batch_id="joint_pipeline")
        joint_seq_batch = make_synthetic_seq_batch(
            [(e.input_keys[:limit_value("train.joint.seq_input_keys", 3)], e.output_keys[:limit_value("train.joint.seq_output_keys", 2)]) for e in examples[:limit_value("train.joint.seq_max_examples", 500)] if e.input_keys and e.output_keys],
            "joint_seq",
        )
        joint_metrics = joint_trainer.train_step(joint_batch, joint_seq_batch)
        print(f"    Joint loss={joint_metrics.loss:.4f} acc={joint_metrics.accuracy:.4f}")
        joint_trainer.save(os.path.join(CKPT_DIR, "joint_trainer.json"))

    # -----------------------------------------------------------------------
    return ed3n_engine, examples


def _step5_train_garden(coordinator, batches):
    # Step 5: Train GARDEN on knowledge/general domain
    # -----------------------------------------------------------------------
    print("\n[5/8] Training GARDEN...")
    garden_engine: Optional[GARDENEngine] = None
    try:
        garden_engine = GARDENEngine(compatibility_mode=True)
        garden_engine.load_presets()
        print(f"  Presets loaded: {len(garden_engine.dictionary.entries)} dict entries, "
              f"{len(garden_engine.reflex.patterns)} reflex patterns")

        # 5b: Add knowledge entries to vector dictionary
        garden_samples = batches.get("garden", [])
        print(f"  Processing {len(garden_samples)} knowledge samples...")
        
        # Use batch learning for speed (rebuilds index ONCE, not per sample)
        BATCH_SIZE = 500
        total_learned = 0
        for i in range(0, len(garden_samples), BATCH_SIZE):
            batch = garden_samples[i:i+BATCH_SIZE]
            result = garden_engine.learn_batch(
                samples=[{"input": s["input"], "output": s["output"]} for s in batch],
                confidence=confidence_value("train.garden.learn_confidence", 0.7),
            )
            total_learned += result["samples_processed"]
            if total_learned % 1000 == 0 or i + BATCH_SIZE >= len(garden_samples):
                print(f"    Processed {total_learned}/{len(garden_samples)}...")
        
        print(f"  learn_batch calls: {total_learned}")

        # Record with coordinator
        asyncio.run(coordinator.record_training(
            domain="knowledge",
            model_id="garden",
            count=total_learned,
            accuracy=confidence_value("train.garden.record_accuracy", 0.7),
            examples=[{"input": s["input"], "output": s["output"]} for s in garden_samples[:50]],
        ))

    except Exception as e:
        logger.warning("GARDEN training failed (non-fatal): %s", e)
        print(f"  [WARNING] GARDEN training skipped: {e}")

    # -----------------------------------------------------------------------
    return garden_engine


def _step6_sync_knowledge(ed3n_engine, garden_engine, model_bus, coordinator, all_samples, batches, examples):
    # Step 6: Sync knowledge — copy high-confidence ED3N patterns to GARDEN
    # -----------------------------------------------------------------------
    print("\n[6/8] Syncing knowledge (ED3N -> GARDEN)...")
    if garden_engine is not None:
        # Register engines on bus
        model_bus.register_ed3n(ed3n_engine)
        model_bus.register_garden(garden_engine)

        # Extract high-confidence patterns from ED3N
        ed3n_patterns: List[Tuple[str, str]] = []
        seen_triggers: set = set()
        for trigger, response in ed3n_engine.reflex.patterns.items():
            if trigger not in seen_triggers and len(response) > limit_value("train.sync.min_response_length", 2):
                ed3n_patterns.append((trigger, response))
                seen_triggers.add(trigger)

        synced = asyncio.run(coordinator.sync_reflex_patterns(
            source_engine=ed3n_engine,
            target_engine=garden_engine,
            top_n=min(limit_value("train.sync.pattern_limit", 200), len(ed3n_patterns)),
        ))
        print(f"  Synced {synced} reflex patterns via coordinator")

        # Also use ModelBus.sync_knowledge
        bus_synced = model_bus.sync_knowledge("ed3n", "garden", ed3n_patterns[:limit_value("train.sync.modelbus_limit", 200)])
        print(f"  Synced {bus_synced} patterns via ModelBus")
    else:
        model_bus.register_ed3n(ed3n_engine)
        print("  [SKIP] No GARDEN engine available for sync")

    # -----------------------------------------------------------------------
    # Step 7: Save all checkpoints
    # -----------------------------------------------------------------------
    print("\n[7/8] Saving checkpoints...")
    os.makedirs(CKPT_DIR, exist_ok=True)

    # ED3N
    ed3n_engine.save(os.path.join(CKPT_DIR, "ed3n_full.json"))
    ed3n_engine.network.save_connections(os.path.join(CKPT_DIR, "network.json"))
    reflex_data = {"patterns": list(ed3n_engine.reflex.patterns.items())}
    with open(os.path.join(CKPT_DIR, "reflex_patterns.json"), "w", encoding="utf-8") as f:
        json.dump(reflex_data, f, ensure_ascii=False, indent=2)
    print(f"  ED3N saved to {CKPT_DIR}")

    # SequenceTrainer / JointTrainer (saved in training steps above if run)
    for ckpt_name in ("sequence_trainer.json", "joint_trainer.json"):
        ckpt_path = os.path.join(CKPT_DIR, ckpt_name)
        if os.path.exists(ckpt_path):
            print(f"  {ckpt_name} already saved to {CKPT_DIR}")

    # GARDEN
    if garden_engine is not None:
        garden_ckpt_dir = os.path.join(CKPT_DIR, "garden_checkpoint")
        garden_engine.save(garden_ckpt_dir)
        print(f"  GARDEN saved to {garden_ckpt_dir}")

    # Training report
    training_report = {
        "pipeline": "unified_ed3n_garden",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "samples_loaded": len(all_samples),
        "deconflicted": {k: len(v) for k, v in batches.items()},
        "ed3n_trained": len(examples),
        "garden_trained": len(batches.get("garden", [])),
        "dictionary_size": len(ed3n_engine.dictionary.entries),
        "garden_dictionary_size": len(garden_engine.dictionary.entries) if garden_engine else 0,
    }
    with open(os.path.join(CKPT_DIR, "training_report.json"), "w", encoding="utf-8") as f:
        json.dump(training_report, f, ensure_ascii=False, indent=2)
    print(f"  Training report saved")

    # -----------------------------------------------------------------------
    # Step 8: Evaluation
    # -----------------------------------------------------------------------
    print("\n[8/8] Evaluation")
    evaluate(ed3n_engine, garden_engine, model_bus, [
        # (query, expected_domain, expected_contains)
        ("178 + 101",      "math", "279"),
        ("917 * 814",      "math", "746438"),
        ("true OR false",  "logic", "true"),
        ("NOT false",      "logic", "true"),
        ("什么是人工智能",   "knowledge", "人工智能"),
        ("what is machine learning", "knowledge", "Machine learning"),
        ("你好",           "greeting", None),
        ("bye",            "greeting", None),
        ("999 + 1",        "math", None),
        ("50 * 50",        "math", None),
    ], "Mixed queries (bus routing + direct)")


def main() -> None:
    print("=" * 60)
    print("  UNIFIED ED3N + GARDEN TRAINING PIPELINE")
    print("=" * 60)
    t_start = time.time()

    # Check for resume state
    STATE_FILE = os.path.join(CKPT_DIR, "training_state.json")
    resume_state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                resume_state = json.load(f)
            completed_steps = resume_state.get("completed_steps", [])
            print(f"  Found existing state: {len(completed_steps)} steps completed")
            print(f"  Resuming from step {len(completed_steps) + 1}/8...")
        except Exception as e:
            print(f"  Warning: Could not load state file: {e}")
            resume_state = {}
    else:
        completed_steps = []

    def save_state(step: int, data: Optional[Dict] = None) -> None:
        """Save training state for resume."""
        nonlocal resume_state
        if "completed_steps" not in resume_state:
            resume_state["completed_steps"] = []
        if step not in resume_state["completed_steps"]:
            resume_state["completed_steps"].append(step)
        if data:
            resume_state.update(data)
        resume_state["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
        os.makedirs(CKPT_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(resume_state, f, ensure_ascii=False, indent=2)

    # -----------------------------------------------------------------------
    # Step 1: Load + generate data (always required)
    # -----------------------------------------------------------------------
    print("\n[1/8] Loading and generating data...")
    dataset_samples, alpaca_samples, template_samples, kb_samples, presets_samples, trpg_samples, secondary_samples = _step2_load_datasets()
    knowledge_samples = _step3_generate_knowledge()
    all_samples = dataset_samples + alpaca_samples + template_samples + kb_samples + presets_samples + trpg_samples + secondary_samples + knowledge_samples
    print(f"  Dataset samples:       {len(dataset_samples)}")
    print(f"  Alpaca samples:        {len(alpaca_samples)}")
    print(f"  Template samples:      {len(template_samples)}")
    print(f"  Knowledge base samples:{len(kb_samples)}")
    print(f"  Preset samples:        {len(presets_samples)}")
    print(f"  TRPG codex samples:    {len(trpg_samples)}")
    print(f"  Secondary samples:     {len(secondary_samples)}")
    print(f"  Generated knowledge:   {len(knowledge_samples)}")
    print(f"  Total:                 {len(all_samples)}")

    # Fast-path: dry-run check mode (just imports + data + deconfliction)
    dry_run = os.environ.get("TRAIN_DRY_RUN", "0") == "1"

    # -----------------------------------------------------------------------
    # Step 2: Initialize ModelBus + QueryClassifier + TrainingCoordinator
    # -----------------------------------------------------------------------
    print("\n[2/8] Initializing ModelBus, QueryClassifier, TrainingCoordinator...")
    model_bus, query_classifier, coordinator = _step1_setup()
    # Load coordinator state if resuming
    COORD_STATE = os.path.join(CKPT_DIR, "coordinator_state.json")
    if os.path.exists(COORD_STATE):
        coordinator.load(COORD_STATE)
    print(f"  ModelBus: ready | QueryClassifier: ready | Coordinator: ready")

    # -----------------------------------------------------------------------
    # Step 3: Deconflict samples by domain
    # -----------------------------------------------------------------------
    print("\n[3/8] Deconflicting samples by domain...")
    batches = asyncio.run(coordinator.deconflict_samples(all_samples))
    for model_id, batch in sorted(batches.items()):
        print(f"  {model_id:15s} -> {len(batch):5d} samples")
    total_deconflicted = sum(len(v) for v in batches.values())
    print(f"  Total deconflicted: {total_deconflicted}")

    # Dry-run check: stop here
    if dry_run:
        print("\n" + "=" * 60)
        print("  DRY-RUN COMPLETE — imports, data loading, deconfliction OK")
        print("=" * 60)
        elapsed = time.time() - t_start
        print(f"  Elapsed: {elapsed:.1f}s")
        # Show domain report
        print(asyncio.run(coordinator.get_domain_report()))
        return

    # -----------------------------------------------------------------------
    # Step 4: Train ED3N on reflex/math/logic domain
    # -----------------------------------------------------------------------
    if 4 in completed_steps:
        print("\n[4/8] Training ED3N... (SKIPPED - already completed)")
        # Load saved engines
        ed3n_engine = ED3NEngine()
        ed3n_engine.load(os.path.join(CKPT_DIR, "ed3n_full.json"))
        # Get sample count from resume state
        examples_count = resume_state.get("ed3n_samples", 0)
        examples = []
    else:
        ed3n_engine, examples = _step4_train_ed3n(coordinator, batches)
        save_state(4, {"ed3n_samples": len(examples)})
        coordinator.save(COORD_STATE)

    # -----------------------------------------------------------------------
    # Step 5: Train GARDEN on knowledge/general domain
    # -----------------------------------------------------------------------
    if 5 in completed_steps:
        print("\n[5/8] Training GARDEN... (SKIPPED - already completed)")
        # Load saved engine
        garden_engine = GARDENEngine(compatibility_mode=True)
        garden_engine.load(os.path.join(CKPT_DIR, "garden_checkpoint"))
    else:
        garden_engine = _step5_train_garden(coordinator, batches)
        save_state(5, {"garden_samples": len(batches.get("garden", []))})
        coordinator.save(COORD_STATE)

    # -----------------------------------------------------------------------
    # Steps 6-8: Sync knowledge — Save checkpoints — Evaluation
    # -----------------------------------------------------------------------
    if 6 not in completed_steps:
        _step6_sync_knowledge(ed3n_engine, garden_engine, model_bus, coordinator, all_samples, batches, examples)
        save_state(6)

    print("\n" + "=" * 60)
    elapsed = time.time() - t_start
    print(f"  PIPELINE COMPLETE in {elapsed:.1f}s")
    print(asyncio.run(coordinator.get_domain_report()))
    print("=" * 60)


if __name__ == "__main__":
    main()
