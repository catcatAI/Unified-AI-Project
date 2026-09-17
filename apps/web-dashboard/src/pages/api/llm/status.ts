import type { NextApiRequest, NextApiResponse } from 'next'

const BACKEND = process.env.BACKEND_URL || 'http://localhost:8000'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const resp = await fetch(`${BACKEND}/api/v1/llm/status`, {
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(5000),
    })
    if (!resp.ok) {
      res.status(resp.status).json({ error: `Backend returned ${resp.status}` })
      return
    }
    const data = await resp.json()
    res.status(200).json(data)
  } catch (e: any) {
    res.status(502).json({ error: e?.message || 'Backend unreachable' })
  }
}
