export interface CatalogOptions { cities: string[]; categories: string[]; event_formats: string[]; languages: string[] }
export interface BackendReadiness {
 status: 'ready' | 'not_ready'
 dependencies: { catalog: boolean; cache: boolean }
}
export interface RecommendationRequest { city: string; event_date: string; event_format: string; category: string; budget_kzt: number; duration_hours?: number; language?: string }
export interface Contractor { id: string; name: string; categories: string[]; city: string; price_from_kzt: number; synthetic: boolean; explanation: string }
export interface RecommendationResponse {
 status: 'matched' | 'category_not_found' | 'no_eligible_candidates'
 items: Contractor[]
 message: string
 meta: { total_in_city_category: number; eligible_count: number; exclusions: Record<'busy' | 'over_budget' | 'wrong_format' | 'wrong_language' | 'insufficient_duration', number> }
}
