import type { NextApiRequest, NextApiResponse } from 'next'

type Data = {
  happiness: number
  hunger: number
  energy: number
  health: number
}

export default function handler(req: NextApiRequest, res: NextApiResponse<Data>) {
  res.status(200).json({
    happiness: 0.5,
    hunger: 0.5,
    energy: 0.5,
    health: 1.0
  })
}
