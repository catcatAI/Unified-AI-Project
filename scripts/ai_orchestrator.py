#!/usr/bin/env python3
"""
AI Orchestrator for project automation:
- Dataset check and (optional) repair
- Model and training system inspection
- Conditional training
- Docs auto-update with placeholders and validation
- One-click run-all pipeline with decision flow

Usage examples:
  python scripts/ai_orchestrator.py check-datasets
  python scripts/ai_orchestrator.py update-docs --dry-run
  python scripts/ai_orchestrator.py run-all --dry-run
  python scripts/ai_orchestrator.py run-all --apply

Placeholders supported in Markdown (anywhere in *.md):
  <!-- AUTO:BEGIN key=dataset_summary --> ... <!-- AUTO:END key=dataset_summary -->
  <!-- AUTO:BEGIN key=model_registry --> ... <!-- AUTO:END key=model_registry -->
  <!-- AUTO:BEGIN key=training_status --> ... <!-- AUTO:END key=training_status -->
  <!-- AUTO:BEGIN key=project_status --> ... <!-- AUTO:END key=project_status -->
  <!-- AUTO:BEGIN key=link_check_summary --> ... <!-- AUTO:END key=link_check_summary -->

The script is dependency-free (stdlib only) and safe by default (dry-run).
"""
import argparse
import os
import re
import sys
import subprocess
import json
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
# NEW: for plugin loading and discovery
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIRS = [ROOT / 'docs', ROOT]
IGNORE_PARTS = {"node_modules", ".git", "backup", "archives", "__pycache__", "venv", ".venv", ".pnpm", "dist", "build"}

SECTION_KEYS = [
    'dataset_summary',
    'model_registry',
    'training_status',
    'project_status',
    'link_check_summary',
]

# ------------------------------- utils ---------------------------------

def log(msg: str):
    now = datetime.now().strftime('%H:%M:%S')
    print(f"[{now}] {msg}")

# NEW: plugin loader for validators
def load_validators(kind: str) -> List:
    """Dynamically load validator callables from scripts/validators.
    Each module may expose a function named `validate` or `validate_{kind}`.
    The callable signature: func(context: Dict) -> Dict with fields {ok: bool, name: str, issues: List[str]}.
    """
    validators = []
    base = ROOT / 'scripts' / 'validators'
    if not base.exists() or not base.is_dir():
        return validators
    for p in base.glob('*.py'):
        try:
            spec = importlib.util.spec_from_file_location(p.stem, p)
            if not spec or not spec.loader:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            func = getattr(mod, f'validate_{kind}', None) or getattr(mod, 'validate', None)
            if callable(func):
                validators.append((p.stem, func))
        except Exception as e:
            log(f"Validator load failed: {p.name}: {e}")
    return validators


def should_ignore(path: Path) -> bool:
    low = str(path).lower()
    for part in IGNORE_PARTS:
        if f"{os.sep}{part}{os.sep}" in low or f"/{part}/" in low or f"\\{part}\\" in low:
            return True
    return False

# NEW: scan data generators
def scan_data_generators() -> List[Dict]:
    entries: List[Dict] = []
    candidates = [ROOT / 'scripts' / 'data_gen', ROOT / 'data' / 'generators', ROOT / 'scripts']
    for base in candidates:
        if not base.exists():
            continue
        for p in base.rglob('generate_data*.py') if base.name == 'scripts' else base.rglob('*.py'):
            if p.is_file() and not should_ignore(p):
                # Heuristic: include likely generator scripts
                if 'generate' in p.stem or 'data' in p.stem or p.parent.name.lower() in {'data_gen', 'generators'}:
                    entries.append({
                        'path': str(p.relative_to(ROOT)),
                        'size': p.stat().st_size,
                        'modified': datetime.fromtimestamp(p.stat().st_mtime).isoformat()
                    })
    # de-dup by path
    seen = set()
    uniq = []
    for it in entries:
        if it['path'] in seen:
            continue
        seen.add(it['path'])
        uniq.append(it)
    return sorted(uniq, key=lambda x: x['path'])


def safe_run(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str]:
    try:
        res = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True, check=False)
        return res.returncode, (res.stdout or '') + (res.stderr or '')
    except Exception as e:
        return 1, f"Exception running {' '.join(cmd)}: {e}"

# ------------------------------ scanners -------------------------------

def scan_datasets() -> Dict:
    candidates = [ROOT / 'data', ROOT / 'datasets']
    items = []
    for base in candidates:
        if base.exists():
            for p in base.rglob('*'):
                if p.is_file() and not should_ignore(p):
                    try:
                        sz = p.stat().st_size
                    except Exception:
                        sz = -1
                    items.append({
                        'path': str(p.relative_to(ROOT)),
                        'size': sz,
                        'modified': datetime.fromtimestamp(p.stat().st_mtime).isoformat() if sz >= 0 else None
                    })
    ok = len(items) > 0
    return {'ok': ok, 'count': len(items), 'samples': items[:50]}


def scan_models() -> Dict:
    candidates = [ROOT / 'models', ROOT / 'checkpoints', ROOT / 'outputs']
    exts = {'.pt', '.bin', '.onnx', '.ckpt', '.safetensors'}
    items = []
    for base in candidates:
        if base.exists():
            for p in base.rglob('*'):
                if p.is_file() and p.suffix.lower() in exts and not should_ignore(p):
                    try:
                        ts = p.stat().st_mtime
                        sz = p.stat().st_size
                    except Exception:
                        ts, sz = 0, -1
                    items.append({
                        'path': str(p.relative_to(ROOT)),
                        'size': sz,
                        'modified': datetime.fromtimestamp(ts).isoformat() if ts else None
                    })
    latest_ts = max((datetime.fromisoformat(i['modified']) for i in items if i['modified']), default=None)
    return {'count': len(items), 'latest_modified': latest_ts.isoformat() if latest_ts else None, 'items': items[:50]}


def scan_training() -> Dict:
    candidates = [ROOT / 'runs', ROOT / 'logs', ROOT / 'training_logs']
    logs = []
    for base in candidates:
        if base.exists():
            for p in base.rglob('*.log'):
                if p.is_file() and not should_ignore(p):
                    try:
                        ts = p.stat().st_mtime
                        size = p.stat().st_size
                        logs.append({
                            'path': str(p.relative_to(ROOT)),
                            'size': size,
                            'modified': datetime.fromtimestamp(ts).isoformat(),
                        })
                    except Exception:
                        pass
    return {'count': len(logs), 'items': logs[:50]}

# ----------------------------- doc update ------------------------------
START_PATTERNS = [
    re.compile(r"<!--\s*AUTO:(?:BEGIN|START)\s+key\s*=\s*([a-zA-Z0-9_\-]+)\s*-->", re.IGNORECASE),
    re.compile(r"<!--\s*auto:([a-zA-Z0-9_\-]+):start\s*-->", re.IGNORECASE),
]
END_PATTERNS = [
    re.compile(r"<!--\s*AUTO:(?:END|STOP)\s+key\s*=\s*([a-zA-Z0-9_\-]+)\s*-->", re.IGNORECASE),
    re.compile(r"<!--\s*auto:([a-zA-Z0-9_\-]+):end\s*-->", re.IGNORECASE),
]

def render_section(key: str, ctx: Dict) -> str:
    if key == 'dataset_summary':
        d = ctx.get('datasets', {})
        lines = ["### Dataset Summary", f"- OK: {d.get('ok')} - Files: {d.get('count')}"]
        for it in d.get('samples', [])[:10]:
            lines.append(f"  - {it['path']} (size={it['size']})")
        return "\n".join(lines)
    if key == 'model_registry':
        m = ctx.get('models', {})
        lines = ["### Model Registry", f"- Count: {m.get('count')} - Latest: {m.get('latest_modified')}"]
        for it in m.get('items', [])[:10]:
            lines.append(f"  - {it['path']} (modified={it.get('modified')})")
        return "\n".join(lines)
    if key == 'training_status':
        t = ctx.get('training', {})
        lines = ["### Training Status", f"- Log files: {t.get('count')}"]
        for it in t.get('items', [])[:10]:
            lines.append(f"  - {it['path']} (modified={it.get('modified')})")
        return "\n".join(lines)
    if key == 'project_status':
        lines = ["### Project Status", "- Auto-generated by AI Orchestrator", f"- Time: {datetime.now().isoformat()} "]
        rpt = ROOT / 'doc_update_report.md'
        if rpt.exists():
            lines.append(f"- Changelog: {rpt}")
        return "\n".join(lines)
    if key == 'link_check_summary':
        logf = ROOT / 'docs_link_check.log'
        lines = ["### Link Check Summary"]
        if logf.exists():
            try:
                tail = ''.join(logf.read_text(encoding='utf-8', errors='ignore').splitlines(True)[-40:])
                lines.append("```\n" + tail + "\n```")
            except Exception as e:
                lines.append(f"(failed to read log: {e})")
        else:
            lines.append("(no log found)")
        return "\n".join(lines)
    return f"<!-- Unknown section key: {key} -->"


def update_markdown_content(content: str, ctx: Dict) -> Tuple[str, List[str]]:
    updates = []
    # Find all start markers and corresponding end markers and replace content
    pos = 0
    out = content
    while True:
        m_start = None
        for sp in START_PATTERNS:
            m = sp.search(out, pos)
            if m:
                m_start = m
                break
        if not m_start:
            break
        key = m_start.group(1).lower()
        # find matching end after start
        m_end = None
        for ep in END_PATTERNS:
            m2 = ep.search(out, m_start.end())
            if m2 and m2.group(1).lower() == key:
                m_end = m2
                break
        if not m_end:
            pos = m_start.end()
            continue
        new_block = render_section(key, ctx)
        # replace between end of start and start of end
        out = out[:m_start.end()] + "\n" + new_block + "\n" + out[m_end.start():]
        pos = m_start.end() + len(new_block) + 2
        updates.append(key)
    return out, list(dict.fromkeys(updates))


def collect_markdown_files(targets: Optional[List[str]]) -> List[Path]:
    files: List[Path] = []
    if targets:
        for t in targets:
            p = (ROOT / t).resolve()
            if p.exists() and p.suffix.lower() == '.md' and not should_ignore(p):
                files.append(p)
    else:
        for d in DOCS_DIRS:
            if d.exists():
                for p in d.rglob('*.md'):
                    if p.is_file() and not should_ignore(p):
                        files.append(p)
    # prioritize root README.md first
    files = sorted(set(files), key=lambda p: (0 if p.name.lower()=="readme.md" and p.parent==ROOT else 1, str(p)))
    return files

# --------------------------- decisions / actions ------------------------

def decide_training_needed(dsets: Dict, models: Dict) -> bool:
    # naive policy: if datasets ok and newer than latest model, or there is no model
    if models.get('count', 0) == 0:
        return dsets.get('ok', False)
    # compare timestamps
    try:
        latest_model_ts = datetime.fromisoformat(models.get('latest_modified')) if models.get('latest_modified') else None
    except Exception:
        latest_model_ts = None
    # compute latest dataset ts
    latest_data_ts = None
    for it in dsets.get('samples', []):
        try:
            ts = datetime.fromisoformat(it.get('modified'))
            latest_data_ts = max(latest_data_ts, ts) if latest_data_ts else ts
        except Exception:
            pass
    if latest_model_ts and latest_data_ts:
        return latest_data_ts > latest_model_ts
    return False

# ------------------------------- CLI cmds -------------------------------

def cmd_check_datasets(args) -> int:
    d = scan_datasets()
    # NEW: discover potential data generators
    gens = scan_data_generators()
    # NEW: run pluggable validators if present
    val_results = []
    overall_ok = d['ok']
    for name, func in load_validators('dataset'):
        try:
            res = func({'root': str(ROOT), 'datasets': d, 'generators': gens})
            # normalize result
            ok = bool(res.get('ok', True))
            issues = res.get('issues', []) or []
            val_results.append({'name': res.get('name') or name, 'ok': ok, 'issues': issues})
            if not ok:
                overall_ok = False
        except Exception as e:
            val_results.append({'name': name, 'ok': False, 'issues': [f'validator error: {e}']})
            overall_ok = False
    report = {
        'datasets': d,
        'generators': gens,
        'validators': val_results,
        'ok': bool(overall_ok),
        'generated_at': datetime.now().isoformat()
    }
    (ROOT / 'dataset_health.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    log(f"Datasets: ok={report['ok']} count={d['count']} validators={len(val_results)} (report: dataset_health.json)")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report['ok'] else 1


def cmd_check_models(args) -> int:
    m = scan_models()
    log(f"Models: count={m['count']} latest={m.get('latest_modified')}")
    print(json.dumps(m, indent=2, ensure_ascii=False))
    return 0


def cmd_check_training(args) -> int:
    t = scan_training()
    log(f"Training logs: {t['count']}")
    print(json.dumps(t, indent=2, ensure_ascii=False))
    return 0


def cmd_train(args) -> int:
    # Heuristic: look for scripts/train.py
    entry = ROOT / 'scripts' / 'train.py'
    if args.entry:
        entry = (ROOT / args.entry).resolve()
    if not entry.exists():
        log(f"Train entry not found: {entry}. Skip.")
        return 0
    cmd = [sys.executable, str(entry)]
    if args.extra:
        cmd.extend(args.extra)
    log(f"Running training: {' '.join(cmd)}")
    code, out = safe_run(cmd, cwd=ROOT)
    print(out)
    return code


def cmd_update_docs(args) -> int:
    d = scan_datasets()
    m = scan_models()
    t = scan_training()
    ctx = {'datasets': d, 'models': m, 'training': t}
    files = collect_markdown_files(args.targets)
    changes = []
    for f in files:
        try:
            content = f.read_text(encoding='utf-8', errors='ignore')
            new_content, updated = update_markdown_content(content, ctx)
            if updated:
                changes.append({'file': str(f.relative_to(ROOT)), 'sections': updated})
                if args.apply:
                    f.write_text(new_content, encoding='utf-8')
        except Exception as e:
            log(f"Failed updating {f}: {e}")
    report = {
        'changes': changes,
        'generated_at': datetime.now().isoformat(),
        'apply': bool(args.apply),
    }
    (ROOT / 'doc_auto_update_report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    log(f"Doc auto-update {'applied' if args.apply else 'dry-run'}; changes: {len(changes)} (report: doc_auto_update_report.json)")
    return 0


def cmd_validate_docs(args) -> int:
    script = ROOT / 'scripts' / 'validate_doc_links.py'
    if not script.exists():
        log("validate_doc_links.py not found")
        return 1
    env = os.environ.copy()
    env['DOC_LINK_CHECK_VERBOSE'] = '0'
    # 仅验证 docs 目錄，避免掃到第三方依賴；如需同時檢查根 README，可在後續擴展
    cmds = [
        [sys.executable, str(script), '--root', 'docs', '--ignore', 'venv,.venv,node_modules,dist,build,archives,backup,.git,__pycache__,.pnpm', '--report-json', 'docs_link_check_errors.json', '--report-text', 'docs_link_check_errors.txt']
    ]
    combined_out = []
    rc_final = 0
    for cmd in cmds:
        log(f"Running: {' '.join(cmd)}")
        try:
            res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, env=env)
            combined_out.append((res.returncode, (res.stdout or '') + (res.stderr or '')))
            if res.returncode != 0:
                rc_final = 1
        except Exception as e:
            combined_out.append((1, f"Exception: {e}"))
            rc_final = 1
    # 寫入合併日誌
    buf = []
    for i, (rc, out) in enumerate(combined_out, 1):
        buf.append(f"--- validate pass {i} exit={rc} ---\n{out}\n")
    (ROOT / 'docs_link_check.log').write_text(''.join(buf), encoding='utf-8')
    # 同步輸出到控制台
    print(''.join(buf))
    return rc_final


# Build a simple index of all Markdown files in docs by filename (case-insensitive)
DOCS_FILE_INDEX: Dict[str, List[Path]] = {}
# Normalized filename index to improve fuzzy matching (hyphen/underscore, prefixes)
DOCS_FILE_INDEX_NORM: Dict[str, List[Path]] = {}


def _normalize_name(name: str) -> str:
    s = name.lower()
    # keep extension if provided, normalize separators
    s = s.replace("\\", "/").split("/")[-1]
    # normalize hyphen/underscore equivalence and collapse non-alnum to '-'
    import re as _re
    base, dot, ext = s.partition(".")
    base = _re.sub(r"[^a-z0-9]+", "-", base.replace("_", "-").strip("-"))
    ext = _re.sub(r"[^a-z0-9]+", "", ext)
    return f"{base}.{ext}" if ext else base


def _generate_name_variants(name: str) -> List[str]:
    """Generate possible filename variants for robust matching in docs index."""
    nm = name.lower()
    variants = {nm}
    if "." not in nm:
        variants.add(nm + ".md")
    # hyphen/underscore swaps
    variants.add(nm.replace("_", "-"))
    variants.add(nm.replace("-", "_"))
    # common prefixes to drop (project_, projects_)
    for pref in ("project_", "projects_"):
        if nm.startswith(pref):
            stripped = nm[len(pref):]
            variants.add(stripped)
            if "." not in stripped:
                variants.add(stripped + ".md")
            variants.add(stripped.replace("_", "-"))
            variants.add(stripped.replace("-", "_"))
    # ensure .md variants exist
    more = set()
    for v in list(variants):
        if "." not in v:
            more.add(v + ".md")
    variants |= more
    return list(variants)


def _build_docs_file_index() -> Dict[str, List[Path]]:
    global DOCS_FILE_INDEX, DOCS_FILE_INDEX_NORM
    if DOCS_FILE_INDEX and DOCS_FILE_INDEX_NORM:
        return DOCS_FILE_INDEX
    base = ROOT / 'docs'
    idx: Dict[str, List[Path]] = {}
    idx_norm: Dict[str, List[Path]] = {}
    if base.exists():
        for p in base.rglob('*.md'):
            try:
                key = p.name.lower()
                idx.setdefault(key, []).append(p)
                nkey = _normalize_name(key)
                idx_norm.setdefault(nkey, []).append(p)
            except Exception:
                continue
    DOCS_FILE_INDEX = idx
    DOCS_FILE_INDEX_NORM = idx_norm
    return DOCS_FILE_INDEX


def _lookup_docs_candidates(filename: str) -> List[Path]:
    """Lookup candidate markdown files in docs by filename with tolerant matching."""
    _build_docs_file_index()
    name = filename.lower()
    cands: List[Path] = []
    # try direct and simple variants
    for key in _generate_name_variants(name):
        ps = DOCS_FILE_INDEX.get(key)
        if ps:
            cands.extend(ps)
    # try normalized key match
    nkey = _normalize_name(name)
    if nkey in DOCS_FILE_INDEX_NORM:
        cands.extend(DOCS_FILE_INDEX_NORM[nkey])
    # de-duplicate preserving order
    seen = set()
    uniq: List[Path] = []
    for p in cands:
        rp = p.as_posix().lower()
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq

# Fallback relocation for known non-doc targets referenced via file:// or wrong names
FILENAME_RELOCATION: Dict[str, List[Path]] = {
    'test_imports.py': [ROOT / 'verify_core_functionality.py', ROOT / 'tools' / 'final_integration_test.py', ROOT / 'apps' / 'backend' / 'scripts' / 'final_validation.py'],
    'final_test.py': [ROOT / 'tools' / 'final_integration_test.py', ROOT / 'verify_core_functionality.py'],
    # Added mappings discovered from repo structure
    'execution_monitor.py': [
        ROOT / 'apps' / 'backend' / 'src' / 'core' / 'managers' / 'execution_monitor.py',
        ROOT / 'apps' / 'backend' / 'src' / 'managers' / 'execution_monitor.py',
        # backups as lower priority fallbacks
        ROOT / 'apps' / 'backend' / 'backup' / 'auto_fix_20250911_154229' / 'src' / 'core' / 'managers' / 'execution_monitor.py',
        ROOT / 'apps' / 'backend' / 'backup' / 'auto_fix_20250911_154229' / 'src' / 'managers' / 'execution_monitor.py',
    ],
    # NEW: map old execution_manager.py references to current locations
    'execution_manager.py': [
        ROOT / 'apps' / 'backend' / 'src' / 'core' / 'managers' / 'execution_manager.py',
        ROOT / 'apps' / 'backend' / 'src' / 'managers' / 'execution_manager.py',
        # backups as lower priority fallbacks
        ROOT / 'apps' / 'backend' / 'backup' / 'auto_fix_20250911_154229' / 'src' / 'core' / 'managers' / 'execution_manager.py',
        ROOT / 'apps' / 'backend' / 'backup' / 'auto_fix_20250911_154229' / 'src' / 'managers' / 'execution_manager.py',
    ],
    'ham_memory_manager.py': [
        ROOT / 'apps' / 'backend' / 'src' / 'ai' / 'memory' / 'ham_memory_manager.py',
    ],
    'personality_manager.py': [
        ROOT / 'apps' / 'backend' / 'src' / 'ai' / 'personality' / 'personality_manager.py',
    ],
    'project_coordinator.py': [
        ROOT / 'apps' / 'backend' / 'src' / 'ai' / 'dialogue' / 'project_coordinator.py',
    ],
}

def rewrite_links_in_markdown(md_path: Path) -> Tuple[str, List[Tuple[str, str]]]:
    text = md_path.read_text(encoding='utf-8', errors='ignore')
    dirp = md_path.parent
    changes: List[Tuple[str, str]] = []
    # regex for markdown links: [text](url)
    pattern = re.compile(r"(\[[^\]]+\]\()\s*(<[^>]+>|[^)]+?)\s*(\))")

    def repl(m):
        before, raw_url, after = m.group(1), m.group(2), m.group(3)
        url = raw_url.strip()
        # strip optional angle brackets around URL
        if url.startswith('<') and url.endswith('>'):
            url = url[1:-1].strip()
        orig = url
        # skip if url has scheme or anchor-only
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", url) or url.startswith('#'):
            # try to normalize file:// urls pointing inside repo or by filename
            if url.lower().startswith('file://'):
                try:
                    parsed = urllib.parse.urlparse(url)
                    path = urllib.parse.unquote(parsed.path or '')
                    # Windows file URI may start with "/D:/..."; strip the first slash
                    if re.match(r"^/[a-zA-Z]:", path):
                        path = path[1:]
                    abs_res = Path(path)
                    # If exists and is inside the repository, rewrite to relative from current markdown location
                    if abs_res.exists():
                        try:
                            abs_real = abs_res.resolve()
                        except Exception:
                            abs_real = abs_res
                        try:
                            root_real = ROOT.resolve()
                        except Exception:
                            root_real = ROOT
                        if str(abs_real).lower().startswith(str(root_real).lower()):
                            rel = os.path.relpath(abs_real, dirp)
                            newu = rel.replace('\\', '/')
                            if newu != orig:
                                changes.append((orig, newu))
                                return f"{before}{newu}{after}"
                    # If file does not exist, try relocation mapping first
                    name = abs_res.name.lower()
                    mapped = FILENAME_RELOCATION.get(name)
                    if mapped:
                        for cand in mapped:
                            try:
                                if cand.exists():
                                    rel = os.path.relpath(cand.resolve(), dirp)
                                    newu = rel.replace('\\', '/')
                                    if newu != orig:
                                        changes.append((orig, newu))
                                        return f"{before}{newu}{after}"
                            except Exception:
                                continue
                    # Fallback: match by filename within docs even if file does not exist or is outside repo
                    if name:
                        cands = _lookup_docs_candidates(name)
                        chosen = None
                        if cands and len(cands) == 1:
                            chosen = cands[0]
                        elif cands:
                            # choose by common parent tokens
                            parent_tokens = [seg.lower() for seg in abs_res.parent.as_posix().split('/') if seg]
                            best = None
                            best_score = -1
                            for cp in cands:
                                cpath = cp.as_posix().lower()
                                score = sum(1 for tok in parent_tokens if tok in cpath)
                                if score > best_score:
                                    best_score = score
                                    best = cp
                            chosen = best
                        if chosen:
                            try:
                                rel = os.path.relpath(chosen.resolve(), dirp)
                            except Exception:
                                rel = os.path.relpath(chosen, dirp)
                            newu = rel.replace('\\', '/')
                            if newu != orig:
                                changes.append((orig, newu))
                                return f"{before}{newu}{after}"
                except Exception:
                    pass
            return m.group(0)

        # normalize backslashes to slashes for detection only and keep fragment to re-attach later
        url_norm = url.replace('\\', '/')
        frag = ''
        if '#' in url_norm:
            url_norm, frag = url_norm.split('#', 1)
            frag = '#' + frag
        # Only strip leading './' or '.\\' once; keep '../' and dot-prefixed folders like '.qoder'
        if url_norm.startswith('./'):
            url_norm = url_norm[2:]
        elif url_norm.startswith('.\\'):
            url_norm = url_norm[2:]
        # percent-decode for local path processing (validator treats raw path; we will rewrite to actual relative path)
        url_norm = urllib.parse.unquote(url_norm)
        url_path_only = url_norm
        new_url: Optional[str] = None

        prefix_variants = [
            'Unified-AI-Project/docs/',
            'Unified-AI-Project/Docs/',
            'Unified-AI-Project/DOCS/',
            '/docs/',
            'docs/'
        ]
        for pref in prefix_variants:
            if url_norm.lower().startswith(pref.lower()):
                rel_part = url_norm[len(pref):]
                target_abs = (ROOT / 'docs' / rel_part).resolve()
                if target_abs.exists():
                    rel = os.path.relpath(target_abs, dirp)
                    new_url = rel.replace('\\', '/')
                else:
                    rel = os.path.relpath((ROOT / 'docs' / rel_part), dirp)
                    new_url = rel.replace('\\', '/')
                break

        # Try repo-root relative existing file
        if not new_url:
            try:
                cand_abs = (ROOT / url_path_only).resolve()
                if cand_abs.exists():
                    rel = os.path.relpath(cand_abs, dirp)
                    new_url = rel.replace('\\', '/')
            except Exception:
                pass

        # Try relative to current markdown location first (for broken relatives)
        if not new_url:
            try:
                cand_rel = (dirp / url_path_only).resolve()
                if cand_rel.exists():
                    rel = os.path.relpath(cand_rel, dirp)
                    new_url = rel.replace('\\', '/')
            except Exception:
                pass

        # If missing extension, try appending .md in likely locations
        if not new_url:
            try:
                base_name = os.path.basename(url_path_only)
                if base_name and '.' not in base_name:
                    md_variants = [
                        (dirp / (url_path_only + '.md')).resolve(),
                        (ROOT / (url_path_only + '.md')).resolve(),
                        (ROOT / 'docs' / (url_path_only + '.md')).resolve(),
                    ]
                    for c in md_variants:
                        try:
                            if c.exists():
                                rel = os.path.relpath(c, dirp)
                                new_url = rel.replace('\\', '/')
                                break
                        except Exception:
                            continue
            except Exception:
                pass

        # Handle directory links -> README.md or index.md
        if not new_url:
            for base_abs in [dirp / url_path_only, ROOT / url_path_only, ROOT / 'docs' / url_path_only]:
                try:
                    base_abs = base_abs.resolve()
                except Exception:
                    base_abs = base_abs
                if base_abs.exists() and base_abs.is_dir():
                    cands = []
                    for fn in ['README.md', 'readme.md', 'Index.md', 'index.md']:
                        p = base_abs / fn
                        if p.exists():
                            cands.append(p)
                    chosen = None
                    if len(cands) == 1:
                        chosen = cands[0]
                    elif len(cands) > 1:
                        # prefer README.md then index.md (case-insensitive)
                        pref = ['readme.md', 'index.md']
                        for name in pref:
                            for p in cands:
                                if p.name.lower() == name:
                                    chosen = p
                                    break
                            if chosen:
                                break
                    if not chosen:
                        # fallback by filename search in docs
                        idx = _build_docs_file_index()
                        # try to map to a file whose parent path shares tokens with requested path
                        parent_tokens = [seg.lower() for seg in os.path.dirname(url_path_only).split('/') if seg]
                        best = None
                        best_score = -1
                        for cp in cands:
                            cpath = cp.as_posix().lower()
                            score = sum(1 for tok in parent_tokens if tok in cpath)
                            if score > best_score:
                                best_score = score
                                best = cp
                        chosen = best
                    if chosen:
                        try:
                            rel = os.path.relpath(chosen, dirp)
                            new_url = rel.replace('\\', '/')
                        except Exception:
                            pass
        # Fallback: if still unresolved, try mapping by filename across docs (best-effort)
        if not new_url:
            try:
                base_name = os.path.basename(url_path_only)
                if base_name:
                    # tolerant lookup in docs index
                    cands2 = _lookup_docs_candidates(base_name)
                    parent_tokens = [seg.lower() for seg in os.path.dirname(url_path_only).split('/') if seg]
                    chosen = None
                    best_score = -1
                    for cp in cands2:
                        cpath = cp.as_posix().lower()
                        score = sum(1 for tok in parent_tokens if tok in cpath)
                        if score > best_score:
                            best_score = score
                            chosen = cp
                    if chosen:
                        try:
                            rel = os.path.relpath(chosen.resolve(), dirp)
                        except Exception:
                            rel = os.path.relpath(chosen, dirp)
                        new_url = rel.replace('\\', '/')
            except Exception:
                pass
        if new_url and frag:
            new_url = new_url + frag
        if new_url and new_url != orig:
            changes.append((orig, new_url))
            return f"{before}{new_url}{after}"
        return m.group(0)

    new_text = pattern.sub(repl, text)
    return new_text, changes

def cmd_fix_doc_links(args) -> int:
    base = ROOT / 'docs'
    if not base.exists():
        log('docs directory not found')
        return 0
    total_files = 0
    total_changes = 0
    details = []
    for p in base.rglob('*.md'):
        if not p.is_file() or should_ignore(p):
            continue
        total_files += 1
        try:
            new_text, changes = rewrite_links_in_markdown(p)
            if changes:
                total_changes += len(changes)
                details.append({
                    'file': str(p.relative_to(ROOT)),
                    'changes': [{'from': a, 'to': b} for a, b in changes]
                })
                if args.apply:
                    p.write_text(new_text, encoding='utf-8')
        except Exception as e:
            details.append({'file': str(p.relative_to(ROOT)), 'error': str(e)})
    report = {
        'total_files': total_files,
        'total_link_rewrites': total_changes,
        'applied': bool(args.apply),
        'generated_at': datetime.now().isoformat(),
        'items': details[:200]
    }
    (ROOT / 'doc_link_fix_report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    log(f"Doc links rewrite {'applied' if args.apply else 'dry-run'}; files={total_files}, rewrites={total_changes} (report: doc_link_fix_report.json)")
    return 0

def cmd_run_all(args) -> int:
    # 1) check datasets
    d = scan_datasets()
    # 2) check models
    m = scan_models()
    # 3) check training system
    t = scan_training()
    # 4) decide training
    need_train = decide_training_needed(d, m) or args.force_train
    summary = {
        'datasets_ok': d.get('ok'),
        'models_count': m.get('count'),
        'need_train': bool(need_train),
    }
    log(f"Decision: need_train={need_train}")
    train_code = 0
    if need_train and not args.dry_run:
        train_code = cmd_train(argparse.Namespace(entry=args.entry, extra=args.extra or []))
    # 5) update docs
    upd_code = cmd_update_docs(argparse.Namespace(targets=None, apply=bool(args.apply)))
    # 6) fix doc links (dry-run if not apply)
    fix_code = cmd_fix_doc_links(argparse.Namespace(apply=bool(args.apply)))
    # 7) validate docs
    val_code = cmd_validate_docs(argparse.Namespace())
    final = {
        'summary': summary,
        'train_exit_code': train_code,
        'update_docs_exit_code': upd_code,
        'fix_links_exit_code': fix_code,
        'validate_docs_exit_code': val_code,
        'finished_at': datetime.now().isoformat(),
    }
    Path(ROOT / 'ai_orchestrator_report.json').write_text(json.dumps(final, indent=2, ensure_ascii=False), encoding='utf-8')
    log("Orchestration finished. Report: ai_orchestrator_report.json")
    # If any step failed, return non-zero
    return 0 if (train_code == 0 and upd_code == 0 and fix_code == 0 and val_code == 0) else 1

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='AI Orchestrator for project automation')
    sub = p.add_subparsers(dest='cmd', required=True)

    s1 = sub.add_parser('check-datasets', help='Scan and validate datasets')
    s1.set_defaults(func=cmd_check_datasets)

    s2 = sub.add_parser('check-models', help='Scan model registry')
    s2.set_defaults(func=cmd_check_models)

    s3 = sub.add_parser('check-training', help='Scan training logs')
    s3.set_defaults(func=cmd_check_training)

    s4 = sub.add_parser('train', help='Run training entry script')
    s4.add_argument('--entry', help='Training entry path relative to repo root (default: scripts/train.py)')
    s4.add_argument('extra', nargs='*', help='Extra args passed to training script')
    s4.set_defaults(func=cmd_train)

    s5 = sub.add_parser('update-docs', help='Auto-update markdown placeholders')
    s5.add_argument('--apply', action='store_true', help='Apply changes to files (otherwise dry-run/report only)')
    s5.add_argument('--targets', nargs='*', help='Limit to specific Markdown file paths relative to repo root')
    s5.set_defaults(func=cmd_update_docs)

    s6 = sub.add_parser('validate-docs', help='Validate markdown links')
    s6.set_defaults(func=cmd_validate_docs)

    s6b = sub.add_parser('fix-doc-links', help="Rewrite bad internal links like 'docs/...'")
    s6b.add_argument('--apply', action='store_true', help='Apply rewrites to files (otherwise dry-run)')
    s6b.set_defaults(func=cmd_fix_doc_links)

    # NEW: run-all orchestrator
    s7 = sub.add_parser('run-all', help='End-to-end pipeline: datasets->models->training decision->docs update->link fix->validate')
    s7.add_argument('--dry-run', action='store_true', help='Do not execute training, only make decisions and update docs in dry-run mode')
    s7.add_argument('--apply', action='store_true', help='Apply doc updates and link fixes to files')
    s7.add_argument('--force-train', action='store_true', help='Force run training step regardless of decision (ignored in --dry-run)')
    s7.add_argument('--entry', help='Training entry path relative to repo root (default: scripts/train.py)')
    s7.add_argument('extra', nargs='*', help='Extra args passed to training script')
    s7.set_defaults(func=cmd_run_all)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())