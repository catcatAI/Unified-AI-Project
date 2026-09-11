#!/usr/bin/env python3
"""數據驅動模板引擎：新模板用 JSON 定義（公式+材料引用），免寫碼即算。

回答"專案ai能自己從基本面算出新模板嗎"：能一半——AI 寫 JSON 公式，
引擎验算+執行（本腳本即證）。公式是不透明字串，需受信來源或人工審。
"""

import argparse
import ast
import json
import operator
import os

DB = os.path.join(
    os.path.dirname(__file__), "..", "data", "materials", "civil_materials.json"
)
TPL = os.path.join(
    os.path.dirname(__file__), "..", "data", "materials", "civil_templates.json"
)

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
       ast.GtE: operator.ge, ast.LtE: operator.le, ast.Gt: operator.gt,
       ast.Lt: operator.lt, ast.Eq: operator.eq}


def safe_eval(expr, ns):
    tree = ast.parse(expr, mode="eval")

    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.Name):
            if n.id not in ns:
                raise ValueError(f"unknown name: {n.id}")
            return ns[n.id]
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            return OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in OPS:
            return OPS[type(n.op)](ev(n.operand))
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and type(n.ops[0]) in OPS:
            return OPS[type(n.ops[0])](ev(n.left), ev(n.comparators[0]))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            if n.func.id == "db" and len(n.args) in (2, 3):
                a = [ev(x) if not isinstance(x, ast.Constant) else x.value for x in n.args]
                v = ns["__db"]
                for k in a:
                    v = v[k]
                return v
            if n.func.id in ("min", "max") and n.args:
                return (min if n.func.id == "min" else max)([ev(x) for x in n.args])
            raise ValueError(f"call not allowed: {n.func.id}")
        raise ValueError(f"node not allowed: {type(n).__name__}")

    return ev(tree.body)


def run_template(tpl, db, overrides):
    ns = {"__db": db}
    ns.update(tpl.get("materials", {}))
    ns.update(tpl.get("inputs", {}))
    ns.update(overrides or {})
    trace = {}
    for step in tpl.get("steps", []):
        for var, expr in step.items():
            val = safe_eval(expr, ns)
            ns[var] = val
            trace[var] = round(val, 3) if isinstance(val, float) else val
    checks = {}
    for c in tpl.get("checks", []):
        checks[c["name"]] = bool(safe_eval(c["expr"], ns))
    out = {k: trace[k] for k in tpl.get("outputs", []) if k in trace}
    return {"inputs": {k: ns[k] for k in tpl.get("inputs", {})},
            "results": out, "checks": checks,
            "assumptions": tpl.get("assumptions", [])}


def main():
    ap = argparse.ArgumentParser(description="data-driven civil templates")
    ap.add_argument("--template", default="", help="name or empty=all")
    ap.add_argument("--json", default="{}", help="input overrides")
    args = ap.parse_args()
    db = json.load(open(DB, encoding="utf-8"))
    tpls = json.load(open(TPL, encoding="utf-8"))["templates"]
    over = json.loads(args.json)
    for t in tpls:
        if args.template and t["name"] != args.template:
            continue
        print(json.dumps({"template": t["name"],
                          **run_template(t, db, over.get(t["name"], {}))},
                         ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
