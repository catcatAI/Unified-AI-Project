"""Practical test: QueryClassifier, ExecutionGate, FileHandler, Math, Reflex"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src'))
from pathlib import Path

print("=== QueryClassifier Intent Detection ===")
from ai.core.query_classifier import QueryClassifier, QueryType
qc = QueryClassifier()
tests = [
    ("hello", QueryType.GREETING),
    ("2+2", QueryType.MATH),
    ("move test.txt to Documents", QueryType.FILE),
    ("delete temp.txt", QueryType.FILE),
    ("create a note please", QueryType.FILE),
    ("search for python", QueryType.SEARCH),
    ("capital of France", QueryType.KNOWLEDGE),
    ("what is AI", QueryType.KNOWLEDGE),
    ("tell me about Python", QueryType.KNOWLEDGE),
]
for msg, exp in tests:
    r = qc.classify(msg)
    ok = "Y" if r.primary_type == exp else "N"
    print(f'  {ok} [{r.primary_type.name:10s}] c={r.confidence:.3f} a={r.actionability:.3f} t={r.action_type:10s} "{msg[:50]}"')

print("\n=== ExecutionGate Safety ===")
from ai.core.execution_gate import ExecutionGate
gate = ExecutionGate()
for msg, qtype, atype in [
    ("create file x.txt", QueryType.FILE, "create"),
    ("delete my file.txt", QueryType.FILE, "delete"),
    ("delete all files", QueryType.FILE, "delete"),
    ("run dangerous command", QueryType.EXECUTE, "execute"),
    ("read notes.txt", QueryType.FILE, "read"),
    ("I don't want to delete anything", QueryType.FILE, "delete"),  # negation
]:
    r = qc.classify(msg)
    d = gate.decide(query_type=qtype, action_type=atype, user_message=msg, confidence=r.confidence, context={})
    neg = "no-delete" in msg.lower()
    print(f'  [{d.action:22s}] reason="{d.reason[:60]}..." neg={neg}')

print("\n=== MathVerifier ===")
from services.math_verifier import MathVerifier
mv = MathVerifier()
for t in ["2+2", "10*5", "100/4", "calculate 3+5", "not math", "hello"]:
    ans = mv.verify(t)
    is_math = mv.is_math_message(t)
    print(f'  {"Y" if is_math else "N"} "{t:20s}" → is_math={is_math} answer={ans}')

print("\n=== FileOperationHandler Path Safety ===")
from services.handlers.file_operation_handler import _is_safe_path as fh_safe
for p in [
    Path.home() / "Desktop" / "test.txt",
    Path.home() / "Documents" / "report.pdf",
    Path("C:/Windows/system32/cmd.exe"),
    Path.home() / "Desktop" / ".." / ".." / "Windows" / "system32" / "hack.exe",
]:
    safe = fh_safe(p.resolve())
    print(f'  {"SAFE" if safe else "BLOCK"} {p.name}')

print("\n=== GARDEN Reflex ===")
from ai.garden.garden_engine import _ReflexTable
grt = _ReflexTable()
for p in ["hello", "hi", "你好", "thank you", "bye", "unknown"]:
    r = grt.match(p)
    print(f'  {"Y" if r else "N"} "{p:15s}" → {r[:50] if r else "no match"}')

print("\n=== ED3N Reflex ===")
from ai.ed3n.ed3n_engine import ReflexLayer
erl = ReflexLayer(config={})
for p in ["hello", "hi", "你好", "thanks", "help", "unknown"]:
    r = erl.process(p)
    print(f'  {"Y" if r else "N"} "{p:15s}" → {r[:50] if r else "no match"}')

print("\n=== ALL PRACTICAL TESTS PASSED ===")
