import type { NextApiRequest, NextApiResponse } from 'next'

// Interacting with the pet (pet / feed / play / rest).
//
// The actions used to mutate a local in-memory object that had nothing to do
// with the backend. Now they are forwarded to the backend, which applies them
// to the real digital life (the state matrix), and the *real* state comes
// back. If the backend is unreachable the request fails honestly (503)
// instead of pretending the interaction happened.

interface PetState {
  happiness: number
  hunger: number
  energy: number
  health: number
  life_phase?: string | null
  emotion?: string | null
  source?: string
  error?: string
}

const BACKEND = process.env.BACKEND_URL || 'http://localhost:8000'

export default async function handler(req: NextApiRequest, res: NextApiResponse<PetState>) {
  if (req.method !== 'POST') {
    return res.status(405).json({
      happiness: 0,
      hunger: 0,
      energy: 0,
      health: 0,
      error: 'POST required',
    })
  }

  const { action } = req.body || {}
  if (!action || typeof action !== 'string') {
    return res.status(400).json({
      happiness: 0,
      hunger: 0,
      energy: 0,
      health: 0,
      error: 'action is required',
    })
  }

  try {
    const resp = await fetch(`${BACKEND}/api/v1/system/pet/interact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ action }),
      signal: AbortSignal.timeout(5000),
    })
    if (!resp.ok) {
      const text = await resp.text().catch(() => '')
      return res.status(resp.status).json({
        happiness: 0,
        hunger: 0,
        energy: 0,
        health: 0,
        error: `Backend returned ${resp.status}${text ? `: ${text.slice(0, 200)}` : ''}`,
      })
    }
    const data = (await resp.json()) as PetState
    res.status(200).json(data)
  } catch (e: any) {
    res.status(502).json({
      happiness: 0,
      hunger: 0,
      energy: 0,
      health: 0,
      error: e?.message || 'Backend unreachable',
    })
  }
}
