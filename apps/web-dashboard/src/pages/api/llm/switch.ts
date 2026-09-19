import type { NextApiRequest, NextApiResponse } from 'next'

const BACKEND = process.env.BACKEND_URL || 'http://localhost:8000'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' })
    return
  }
  try {
    const resp = await fetch(`${BACKEND}/api/v1/llm/switch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(req.body),
      signal: AbortSignal.timeout(5000),
    })
    const data = await resp.json()
    res.status(resp.status).json(data)
  } catch (e: any) {
    res.status(502).json({ error: e?.message || 'Backend unreachable' })
  }
}
