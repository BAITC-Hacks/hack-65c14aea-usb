import { ref } from 'vue'
import { getRecommendations } from '@/api/client'
import type { RecommendationRequest, RecommendationResponse } from '@/types/api'
export function useRecommendations() {
 const result = ref<RecommendationResponse | null>(null)
 const loading = ref(false)
 const error = ref('')
 const submitted = ref<RecommendationRequest | null>(null)
 async function search(payload: RecommendationRequest) {
  if (loading.value) return
  submitted.value = { ...payload }; loading.value = true; error.value = ''; result.value = null
  try { result.value = await getRecommendations(payload) }
  catch (e) { error.value = e instanceof Error ? e.message : 'Не удалось загрузить подборку.' }
  finally { loading.value = false }
 }
 return { result, loading, error, submitted, search }
}