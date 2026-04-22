import type { TripPlanRequest, TripPlan } from '../types'

const BASE = 'http://localhost:8000/api'

export async function generateTripPlan(
  req: TripPlanRequest,
  onProgress: (node: string) => void,
): Promise<TripPlan> {
  const response = await fetch(`${BASE}/trip/plan/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${response.status}`)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  return new Promise((resolve, reject) => {
    const pump = async () => {
      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const event = JSON.parse(line.slice(6))

            if (event.type === 'progress') {
              onProgress(event.node)
            } else if (event.type === 'result') {
              resolve(event.data as TripPlan)
              return
            } else if (event.type === 'error') {
              reject(new Error(event.message))
              return
            }
          }
        }
        reject(new Error('连接中断，未收到规划结果'))
      } catch (e) {
        reject(e)
      }
    }
    pump()
  })
}
