<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ArrowRight, CalendarDays, Check, ChevronDown, Compass, LoaderCircle, MapPin, Search, SlidersHorizontal, Sparkles, Users, RefreshCw, CircleAlert } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import ContractorCard from '@/components/ContractorCard.vue'
import { getBackendReadiness, getCatalogOptions } from '@/api/client'
import { useRecommendations } from '@/composables/useRecommendations'
import type { CatalogOptions, RecommendationRequest } from '@/types/api'

const options = ref<CatalogOptions | null>(null)
const optionsLoading = ref(true)
const optionsError = ref('')
const backendState = ref<'checking' | 'ready' | 'degraded' | 'offline'>('checking')
const form = reactive({ city: '', event_date: '2026-11-14', event_format: '', category: '', budget_kzt: '1000000', duration_hours: '', language: '' })
const { result, loading, error, submitted, search } = useRecommendations()
const validation = ref('')
const ready = computed(() => !!options.value?.cities.length && !!options.value?.categories.length && !!options.value?.event_formats.length)
const heading = computed(() => loading.value ? 'Ищем вашу команду' : result.value?.status === 'matched' ? 'Ваша подборка' : result.value ? 'Попробуем другие условия?' : 'Хорошее событие начинается с команды')
const exclusionLabels: Record<string, string> = { busy: 'Заняты на эту дату', over_budget: 'Выше бюджета', wrong_format: 'Другой формат', wrong_language: 'Не подходит язык', insufficient_duration: 'Недостаточная длительность' }
const exclusions = computed(() => Object.entries(result.value?.meta.exclusions || {}).filter(([, count]) => count > 0))
const backendStatus = computed(() => ({
 checking: { label: 'Проверяем подключение', title: 'Проверка нового API' },
 ready: { label: 'Каталог подключён', title: 'PostgreSQL, Elasticsearch и Redis доступны' },
 degraded: { label: 'Каталог доступен без кэша', title: 'Каталог работает, Redis временно недоступен' },
 offline: { label: 'Сервис недоступен', title: 'Не удалось подключиться к API' },
}[backendState.value]))

async function checkBackend() {
 try {
  const readiness = await getBackendReadiness()
  backendState.value = readiness.dependencies.catalog
   ? readiness.dependencies.cache ? 'ready' : 'degraded'
   : 'offline'
 } catch {
  backendState.value = 'offline'
 }
}
async function loadOptions() {
 optionsLoading.value = true; optionsError.value = ''
 try {
  options.value = await getCatalogOptions()
  form.city ||= options.value.cities[0] || ''
  form.category ||= options.value.categories[0] || ''
  form.event_format ||= options.value.event_formats[0] || ''
 } catch (e) { optionsError.value = e instanceof Error ? e.message : 'Не удалось загрузить параметры.' }
 finally { optionsLoading.value = false }
}
function submit() {
 validation.value = ''
 const budget = Number(form.budget_kzt)
 const duration = form.duration_hours ? Number(form.duration_hours) : undefined
 if (!form.city || !form.category || !form.event_format || !form.event_date || form.event_date < '2026-09-23' || form.event_date > '2026-12-31' || !Number.isSafeInteger(budget) || budget <= 0 || (duration !== undefined && (!Number.isFinite(duration) || duration <= 0 || duration > 24))) {
  validation.value = 'Заполните обязательные поля. Бюджет — целое положительное число, длительность — до 24 часов, дата — в пределах календаря.'
  return
 }
 const payload: RecommendationRequest = { city: form.city, event_date: form.event_date, event_format: form.event_format, category: form.category, budget_kzt: budget, ...(duration !== undefined ? { duration_hours: duration } : {}), ...(form.language ? { language: form.language } : {}) }
 void search(payload)
}
onMounted(async () => {
 await loadOptions()
 await checkBackend()
})
</script>

<template>
 <div class="app-shell">
  <header class="site-header">
   <a href="#" class="brand" aria-label="Событие — главная"><span class="brand-mark"><Compass :size="24" /></span>событие<span class="brand-dot">.</span></a>
   <span class="header-section">Подбор подрядчиков</span>
   <span class="header-note" :title="backendStatus.title"><span class="status-dot" :class="`status-${backendState}`" /> {{ backendStatus.label }}</span>
  </header>
  <main>
   <section class="hero">
    <div class="hero-copy"><div class="eyebrow"><span /> ЛЮДИ, КОТОРЫЕ СОЗДАЮТ МОМЕНТЫ</div><h1>Ваше событие.<br /><span>Ваша команда.</span></h1><p>Найдите тех, кто воплотит вашу идею.<br class="desktop-break" /> Подберём подрядчиков под дату, пожелания и бюджет.</p><div class="hero-points"><span><Check :size="15" /> Свободны на вашу дату</span><span><Check :size="15" /> В рамках бюджета</span></div></div>
    <div class="hero-art" aria-hidden="true"><div class="orbit orbit-one" /><div class="orbit orbit-two" /><div class="art-center"><Sparkles :size="42" stroke-width="1.2" /></div><div class="art-label label-top"><CalendarDays :size="17" /> Всё начинается с даты</div><div class="art-label label-bottom"><Users :size="17" /> И подходящих людей</div><span class="art-star">✳</span></div>
   </section>
   <div class="workspace">
    <aside class="filter-panel">
     <div class="panel-title"><div><span class="section-kicker">01 / ВАШЕ СОБЫТИЕ</span><h2>Расскажите о планах</h2></div><SlidersHorizontal :size="19" /></div>
     <div v-if="optionsLoading" class="options-notice" role="status"><LoaderCircle class="spin" :size="18" /> Загружаем параметры…</div>
     <div v-else-if="optionsError" class="error-notice" role="alert"><p>{{ optionsError }}</p><Button variant="outline" @click="loadOptions"><RefreshCw :size="15" /> Повторить</Button></div>
     <div v-else-if="!ready" class="options-notice">Каталог пока пуст. Параметры появятся после загрузки подрядчиков.<Button variant="outline" @click="loadOptions">Обновить</Button></div>
     <form @submit.prevent="submit">
      <fieldset :disabled="!ready || optionsLoading || loading">
       <label for="city">Город <span>*</span></label><div class="select-wrap"><MapPin class="field-icon" :size="16" /><select id="city" v-model="form.city" required class="with-icon"><option value="" disabled>Выберите город</option><option v-for="city in options?.cities" :key="city">{{ city }}</option></select><ChevronDown :size="15" /></div>
       <label for="date">Дата мероприятия <span>*</span></label><input id="date" v-model="form.event_date" type="date" min="2026-09-23" max="2026-12-31" required /><p class="field-hint">Календарь: 23 сентября — 31 декабря 2026</p>
       <label for="format">Формат события <span>*</span></label><div class="select-wrap"><select id="format" v-model="form.event_format" required><option value="" disabled>Выберите формат</option><option v-for="format in options?.event_formats" :key="format">{{ format }}</option></select><ChevronDown :size="15" /></div>
       <label for="category">Кого ищем? <span>*</span></label><div class="select-wrap"><select id="category" v-model="form.category" required><option value="" disabled>Выберите категорию</option><option v-for="category in options?.categories" :key="category">{{ category }}</option></select><ChevronDown :size="15" /></div>
       <label for="budget">Бюджет на подрядчика <span>*</span></label><div class="input-wrap"><input id="budget" v-model="form.budget_kzt" type="number" min="1" step="1" max="9007199254740991" required /><span>₸</span></div>
       <details class="extra-filters"><summary>Дополнительные пожелания <ChevronDown :size="15" /></summary><label for="duration">Длительность, часов</label><input id="duration" v-model="form.duration_hours" type="number" min="0.1" max="24" step="any" placeholder="Неважно" /><label for="language">Язык</label><div class="select-wrap"><select id="language" v-model="form.language"><option value="">Любой язык</option><option v-for="language in options?.languages" :key="language">{{ language }}</option></select><ChevronDown :size="15" /></div></details>
       <p v-if="validation" class="validation" role="alert">{{ validation }}</p>
       <Button class="search-button" type="submit"><LoaderCircle v-if="loading" class="spin" :size="17" /><Search v-else :size="17" />{{ loading ? 'Подбираем…' : 'Найти подрядчиков' }}<ArrowRight v-if="!loading" :size="17" /></Button>
       <p class="form-footnote">До 3 подходящих вариантов с объяснением выбора</p>
      </fieldset>
     </form>
    </aside>
    <section class="results-panel" aria-live="polite" :aria-busy="loading">
     <div class="results-heading"><div><span class="section-kicker">02 / ВАША КОМАНДА</span><h2>{{ heading }}</h2></div><span v-if="result?.status === 'matched'" class="result-count">{{ result.items.length }} из {{ result.meta.eligible_count }}</span></div>
     <div v-if="submitted" class="query-summary"><span>{{ submitted.city }}</span><span>{{ submitted.event_date.split('-').reverse().join('.') }}</span><span>{{ submitted.category }}</span><span>до {{ new Intl.NumberFormat('ru-RU').format(submitted.budget_kzt) }} ₸</span><span>{{ submitted.event_format }}</span><span v-if="submitted.language">{{ submitted.language }}</span><span v-if="submitted.duration_hours">{{ submitted.duration_hours }} ч</span></div>
     <template v-if="loading"><p class="results-description">Проверяем доступность и условия подрядчиков…</p><div class="cards-grid"><div v-for="i in 3" :key="i" class="skeleton-card"><div /><div /><div /><div /></div></div></template>
     <div v-else-if="error" class="empty-state error-state" role="alert"><CircleAlert :size="32" /><h3>Не удалось получить подборку</h3><p>{{ error }}</p><Button v-if="submitted" variant="outline" @click="search(submitted)"><RefreshCw :size="16" /> Повторить запрос</Button></div>
     <template v-else-if="result?.status === 'matched'"><p class="results-description">{{ result.message }}</p><div class="cards-grid"><ContractorCard v-for="(contractor, index) in result.items.slice(0, 3)" :key="contractor.id" :contractor="contractor" :index="index" /></div><p class="results-footnote"><Check :size="15" /> Подбор учитывает дату, формат, бюджет и ваши пожелания.</p></template>
     <div v-else-if="result" class="empty-state"><Search :size="32" /><h3>{{ result.status === 'category_not_found' ? 'В этом городе пока нет такой категории' : 'На эти условия пока нет совпадений' }}</h3><p>{{ result.message }}</p><div v-if="exclusions.length" class="exclusions"><span v-for="[key, count] in exclusions" :key="key">{{ exclusionLabels[key] }} <b>{{ count }}</b></span></div><p>{{ result.status === 'category_not_found' ? 'Выберите другой город или категорию слева.' : 'Попробуйте изменить дату, увеличить бюджет или уточнить пожелания.' }}</p></div>
     <div v-else class="welcome-state"><div class="welcome-icon"><Users :size="32" stroke-width="1.3" /></div><h3>Меньше поисков.<br />Больше предвкушения.</h3><p>Расскажите о событии — мы найдём подходящих<br class="desktop-break" /> специалистов и объясним, почему выбрали их.</p><div class="steps"><div><span>01</span><strong>Задайте условия</strong><p>Город, дата и бюджет</p></div><div><span>02</span><strong>Получите подборку</strong><p>До трёх совпадений</p></div><div><span>03</span><strong>Сравните варианты</strong><p>С понятными объяснениями</p></div></div></div>
     <div class="trust-note"><Sparkles :size="19" /><div><strong>У каждого совпадения есть причина</strong><p>Рекомендации основаны на данных профилей и календаре занятости.</p></div></div>
    </section>
   </div>
  </main>
  <footer><a class="brand footer-brand" href="#">событие.</a><span>Анонимные профили подрядчиков · Хакатон 2026</span><span>Создавайте моменты, которые остаются.</span></footer>
 </div>
</template>
