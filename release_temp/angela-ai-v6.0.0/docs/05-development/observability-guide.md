# Observability Guide: Hot Status Metrics & Dashboard Schema

This guide aligns the /api/v1/hot/status endpoint fields with a minimal dashboard schema for quick visibility.

## 1. Endpoint
- `GET /api/v1/hot/status`
- Returns best-effort fields (some may be null depending on runtime or mocks).

Top-level keys:
- `draining: boolean`
- `services_initialized: { [service_name]: boolean }`
- `hsp: object` — communication status from HSPConnector.get_communication_status()
- `mcp: object` — communication status from MCPConnector.get_communication_status()
- `metrics: object` — best-effort metrics

## 2. Metrics (current)
```jsonc
{
  "metrics": {
    "hsp": {
      "is_connected": true,
      "pending_acks_count": 0,
      "retry_counts_active": 0
    },
    "mcp": {
      "is_connected": false,
      "fallback_initialized": false
    },
    "learning": {
      "known_ai_count": 1,
      "tools": {
        "total_invocations": 0,
        "success_rate": 0.0,
        "recent_failures": 0,
        "avg_latency": null
      }
    },
    "memory": {
      "ham_store_size": 124
    },
    "lis": {
      "incidents_recent": 5,
      "antibodies_recent": 2
    }
  }
}
```

Notes:
- The `learning.tools` block is reserved for the Action–Tool Policy aggregation to be implemented.
- Values are best-effort and may be null; clients should handle missing fields gracefully.

## 3. Minimal Dashboard Schema (proposal)
A compact JSON schema for frontends to render a status panel quickly.

```jsonc
{
  "version": "v0.1",
  "panels": [
    { "id": "hsp", "title": "HSP", "type": "kpi", "fields": [
      { "label": "Connected", "path": "metrics.hsp.is_connected" },
      { "label": "Pending ACKs", "path": "metrics.hsp.pending_acks_count" },
      { "label": "Active Retries", "path": "metrics.hsp.retry_counts_active" }
    ]},
    { "id": "mcp", "title": "MCP", "type": "kpi", "fields": [
      { "label": "Connected", "path": "metrics.mcp.is_connected" },
      { "label": "Fallback Init", "path": "metrics.mcp.fallback_initialized" }
    ]},
    { "id": "learning", "title": "Learning / Trust", "type": "kpi", "fields": [
      { "label": "Known AIs", "path": "metrics.learning.known_ai_count" },
      { "label": "Tool Success %", "path": "metrics.learning.tools.success_rate" }
    ]},
    { "id": "memory", "title": "Memory (HAM)", "type": "kpi", "fields": [
      { "label": "Store Size", "path": "metrics.memory.ham_store_size" }
    ]},
    { "id": "lis", "title": "LIS", "type": "kpi", "fields": [
      { "label": "Incidents (recent)", "path": "metrics.lis.incidents_recent" },
      { "label": "Antibodies (recent)", "path": "metrics.lis.antibodies_recent" }
    ]}
  ]
}
```

## 4. Client Guidelines
- Treat all fields as optional; default to "N/A" when absent.
- Poll frequency: 5–10s for dev; consider backoff and caching in production.
- Surface last update timestamp and, optionally, a link to raw JSON for debugging.

## 5. Next Steps
- Implement Action–Tool Policy logging in ToolDispatcher and aggregate into `metrics.learning.tools`.
- Add unit/integration tests for status metrics.
- Iterate on dashboard schema with frontend needs.
