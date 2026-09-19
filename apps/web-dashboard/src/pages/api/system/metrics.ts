import type { NextApiRequest, NextApiResponse } from 'next'

// Proxies real system metrics from the backend ops API (psutil-based).
// Replaces the former Math.random() mock (removed per RELEASE_CRITERIA mock-data gap).

const BACKEND = process.env.BACKEND_URL || 'http://localhost:8000'

type Data = {
  cpu: number
  memory: number
  disk: number
  uptime?: number
  activeConnections?: number
  error?: string
}

export default async function handler(req: NextApiRequest, res: NextApiResponse<Data>) {
  try {
    const resp = await fetch(`${BACKEND}/api/v1/ops/status`, {
      headers: { Accept: 'application/json' },
      signal: AbortSignal.timeout(5000),
    })
    if (!resp.ok) {
      res
        .status(resp.status)
        .json({ cpu: 0, memory: 0, disk: 0, error: `Backend returned ${resp.status}` })
      return
    }
    const data = await resp.json()
    const m = data.metrics || {}
    res.status(200).json({
      cpu: typeof m.cpu_percent === 'number' ? m.cpu_percent : 0,
      memory: typeof m.memory_percent === 'number' ? m.memory_percent : 0,
      disk: typeof m.disk_percent === 'number' ? m.disk_percent : 0,
    })
  } catch (e: any) {
    res.status(502).json({ cpu: 0, memory: 0, disk: 0, error: e?.message || 'Backend unreachable' })
  }
}
