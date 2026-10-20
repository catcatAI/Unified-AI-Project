import type { NextApiRequest, NextApiResponse } from 'next'

// The pet panel shows the REAL digital-life state.
//
// It used to be a local in-memory simulation: an object in this module that
// decayed on its own and answered "pet"/"feed" with hard-coded deltas. The
// numbers on screen had nothing to do with the system they claimed to
// describe. The backend now reports the real state matrix (and names the
// source of every field), and the local simulation is only a clearly
// labelled fallback for when the backend cannot be reached.

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

// Fallback only: used when the backend is unreachable. Marked as
// "simulated" so the panel can say the numbers are not the real thing.
const SIMULATED: PetState = {
  happiness: 0.5,
  hunger: 0.5,
  energy: 0.5,
  health: 1.0,
  source: 'simulated',
  error: 'Backend unreachable — showing simulated values',
}

export default async function handler(req: NextApiRequest, res: NextApiResponse<PetState>) {
  try {
    const resp = await fetch(`${BACKEND}/api/v1/system/pet`, {
      headers: { Accept: 'application/json' },
      signal: AbortSignal.timeout(5000),
    })
    if (!resp.ok) {
      res.status(resp.status).json({ ...SIMULATED, error: `Backend returned ${resp.status}` })
      return
    }
    const data = (await resp.json()) as PetState
    res.status(200).json(data)
  } catch (e: any) {
    res.status(502).json({ ...SIMULATED, error: e?.message || 'Backend unreachable' })
  }
}
