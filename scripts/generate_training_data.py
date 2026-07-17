#!/usr/bin/env python3
"""
=============================================================================
ANGELA-MATRIX: [L3] [βγδ] [B] [L3]
=============================================================================

Generate training data for ED3N + GARDEN pipeline.
Fills gaps: logic_train.json (10K boolean logic) + expanded knowledge data.
"""

import json
import logging
import os
import random

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("GenData")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                        "apps/backend/data/raw_datasets"))


# ---------------------------------------------------------------------------
# 1. Boolean logic generators
# ---------------------------------------------------------------------------

BOOL_OPS = {
    "and":   lambda a, b: a and b,
    "or":    lambda a, b: a or b,
    "xor":   lambda a, b: a != b,
    "nand":  lambda a, b: not (a and b),
    "nor":   lambda a, b: not (a or b),
}

# Natural-language patterns for each operator
PATTERNS_CN = {
    "and": [
        "{0} 和 {1} 是否都成立",
        "{0} 与 {1} 同时为真",
        "如果 {0} 而且 {1}",
        "{0} 并且 {1} 的结果",
    ],
    "or": [
        "{0} 或 {1} 是否成立",
        "{0} 或者 {1} 至少一个为真",
        "如果 {0} 或 {1}",
    ],
    "xor": [
        "{0} 和 {1} 是否恰好一个成立",
        "{0} 与 {1} 互斥",
        "要么 {0} 要么 {1} 但不能同时",
    ],
    "nand": [
        "{0} 和 {1} 不都成立",
        "并非 {0} 和 {1} 同时为真",
        "{0} 与 {1} 不能同时成立",
    ],
    "nor": [
        "{0} 和 {1} 都不成立",
        "既不是 {0} 也不是 {1}",
        "{0} 与 {1} 均为假",
    ],
}

PATTERNS_EN = {
    "and": [
        "{0} and {1}",
        "both {0} and {1}",
        "{0} AND {1}",
    ],
    "or": [
        "{0} or {1}",
        "either {0} or {1}",
        "{0} OR {1}",
    ],
    "xor": [
        "{0} xor {1}",
        "exactly one of {0} or {1}",
        "{0} XOR {1}",
    ],
    "nand": [
        "not ({0} and {1})",
        "{0} nand {1}",
        "it is not the case that both {0} and {1}",
    ],
    "nor": [
        "neither {0} nor {1}",
        "not ({0} or {1})",
        "{0} nor {1}",
    ],
}

# Atomic propositions in CN/EN
ATOMS_CN = [
    "今天天气好", "明天会下雨", "太阳从东边升起", "水是液体",
    "地球是圆的", "月亮绕着地球转", "猫是哺乳动物", "鱼会游泳",
    "鸟会飞", "温度高于零度", "速度大于零", "压力正常",
    "电源已接通", "信号强度足够", "门是开着的", "灯是亮的",
    "程序已启动", "数据已备份", "网络已连接", "用户已登录",
]
ATOMS_EN = [
    "the sky is blue", "water is wet", "the sun is hot",
    "gravity exists", "light travels fast", "sound needs a medium",
    "energy is conserved", "entropy increases", "the earth orbits the sun",
    "plants need sunlight", "oxygen supports combustion", "hydrogen is flammable",
    "the system is online", "the database is ready", "the cache is warm",
    "the queue is empty", "the job is complete", "the file exists",
]


def gen_bool_val() -> bool:
    return random.random() < 0.5


def gen_logic_sample() -> dict:
    """Generate one boolean logic training sample."""
    op_name = random.choice(list(BOOL_OPS.keys()))
    op_fn = BOOL_OPS[op_name]
    a_val = gen_bool_val()
    b_val = gen_bool_val()
    answer = op_fn(a_val, b_val)

    # Pick Chinese or English
    if random.random() < 0.5:
        a_text = random.choice(ATOMS_CN)
        b_text = random.choice(ATOMS_CN)
        while b_text == a_text:
            b_text = random.choice(ATOMS_CN)
        pattern = random.choice(PATTERNS_CN[op_name])
        proposition = pattern.format(a_text, b_text)
    else:
        a_text = random.choice(ATOMS_EN)
        b_text = random.choice(ATOMS_EN)
        while b_text == a_text:
            b_text = random.choice(ATOMS_EN)
        pattern = random.choice(PATTERNS_EN[op_name])
        proposition = pattern.format(a_text, b_text)

    return {"proposition": proposition, "answer": answer}


def gen_logic_samples(count: int = 10000) -> list:
    samples = [gen_logic_sample() for _ in range(count)]
    logger.info("Generated %d boolean logic samples", len(samples))
    return samples


# ---------------------------------------------------------------------------
# 2. Expanded knowledge data (add to the template-based generator in pipeline)
# ---------------------------------------------------------------------------

EXTRA_KNOWLEDGE_CN = [
    ("什么是算法", "算法是解决特定问题的步骤序列"),
    ("什么是数据库", "数据库是结构化存储和管理数据的系统"),
    ("什么是操作系统", "操作系统是管理计算机硬件和软件资源的程序"),
    ("什么是编程语言", "编程语言是人与计算机通信的形式语言"),
    ("什么是变量", "变量是存储数据的命名内存位置"),
    ("什么是函数", "函数是执行特定任务的代码块"),
    ("什么是类", "类是面向对象编程中创建对象的蓝图"),
    ("什么是对象", "对象是类的实例，包含数据和行为"),
    ("什么是数组", "数组是存储相同类型元素的集合"),
    ("什么是链表", "链表是由节点组成的线性数据结构"),
    ("什么是栈", "栈是后进先出的数据结构"),
    ("什么是队列", "队列是先进先出的数据结构"),
    ("什么是树", "树是分层结构的数据结构"),
    ("什么是图", "图是由节点和边组成的数据结构"),
    ("什么是哈希表", "哈希表是通过键直接访问的数据结构"),
    ("什么是递归", "递归是函数调用自身的编程技术"),
    ("什么是迭代", "迭代是重复执行代码块的过程"),
    ("什么是排序", "排序是将数据按特定顺序排列的过程"),
    ("什么是搜索", "搜索是在数据集中查找特定元素的过程"),
    ("什么是时间复杂度", "时间复杂度是算法执行时间的度量"),
    ("什么是空间复杂度", "空间复杂度是算法使用内存的度量"),
    ("什么是加密", "加密是将数据转换为不可读形式的过程"),
    ("什么是解密", "解密是将加密数据恢复为原始形式的过程"),
    ("什么是网络协议", "网络协议是计算机通信的规则集合"),
    ("什么是IP地址", "IP地址是网络中设备的唯一标识符"),
    ("什么是域名", "域名是网站的人类可读地址"),
    ("什么是HTTP", "HTTP是超文本传输协议"),
    ("什么是HTTPS", "HTTPS是安全的超文本传输协议"),
    ("什么是API", "API是应用程序编程接口"),
    ("什么是JSON", "JSON是轻量级数据交换格式"),
    ("什么是XML", "XML是可扩展标记语言"),
    ("什么是HTML", "HTML是超文本标记语言"),
    ("什么是CSS", "CSS是层叠样式表"),
    ("什么是JavaScript", "JavaScript是网页编程语言"),
    ("什么是Python", "Python是高级通用编程语言"),
    ("什么是Java", "Java是跨平台面向对象编程语言"),
    ("什么是C++", "C++是系统级编程语言"),
    ("什么是Rust", "Rust是注重安全的内存管理系统编程语言"),
    ("什么是Git", "Git是分布式版本控制系统"),
    ("什么是Docker", "Docker是容器化应用平台"),
    ("什么是云计算", "云计算是通过网络提供按需计算资源"),
    ("什么是大数据", "大数据是传统工具难以处理的庞大数据集"),
    ("什么是区块链", "区块链是去中心化的分布式账本技术"),
    ("什么是物联网", "物联网是互联设备的网络系统"),
    ("什么是5G", "5G是第五代移动通信技术"),
]

EXTRA_KNOWLEDGE_EN = [
    ("what is an algorithm", "An algorithm is a sequence of steps to solve a problem"),
    ("what is a database", "A database is a structured system for storing data"),
    ("what is an operating system", "An OS manages computer hardware and software"),
    ("what is a programming language", "A programming language formally communicates with computers"),
    ("what is a variable", "A variable is a named memory location that stores data"),
    ("what is a function", "A function is a reusable block of code"),
    ("what is a class", "A class is a blueprint for creating objects"),
    ("what is an object", "An object is an instance of a class"),
    ("what is an array", "An array stores elements of the same type"),
    ("what is a linked list", "A linked list is a linear data structure of nodes"),
    ("what is a stack", "A stack follows last-in-first-out order"),
    ("what is a queue", "A queue follows first-in-first-out order"),
    ("what is a tree data structure", "A tree is a hierarchical data structure"),
    ("what is a graph", "A graph consists of nodes and edges"),
    ("what is a hash table", "A hash table maps keys to values for fast lookup"),
    ("what is recursion", "Recursion is when a function calls itself"),
    ("what is iteration", "Iteration repeats execution of a block of code"),
    ("what is sorting", "Sorting arranges data in a specific order"),
    ("what is searching", "Searching finds a specific element in data"),
    ("what is time complexity", "Time complexity measures algorithm runtime"),
    ("what is space complexity", "Space complexity measures algorithm memory use"),
    ("what is encryption", "Encryption converts data to an unreadable form"),
    ("what is decryption", "Decryption restores encrypted data to its original form"),
    ("what is a network protocol", "A protocol is a set of rules for communication"),
    ("what is an IP address", "An IP address uniquely identifies a network device"),
    ("what is a domain name", "A domain name is a human-readable website address"),
    ("what is HTTP", "HTTP is the HyperText Transfer Protocol"),
    ("what is HTTPS", "HTTPS is secure HTTP with encryption"),
    ("what is an API", "An API is an Application Programming Interface"),
    ("what is JSON", "JSON is a lightweight data interchange format"),
    ("what is a microservice", "A microservice is an independent deployable service"),
    ("what is multithreading", "Multithreading runs multiple threads concurrently"),
    ("what is a deadlock", "A deadlock occurs when threads wait for each other forever"),
    ("what is caching", "Caching stores frequently accessed data for fast retrieval"),
    ("what is a CDN", "A CDN is a Content Delivery Network for fast content distribution"),
    ("what is a virtual machine", "A VM emulates a computer system"),
    ("what is a container", "A container packages code with its dependencies"),
    ("what is Kubernetes", "Kubernetes orchestrates container deployments"),
    ("what is CI/CD", "CI/CD automates building, testing, and deploying code"),
    ("what is Agile", "Agile is an iterative approach to software development"),
    ("what is Scrum", "Scrum is a framework for Agile development"),
    ("what is DevOps", "DevOps combines development and operations practices"),
    ("what is machine learning", "ML is a subset of AI that learns from data patterns"),
    ("what is deep learning", "Deep learning uses multi-layer neural networks"),
    ("what is natural language processing", "NLP enables computers to understand human language"),
    ("what is computer vision", "Computer vision enables computers to interpret images"),
    ("what is reinforcement learning", "RL learns through trial and error with rewards"),
    ("what is a transformer model", "Transformers use attention mechanisms for sequence tasks"),
]


# ---------------------------------------------------------------------------
# 3. Write logic_train.json
# ---------------------------------------------------------------------------

def write_logic_train(samples: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    logger.info("Wrote %d logic samples to %s (%.1f KB)",
                len(samples), path, os.path.getsize(path) / 1024)


# ---------------------------------------------------------------------------
# 4. Write expanded knowledge data as separate file for the pipeline to load
# ---------------------------------------------------------------------------

def write_knowledge_extra(path: str):
    pairs = []
    for inp, out in EXTRA_KNOWLEDGE_CN:
        pairs.append({"input": inp, "output": out, "domain": "knowledge"})
    for inp, out in EXTRA_KNOWLEDGE_EN:
        pairs.append({"input": inp, "output": out, "domain": "knowledge"})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)
    logger.info("Wrote %d knowledge pairs to %s (%.1f KB)",
                len(pairs), path, os.path.getsize(path) / 1024)


# ---------------------------------------------------------------------------
# 5. Write expanded math data (more variety)
# ---------------------------------------------------------------------------

MATH_TEMPLATES = [
    "what is {a} {op} {b}",
    "calculate {a} {op} {b}",
    "{a} {op} {b}",
    "{a} {op} {b} equals",
    "{a} {op} {b} =",
]

MATH_OPS = [
    ("+", lambda a, b: a + b),
    ("-", lambda a, b: a - b),
    ("*", lambda a, b: a * b),
    ("/", lambda a, b: a / b),
]


def gen_math_samples(count: int = 20000) -> list:
    samples = []
    for _ in range(count):
        op_sym, op_fn = random.choice(MATH_OPS)
        if op_sym == "/":
            b = random.randint(1, 100)
            a = random.randint(1, 100) * b
        else:
            a = random.randint(-100, 1000)
            b = random.randint(-100, 1000)
        answer = op_fn(a, b)
        # Handle floats
        if isinstance(answer, float) and answer != int(answer):
            answer = round(answer, 2)
        else:
            answer = int(answer)
        template = random.choice(MATH_TEMPLATES)
        inp = template.format(a=a, b=b, op=op_sym)
        samples.append({"problem": inp, "answer": str(answer)})
    logger.info("Generated %d math samples", len(samples))
    return samples


def write_math_extra(path: str, samples: list):
    existing = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            existing = json.load(f)
    combined = existing + samples
    logger.info("Math dataset: %d existing + %d new = %d total",
                len(existing), len(samples), len(combined))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# 6. Reasoning training data (transitive / syllogism / calendar / quantity / mass)
#    Mirrors the deterministic patterns in ai.symbolic_reasoner but as explicit
#    supervised examples so the ED3N/GARDEN networks can learn analogous patterns.
# ---------------------------------------------------------------------------

NAMES = ["Alice", "Bob", "Carol", "Dan", "Eve", "Frank", "Grace", "Heidi",
         "Ivan", "Judy", "Mallory", "Niaj", "Olivia", "Peggy", "Rupert", "Sybil",
         "Trent", "Victor", "Walter", "Yvonne"]

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEEKDAYS_ZH = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

CATS = [("bird", "birds", "fly"), ("mammal", "mammals", "are warm-blooded"),
        ("fish", "fish", "live in water"), ("insect", "insects", "have six legs"),
        ("reptile", "reptiles", "are cold-blooded"), ("dog", "dogs", "are loyal"),
        ("cat", "cats", "are independent"), ("tree", "trees", "produce oxygen")]
MEMBERS = ["a robin", "a sparrow", "a parrot", "a salmon", "a tuna", "an ant",
           "a beetle", "a lizard", "a snake", "a husky", "a poodle", "an oak",
           "a pine", "a Fido", "a Whiskers"]


def gen_transitive_samples(count: int = 3000) -> list:
    samples = []
    for _ in range(count):
        n = random.randint(3, 5)
        # random ordering of names
        people = random.sample(NAMES, n)
        # assign a hidden height rank
        ranks = list(range(n))
        random.shuffle(ranks)
        height = dict(zip(people, ranks))
        # build statements: a > b consistently with ranks
        stmts = []
        for i in range(n):
            for j in range(i + 1, n):
                a, b = people[i], people[j]
                if height[a] > height[b]:
                    stmts.append(f"{a} is taller than {b}.")
                else:
                    stmts.append(f"{b} is taller than {a}.")
        random.shuffle(stmts)
        tallest = max(height, key=lambda k: height[k])
        q_en = " ".join(stmts) + " Who is the tallest?"
        q_zh = " ".join(stmts) + " 谁最高？"
        question = random.choice([q_en, q_zh])
        samples.append({"input": question,
                        "output": f"{tallest} is the tallest." if "谁" not in question else f"{tallest} 最高。",
                        "domain": "reasoning"})
    logger.info("Generated %d transitive reasoning samples", len(samples))
    return samples


def gen_syllogism_samples(count: int = 3000) -> list:
    samples = []
    for _ in range(count):
        cat_sing, cat_plur, prop = random.choice(CATS)
        member = random.choice(MEMBERS)
        # positive: all X have prop; member is an X -> yes
        q_en = (f"All {cat_plur} {prop}. {member.capitalize()} is a {cat_sing}. "
                f"Is {member} {prop}?")
        a_en = "yes"
        q_zh = (f"所有{cat_plur}都{prop}。{member}是一只{cat_sing}。"
                f"{member}是否{prop}？")
        a_zh = "是"
        if random.random() < 0.5:
            samples.append({"input": q_en, "output": a_en, "domain": "reasoning"})
        else:
            samples.append({"input": q_zh, "output": a_zh, "domain": "reasoning"})
    logger.info("Generated %d syllogism reasoning samples", len(samples))
    return samples


def gen_calendar_samples(count: int = 2000) -> list:
    samples = []
    for _ in range(count):
        idx = random.randint(0, 6)
        today = WEEKDAYS[idx]
        q_en = f"If today is {today}, what day is tomorrow?"
        a_en = WEEKDAYS[(idx + 1) % 7]
        q_zh = f"如果今天是{WEEKDAYS_ZH[idx]}，明天是星期几？"
        a_zh = WEEKDAYS_ZH[(idx + 1) % 7]
        if random.random() < 0.5:
            samples.append({"input": q_en, "output": a_en, "domain": "reasoning"})
        else:
            samples.append({"input": q_zh, "output": a_zh, "domain": "reasoning"})
    logger.info("Generated %d calendar reasoning samples", len(samples))
    return samples


def gen_quantity_samples(count: int = 2000) -> list:
    samples = []
    for _ in range(count):
        have = random.randint(1, 20)
        give = random.randint(1, have)
        left = have - give
        q_en = (f"{NAMES[0]} has {have} apples. {NAMES[0]} gives {give} away. "
                f"How many left?")
        a_en = str(left)
        q_zh = (f"{NAMES[0]}有{have}个苹果，给了别人{give}个，还剩几个？")
        a_zh = str(left)
        if random.random() < 0.5:
            samples.append({"input": q_en, "output": a_en, "domain": "reasoning"})
        else:
            samples.append({"input": q_zh, "output": a_zh, "domain": "reasoning"})
    logger.info("Generated %d quantity reasoning samples", len(samples))
    return samples


def gen_mass_trick_samples(count: int = 1000) -> list:
    samples = []
    things = [("feathers", "steel"), ("cotton", "iron"), ("wood", "stone"),
              ("paper", "lead"), ("water", "mercury")]
    for _ in range(count):
        a, b = random.choice(things)
        q_en = f"Which is heavier: 1kg of {a} or 1kg of {b}?"
        a_en = "same"
        q_zh = f"1公斤{a}和1公斤{b}哪个更重？"
        a_zh = "一样重"
        if random.random() < 0.5:
            samples.append({"input": q_en, "output": a_en, "domain": "reasoning"})
        else:
            samples.append({"input": q_zh, "output": a_zh, "domain": "reasoning"})
    logger.info("Generated %d mass-trick reasoning samples", len(samples))
    return samples


def generate_reasoning_data() -> list:
    """Generate structured reasoning training samples across 5 pattern families."""
    samples = []
    samples += gen_transitive_samples(3000)
    samples += gen_syllogism_samples(3000)
    samples += gen_calendar_samples(2000)
    samples += gen_quantity_samples(2000)
    samples += gen_mass_trick_samples(1000)
    logger.info("Total reasoning samples: %d", len(samples))
    return samples


def write_reasoning_train(samples: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    logger.info("Wrote %d reasoning samples to %s (%.1f KB)",
                len(samples), path, os.path.getsize(path) / 1024)


# ---------------------------------------------------------------------------
# 7. Tool-use + domain-routing samples
#    Teaches the router/network to emit structured tool intents and to route
#    queries to the correct subsystem (math / knowledge / reasoning / search).
# ---------------------------------------------------------------------------

TOOLS = [
    ("calculator", "computes arithmetic expressions", "calc(2 + 3)"),
    ("search", "looks up information on the web", "search(weather today)"),
    ("reminder", "sets a timed reminder", "reminder(15m take break)"),
    ("calendar", "manages calendar events", "calendar(add meeting 3pm)"),
    ("translate", "translates text between languages", "translate(hello, zh)"),
    ("weather", "reports current weather", "weather(beijing)"),
    ("timer", "starts a countdown timer", "timer(60s)"),
    ("note", "saves a note", "note(buy milk)"),
]

DOMAIN_ROUTES = [
    ("calculate the integral of x squared", "math"),
    ("what is 15 times 23", "math"),
    ("who was the first president", "knowledge"),
    ("explain photosynthesis", "knowledge"),
    ("if A is taller than B and B taller than C who is tallest", "reasoning"),
    ("all cats are animals is a lynx a cat is it an animal", "reasoning"),
    ("what is the weather in tokyo", "search"),
    ("remind me to call mom", "tool"),
]


def generate_tooluse_data() -> list:
    """Generate tool-use intent + domain-routing training samples."""
    samples = []
    # Tool-use: "<request>" -> "tool: <name> -> <intent>"
    for _ in range(4000):
        name, desc, intent = random.choice(TOOLS)
        req_templates_en = [
            f"please use the {name} to {desc}",
            f"can you {intent}",
            f"I need you to {desc}, use {name}",
            f"run {name} for me",
        ]
        req_templates_zh = [
            f"请用{name}帮我{desc}",
            f"帮我调用{name}",
            f"使用{name}：{intent}",
        ]
        req = random.choice(req_templates_en + req_templates_zh)
        out = f"tool:{name} -> {intent}"
        samples.append({"input": req, "output": out, "domain": "tooluse"})
    # Domain routing: "<query>" -> "route:<domain>"
    for query, domain in DOMAIN_ROUTES:
        samples.append({"input": query, "output": f"route:{domain}", "domain": "routing"})
    for _ in range(2000):
        query, domain = random.choice(DOMAIN_ROUTES)
        # paraphrase slightly to add variety
        q2 = query.replace("the", "").replace("  ", " ")
        samples.append({"input": q2, "output": f"route:{domain}", "domain": "routing"})
    logger.info("Generated %d tool-use/domain-routing samples", len(samples))
    return samples


def write_tooluse_train(samples: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    logger.info("Wrote %d tool-use samples to %s (%.1f KB)",
                len(samples), path, os.path.getsize(path) / 1024)


# ---------------------------------------------------------------------------
# 6. Relational ASSOCIATION data (trains the SNN, NOT the KB)
# ---------------------------------------------------------------------------
# Architectural rule: the SNN must learn ASSOCIATIONS (relations between
# concepts like "A is taller than B"), while facts/reasoning chains go to the
# KB. These pairwise relational samples are the association signal the SNN was
# missing — they build a directional relation graph (A->B, B->C => transitive
# A->C emerges via spike propagation) without baking knowledge facts into the
# neural weights.

ASSOC_DIMS = {
    "taller": ("{a} is taller than {b}.", "{b} is shorter than {a}."),
    "shorter": ("{a} is shorter than {b}.", "{b} is taller than {a}."),
    "heavier": ("{a} is heavier than {b}.", "{b} is lighter than {a}."),
    "lighter": ("{a} is lighter than {b}.", "{b} is heavier than {a}."),
    "older": ("{a} is older than {b}.", "{b} is younger than {a}."),
    "younger": ("{a} is younger than {b}.", "{b} is older than {a}."),
    "bigger": ("{a} is bigger than {b}.", "{b} is smaller than {a}."),
    "smaller": ("{a} is smaller than {b}.", "{b} is bigger than {a}."),
    "faster": ("{a} is faster than {b}.", "{b} is slower than {a}."),
    "slower": ("{a} is slower than {b}.", "{b} is faster than {a}."),
    "smarter": ("{a} is smarter than {b}.", "{b} is duller than {a}."),
    "richer": ("{a} is richer than {b}.", "{b} is poorer than {a}."),
    "hotter": ("{a} is hotter than {b}.", "{b} is colder than {a}."),
    "colder": ("{a} is colder than {b}.", "{b} is hotter than {a}."),
}

ASSOC_ENTITIES = [
    "Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Heidi",
    "Ivan", "Judy", "Karl", "Laura", "Mike", "Nina", "Oscar", "Paula",
    "Tom", "Jerry", "Spike", "Tyke", "Butch", "Tweety", "Sylvester",
    "elephant", "mouse", "whale", "ant", "giraffe", "rabbit", "turtle",
    "mountain", "hill", "building", "tree", "car", "bicycle", "train",
    "cheetah", "snail", "eagle", "sloth", "professor", "student", "billionaire",
]


def generate_association_data(count: int = 12000) -> list:
    """Generate pairwise relational association samples for SNN training.

    Each sample is a single directional relation between two entities, so the
    SNN builds a clean A->B association edge (and its reverse B->A). Grouping
    many such pairs over a shared ranking (A>B, B>C, ...) yields a transitive
    chain in the neural graph without storing the fact in the KB.
    """
    samples = []
    dims = list(ASSOC_DIMS.items())
    for _ in range(count):
        dim, (tmpl_a, tmpl_b) = random.choice(dims)
        a, b = random.sample(ASSOC_ENTITIES, 2)
        samples.append({
            "input": tmpl_a.format(a=a, b=b),
            "output": tmpl_b.format(a=a, b=b),
            "domain": "association",
            "relation": dim,
        })
    logger.info("Total association samples: %d", len(samples))
    return samples


def write_association_train(samples: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    logger.info("Wrote %d association samples to %s (%.1f KB)",
                len(samples), path, os.path.getsize(path) / 1024)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. Logic training data (10K)
    logic_samples = gen_logic_samples(10000)
    logic_path = os.path.join(DATA_DIR, "logic_train.json")
    write_logic_train(logic_samples, logic_path)

    # 2. Knowledge extra (92 pairs)
    knowledge_path = os.path.join(DATA_DIR, "knowledge_extra.json")
    write_knowledge_extra(knowledge_path)

    # 3. Math extra (20K more)
    math_samples = gen_math_samples(20000)
    math_path = os.path.join(DATA_DIR, "arithmetic_train_dataset.json")
    write_math_extra(math_path, math_samples)

    # 4. Reasoning training data (transitive / syllogism / calendar / qty / mass)
    reasoning_samples = generate_reasoning_data()
    reasoning_path = os.path.join(DATA_DIR, "reasoning_train.json")
    write_reasoning_train(reasoning_samples, reasoning_path)

    # 5. Tool-use + domain-routing data
    tooluse_samples = generate_tooluse_data()
    tooluse_path = os.path.join(DATA_DIR, "tooluse_train.json")
    write_tooluse_train(tooluse_samples, tooluse_path)

    # 6. Relational ASSOCIATION data (SNN, not KB)
    association_samples = generate_association_data(12000)
    association_path = os.path.join(DATA_DIR, "association_train.json")
    write_association_train(association_samples, association_path)

    logger.info("=" * 50)
    logger.info("Data generation complete!")
    logger.info("  logic_train.json:   10,000 boolean logic samples")
    logger.info("  knowledge_extra.json: 92 knowledge QA pairs")
    logger.info("  arithmetic_train:    +20,000 math samples")
    logger.info("  reasoning_train:     %d reasoning samples" % len(reasoning_samples))
    logger.info("  tooluse_train:       %d tool-use/domain-routing samples" % len(tooluse_samples))
    logger.info("  association_train:   %d relational association samples" % len(association_samples))


if __name__ == "__main__":
    main()
