import type { BackendReadiness, CatalogOptions, RecommendationRequest, RecommendationResponse } from '@/types/api'
const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

interface FastApiValidationError {
 detail?: string | Array<{ loc?: Array<string | number>; msg?: string }>
}

function errorMessage(body: FastApiValidationError | null, status: number): string {
 if (typeof body?.detail === 'string') return body.detail
 if (Array.isArray(body?.detail)) {
  const messages = body.detail
   .map(item => item.msg)
   .filter((message): message is string => Boolean(message))
  if (messages.length) return `Проверьте параметры запроса: ${messages.join('; ')}`
 }
 return status === 422
  ? 'Проверьте параметры: дату, бюджет и длительность мероприятия.'
  : 'Сервис временно недоступен. Попробуйте ещё раз.'
}

async function request<T>(
 path: string,
 init: RequestInit = {},
 apiPrefix = '/api/v1',
 acceptedStatuses: number[] = [],
): Promise<T> {
 const controller = new AbortController()
 const timeout = setTimeout(() => controller.abort(), 15000)
 try {
    const response = await fetch(base + apiPrefix + path, { ...init, signal: controller.signal })
    if (!response.ok && !acceptedStatuses.includes(response.status)) {
      const body = await response.json().catch(() => null) as FastApiValidationError | null
      throw new Error(errorMessage(body, response.status))
  }
  return await response.json() as T
 } catch (error) {
  if (error instanceof TypeError) throw new Error('Не удалось связаться с сервером. Проверьте подключение и повторите запрос.')
  if (error instanceof Error && error.name === 'AbortError') throw new Error('Сервер отвечает слишком долго. Попробуйте ещё раз.')
  throw error
 } finally { clearTimeout(timeout) }
}
export const getBackendReadiness = () => request<BackendReadiness>('/ready', {}, '', [503])
export const getCatalogOptions = () => request<CatalogOptions>('/catalog/options')
export const getRecommendations = (payload: RecommendationRequest) => request<RecommendationResponse>('/recommendations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
