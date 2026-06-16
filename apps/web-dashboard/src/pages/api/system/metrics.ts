import type { NextApiRequest, NextApiResponse } from 'next'

type Data = {
  cpu: number
  memory: number
  uptime: number
  activeConnections: number
  totalInteractions: number
}

export default function handler(req: NextApiRequest, res: NextApiResponse<Data>) {
  res.status(200).json({
    cpu: Math.random() * 30 + 10,
    memory: Math.random() * 20 + 40,
    uptime: Date.now() / 1000,
    activeConnections: 1,
    totalInteractions: 0
  })
}
