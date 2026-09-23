<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import {
  ArrowRight,
  CalendarDays,
  Check,
  ChevronDown,
  CircleAlert,
  Clock3,
  Compass,
  Database,
  Gauge,
  Languages,
  LoaderCircle,
  MapPin,
  RefreshCw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Target,
  Users,
  WalletCards,
} from 'lucide-vue-next'

import { Button } from '@/components/ui/button'
import ContractorCard from '@/components/ContractorCard.vue'
import ContractorDetail from '@/components/ContractorDetail.vue'
import KazakhstanMap from '@/components/KazakhstanMap.vue'
import { getBackendReadiness, getCatalogOptions } from '@/api/client'
import { useRecommendations } from '@/composables/useRecommendations'
import type { CatalogOptions, Contractor, RecommendationRequest } from '@/types/api'

interface DemoScenario {
  title: string
  description: string
  tone: 'dense' | 'rare' | 'empty'
  request: RecommendationRequest
}

const options = ref<CatalogOptions | null>(null)
const optionsLoading = ref(true)
const optionsError = ref('')
const backendState = ref<'checking' | 'ready' | 'degraded' | 'offline'>('checking')
const validation = ref('')
const selectedContractor = ref<Contractor | null>(null)
const selectedRank = ref(1)

const form = reactive({
  city: '',
  event_date: '2026-10-10',
  event_format: '',
  category: '',
  budget_kzt: '6000000',
  duration_hours: '',
  language: '',
})

const demoScenarios: DemoScenario[] = [
  {
    title: 'Плотная категория',
    description: 'Фотографы · осенняя дата',
    tone: 'dense',
    request: {
      city: 'Алматы',
      event_date: '2026-10-10',
      event_format: 'свадьба',
      category: 'Фотограф',
      budget_kzt: 6000000,
    },
  },
  {
    title: 'Редкая категория',
    description: 'Флористы · объяснение нехватки',
    tone: 'rare',
    request: {
      city: 'Алматы',
      event_date: '2026-10-10',
      event_format: 'свадьба',
      category: 'Флорист',
      budget_kzt: 6000000,
    },
  },
  {
    title: 'Без результата',
    description: 'Кандидаты есть · бюджет 1 ₸',
    tone: 'empty',
    request: {
      city: 'Алматы',
      event_date: '2026-10-10',
      event_format: 'свадьба',
      category: 'Фотограф',
      budget_kzt: 1,
    },
  },
]

const { result, loading, error, submitted, search } = useRecommendations()

const ready = computed(() =>
  Boolean(
    options.value?.cities.length
      && options.value?.categories.length
      && options.value?.event_formats.length,
  ),
)

const resultHeading = computed(() => {
  if (loading.value) return 'Сверяем условия'
  if (result.value?.status === 'matched') {
    const count = result.value.items.length
    return count === 1 ? 'Нашёлся 1 подрядчик' : `Нашлись ${count} подрядчика`
  }
  if (result.value?.status === 'category_not_found') return 'В этом городе пока нет такой категории'
  if (result.value?.status === 'no_eligible_candidates') return 'На эти условия пока нет совпадений'
  return 'Здесь появится подборка'
})

const backendStatus = computed(() => ({
  checking: { label: 'Проверяем сервис', title: 'Проверяем доступность API' },
  ready: { label: 'Сервис готов', title: 'Каталог и кэш отвечают' },
  degraded: { label: 'Каталог доступен без кэша', title: 'Подбор работает без Redis-кэша' },
  offline: { label: 'Нет подключения', title: 'API сейчас недоступен' },
}[backendState.value]))

const exclusionLabels: Record<string, string> = {
  busy: 'заняты на дату',
  over_budget: 'выше бюджета',
  wrong_format: 'не берут формат',
  wrong_language: 'не работают на языке',
  insufficient_duration: 'не хватает часов',
}

const exclusions = computed(() =>
  Object.entries(result.value?.meta.exclusions || {}).filter(([, count]) => count > 0),
)

const money = (value: number) => new Intl.NumberFormat('ru-RU').format(value)
const humanDate = (value: string) =>
  new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
    .format(new Date(`${value}T00:00:00`))

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
  optionsLoading.value = true
  optionsError.value = ''
  try {
    options.value = await getCatalogOptions()
    form.city ||= options.value.cities.includes('Алматы')
      ? 'Алматы'
      : options.value.cities[0] || ''
    form.category ||= options.value.categories.includes('Фотограф')
      ? 'Фотограф'
      : options.value.categories[0] || ''
    form.event_format ||= options.value.event_formats.includes('свадьба')
      ? 'свадьба'
      : options.value.event_formats[0] || ''
  } catch (loadError) {
    optionsError.value = loadError instanceof Error
      ? loadError.message
      : 'Не удалось загрузить параметры.'
  } finally {
    optionsLoading.value = false
  }
}

function createPayload(): RecommendationRequest | null {
  validation.value = ''
  const budget = Number(form.budget_kzt)
  const duration = form.duration_hours ? Number(form.duration_hours) : undefined

  if (
    !form.city
    || !form.category
    || !form.event_format
    || !form.event_date
    || form.event_date < '2026-09-23'
    || form.event_date > '2026-12-31'
    || !Number.isSafeInteger(budget)
    || budget <= 0
    || (duration !== undefined && (!Number.isFinite(duration) || duration <= 0 || duration > 24))
  ) {
    validation.value = 'Проверьте обязательные поля, дату, бюджет и длительность.'
    return null
  }

  return {
    city: form.city,
    event_date: form.event_date,
    event_format: form.event_format,
    category: form.category,
    budget_kzt: budget,
    ...(duration !== undefined ? { duration_hours: duration } : {}),
    ...(form.language ? { language: form.language } : {}),
  }
}

async function runSearch(payload: RecommendationRequest, shouldScroll = true) {
  await search(payload)
  await nextTick()
  if (shouldScroll) {
    document.querySelector('#results')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function submit() {
  const payload = createPayload()
  if (payload) {
    selectedContractor.value = null
    void runSearch(payload)
  }
}

function openContractor(contractor: Contractor, index: number) {
  selectedContractor.value = contractor
  selectedRank.value = index + 1
}

async function selectCity(city: string) {
  if (!options.value?.cities.includes(city)) return
  form.city = city
  await nextTick()
  const payload = createPayload()
  if (payload) await runSearch(payload)
}

async function applyScenario(scenario: DemoScenario) {
  const request = scenario.request
  if (!options.value) return
  form.city = options.value.cities.includes(request.city) ? request.city : options.value.cities[0] || ''
  form.category = options.value.categories.includes(request.category) ? request.category : options.value.categories[0] || ''
  form.event_format = options.value.event_formats.includes(request.event_format) ? request.event_format : options.value.event_formats[0] || ''
  form.event_date = request.event_date
  form.budget_kzt = String(request.budget_kzt)
  form.duration_hours = request.duration_hours ? String(request.duration_hours) : ''
  form.language = request.language && options.value.languages.includes(request.language) ? request.language : ''
  await nextTick()
  const payload = createPayload()
  if (payload) await runSearch(payload)
}

async function compareDate() {
  const nextDate = submitted.value?.event_date === '2026-11-14' ? '2026-10-10' : '2026-11-14'
  form.event_date = nextDate
  await nextTick()
  const payload = createPayload()
  if (payload) await runSearch(payload)
}

onMounted(async () => {
  await loadOptions()
  await checkBackend()
})
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <a href="#" class="product-brand" aria-label="Точка события — главная">
        <span class="brand-mark"><Compass :size="19" /></span>
        <span>точка события</span>
      </a>

      <nav aria-label="Навигация по странице">
        <a href="#search">Подбор</a>
        <a href="#map">Города</a>
      </nav>

      <span class="api-status" :class="`api-status--${backendState}`" :title="backendStatus.title">
        <i />
        {{ backendStatus.label }}
      </span>
    </header>

    <main class="page">
      <section class="hero">
        <div class="hero-copy">
          <span class="eyebrow"><Sparkles :size="14" /> Объяснимый подбор подрядчиков</span>
          <h1>Три подходящих варианта.<br /><em>Ни одного случайного.</em></h1>
          <p>Учитываем календарь, бюджет и формат события. Для каждой рекомендации показываем конкретную причину выбора.</p>
          <a class="hero-action" href="#search">Начать подбор <ArrowRight :size="16" /></a>
        </div>

        <div class="hero-metrics" aria-label="Показатели сервиса">
          <div><strong>66</strong><span>профилей в каталоге</span></div>
          <div><strong>≤ 3</strong><span>варианта в ответе</span></div>
          <div><strong>100</strong><span>дней календаря</span></div>
        </div>
      </section>

      <section id="search" class="section-card search-section">
        <div class="section-heading">
          <div>
            <span class="section-index">01 · Параметры</span>
            <h2>Расскажите о событии</h2>
            <p>Все поля и варианты загружаются из действующего backend-каталога.</p>
          </div>
          <span class="heading-icon"><SlidersHorizontal :size="21" /></span>
        </div>

        <div v-if="optionsLoading" class="inline-notice" role="status">
          <LoaderCircle class="spin" :size="18" /> Загружаем каталог…
        </div>
        <div v-else-if="optionsError" class="inline-notice error-notice" role="alert">
          <span>{{ optionsError }}</span>
          <Button variant="outline" @click="loadOptions"><RefreshCw :size="15" /> Повторить</Button>
        </div>

        <form @submit.prevent="submit">
          <fieldset :disabled="!ready || optionsLoading || loading">
            <div class="form-grid">
              <label>
                <span><MapPin :size="14" /> Город *</span>
                <span class="control select-control">
                  <select id="city" v-model="form.city" required aria-label="Город">
                    <option value="" disabled>Выберите город</option>
                    <option v-for="city in options?.cities" :key="city">{{ city }}</option>
                  </select>
                  <ChevronDown :size="15" />
                </span>
              </label>

              <label>
                <span><CalendarDays :size="14" /> Дата *</span>
                <span class="control">
                  <input id="date" v-model="form.event_date" type="date" min="2026-09-23" max="2026-12-31" required />
                </span>
              </label>

              <label>
                <span><Sparkles :size="14" /> Формат *</span>
                <span class="control select-control">
                  <select id="format" v-model="form.event_format" required aria-label="Формат события">
                    <option value="" disabled>Выберите формат</option>
                    <option v-for="format in options?.event_formats" :key="format">{{ format }}</option>
                  </select>
                  <ChevronDown :size="15" />
                </span>
              </label>

              <label>
                <span><Users :size="14" /> Категория *</span>
                <span class="control select-control">
                  <select id="category" v-model="form.category" required aria-label="Категория подрядчика">
                    <option value="" disabled>Кого ищем?</option>
                    <option v-for="category in options?.categories" :key="category">{{ category }}</option>
                  </select>
                  <ChevronDown :size="15" />
                </span>
              </label>

              <label>
                <span><WalletCards :size="14" /> Бюджет *</span>
                <span class="control money-control">
                  <input id="budget" v-model="form.budget_kzt" type="number" min="1" step="1" max="9007199254740991" required />
                  <b>₸</b>
                </span>
              </label>
            </div>

            <details class="optional-fields">
              <summary><span><SlidersHorizontal :size="14" /> Уточнить длительность и язык</span><ChevronDown :size="15" /></summary>
              <div class="optional-grid">
                <label>
                  <span><Clock3 :size="14" /> Длительность, часов</span>
                  <span class="control"><input id="duration" v-model="form.duration_hours" type="number" min="0.1" max="24" step="any" placeholder="Неважно" /></span>
                </label>
                <label>
                  <span><Languages :size="14" /> Язык работы</span>
                  <span class="control select-control">
                    <select id="language" v-model="form.language" aria-label="Язык работы">
                      <option value="">Любой язык</option>
                      <option v-for="language in options?.languages" :key="language">{{ language }}</option>
                    </select>
                    <ChevronDown :size="15" />
                  </span>
                </label>
              </div>
            </details>

            <p v-if="validation" class="validation" role="alert">{{ validation }}</p>

            <Button class="primary-action" type="submit">
              <LoaderCircle v-if="loading" class="spin" :size="17" />
              <Search v-else :size="17" />
              {{ loading ? 'Проверяем 66 профилей…' : 'Подобрать подрядчиков' }}
              <ArrowRight v-if="!loading" :size="17" />
            </Button>
          </fieldset>
        </form>

        <div class="demo-strip">
          <div class="demo-intro">
            <span>Быстрый показ</span>
            <strong>Три сценария из Definition of Done</strong>
          </div>
          <button
            v-for="scenario in demoScenarios"
            :key="scenario.title"
            type="button"
            class="scenario-button"
            :class="`scenario-button--${scenario.tone}`"
            :disabled="!ready || loading"
            @click="applyScenario(scenario)"
          >
            <span>{{ scenario.title }}</span>
            <small>{{ scenario.description }}</small>
            <ArrowRight :size="14" />
          </button>
        </div>
      </section>

      <section id="map" class="map-section">
        <div class="map-copy">
          <span class="section-index">02 · География</span>
          <h2>Выберите город на карте</h2>
          <p>Нажатие меняет поле «Город» и сразу отправляет текущие условия в backend. Вы увидите только реальных кандидатов из выбранной географии.</p>
          <ul>
            <li><Check :size="15" /> Алматы и Астана — локальные профили</li>
            <li><Check :size="15" /> «Зарубежье» — выездные подрядчики</li>
          </ul>
        </div>
        <KazakhstanMap
          :cities="options?.cities || []"
          :selected-city="form.city"
          :loading="loading"
          @select-city="selectCity"
        />
      </section>

      <section id="results" class="section-card results-section" aria-live="polite" :aria-busy="loading">
        <div class="section-heading results-heading">
          <div>
            <span class="section-index">03 · Рекомендации</span>
            <h2>{{ resultHeading }}</h2>
            <p v-if="!submitted">Заполните параметры или запустите готовый демо-сценарий.</p>
          </div>
          <span v-if="result?.status === 'matched'" class="result-count">
            показано {{ result.items.length }} из {{ result.meta.eligible_count }}
          </span>
        </div>

        <div v-if="submitted" class="query-summary">
          <span><MapPin :size="13" /> {{ submitted.city }}</span>
          <span><CalendarDays :size="13" /> {{ humanDate(submitted.event_date) }}</span>
          <span>{{ submitted.category }}</span>
          <span>{{ submitted.event_format }}</span>
          <span>до {{ money(submitted.budget_kzt) }} ₸</span>
          <span v-if="submitted.language">{{ submitted.language }}</span>
          <span v-if="submitted.duration_hours">{{ submitted.duration_hours }} ч</span>
        </div>

        <template v-if="loading">
          <div class="analysis-line">
            <LoaderCircle class="spin" :size="18" />
            <span><strong>Фильтруем кандидатов</strong> по занятости, бюджету, формату, языку и длительности</span>
          </div>
          <div class="cards-grid">
            <div v-for="index in 3" :key="index" class="skeleton-card"><span /><span /><span /><span /></div>
          </div>
        </template>

        <div v-else-if="error" class="empty-state error-state" role="alert">
          <span class="empty-icon"><CircleAlert :size="27" /></span>
          <h3>Не удалось получить подборку</h3>
          <p>{{ error }}</p>
          <Button v-if="submitted" variant="outline" @click="search(submitted)"><RefreshCw :size="16" /> Повторить</Button>
        </div>

        <template v-else-if="result?.status === 'matched'">
          <div class="outcome-banner outcome-banner--success">
            <span><ShieldCheck :size="18" /></span>
            <p>{{ result.message }}</p>
          </div>
          <div class="cards-grid">
            <ContractorCard
              v-for="(contractor, index) in result.items.slice(0, 3)"
              :key="contractor.id"
              :contractor="contractor"
              :index="index"
              @open="openContractor(contractor, index)"
            />
          </div>
          <div class="date-comparison">
            <div>
              <CalendarDays :size="18" />
              <span><strong>Проверить влияние занятости</strong>Сравните тот же запрос на другой дате.</span>
            </div>
            <Button variant="outline" @click="compareDate">
              {{ submitted?.event_date === '2026-11-14' ? 'Вернуть 10 октября' : 'Сравнить с 14 ноября' }}
            </Button>
          </div>
        </template>

        <div v-else-if="result" class="empty-state">
          <span class="empty-icon"><Search :size="27" /></span>
          <span class="outcome-label">
            {{ result.status === 'category_not_found' ? 'Категории нет' : 'Условия не пройдены' }}
          </span>
          <h3>{{ resultHeading }}</h3>
          <p>{{ result.message }}</p>
          <div v-if="exclusions.length" class="exclusion-grid">
            <span v-for="[key, count] in exclusions" :key="key">
              {{ exclusionLabels[key] }} <b>{{ count }}</b>
            </span>
          </div>
          <small>
            {{ result.status === 'category_not_found'
              ? 'Выберите другой город или категорию.'
              : 'Измените дату, бюджет, формат или дополнительные условия.' }}
          </small>
        </div>

        <div v-else class="welcome-state">
          <div class="welcome-orbit"><Target :size="31" /></div>
          <h3>Короткая подборка вместо длинного каталога</h3>
          <p>Backend вернёт не больше трёх свободных подрядчиков. Порядок стабилен, а объяснения основаны на фактах профиля.</p>
          <div class="welcome-rules">
            <span><ShieldCheck :size="16" /> занятые исключаются</span>
            <span><Gauge :size="16" /> ответ до 10 секунд</span>
            <span><Database :size="16" /> данные из API</span>
          </div>
        </div>
      </section>

    </main>

    <footer class="site-footer">
      <a href="#" class="product-brand"><span class="brand-mark"><Compass :size="17" /></span><span>точка события</span></a>
      <span>Хакатон #79-lite · 66 анонимных профилей</span>
      <span>Календарь 23.09—31.12.2026</span>
    </footer>

    <ContractorDetail
      v-if="selectedContractor"
      :contractor="selectedContractor"
      :request="submitted"
      :rank="selectedRank"
      @close="selectedContractor = null"
    />
  </div>
</template>
