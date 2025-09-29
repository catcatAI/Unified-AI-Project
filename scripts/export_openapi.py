#!/usr/bin/env python3
import os
import json
import pathlib
import sys


BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')
OPENAPI_URL = BASE_URL.rstrip('/') + '/api/v1/openapi'

out_dir = pathlib.Path('Unified-AI-Project/docs/api')
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / 'openapi.json'

try:
    with urllib.request.urlopen(OPENAPI_URL, timeout=10) as resp:
        data = resp.read().decode('utf-8')
        # validate json
        _ = json.loads(data)
        out_path.write_text(data, encoding='utf-8')
        _ = print(f'✅ Exported OpenAPI to {out_path}')
except Exception as e:
    _ = print(f'❌ Failed to export OpenAPI from {OPENAPI_URL}: {e}')
    _ = sys.exit(1)