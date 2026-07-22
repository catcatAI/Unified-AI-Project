import json

p = r"D:\Projects\Unified-AI-Project\data\memory\ham_memory.json"
d = json.load(open(p, encoding="utf-8"))
pre = len(d.get("templates", []))

bad=["didn", "don't know", "do not know", "sorry", "cannot help",
       "can't help", "no answer", "unknown"]


def is_bad(t):
    c = (t.get("content") or "").strip().lower()
    return any(b in c for b in bad)


d["templates"] = [t for t in d.get("templates", []) if not is_bad(t)]
post = len(d["templates"])
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("removed", pre - post, "bad templates; remaining", post)
