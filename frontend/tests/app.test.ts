// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import App from '../src/App.vue'
const options = { cities: ['Алматы', 'Астана', 'Зарубежье'], categories: ['Фотограф', 'Флорист'], event_formats: ['свадьба'], languages: ['русский'] }
const readiness = { status: 'ready', dependencies: { catalog: true, cache: true } }
const meta = { eligible_count: 2, total_in_city_category: 3, exclusions: { busy: 1, over_budget: 0, wrong_format: 0, wrong_language: 0, insufficient_duration: 0 } }
const items = [
 { id: 'z', name: 'Первый', categories: ['Фотограф'], city: 'Алматы', price_from_kzt: 100000, synthetic: true, explanation: 'Свободен на выбранную дату.' },
 { id: 'a', name: 'Второй', categories: ['Фотограф'], city: 'Алматы', price_from_kzt: 90000, synthetic: false, explanation: 'Подходит под бюджет.' },
]
const respond = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
let wrapper: ReturnType<typeof mount>
beforeEach(() => {
 vi.stubGlobal('fetch', vi.fn()
  .mockResolvedValueOnce(respond(options))
  .mockResolvedValueOnce(respond(readiness)))
})
afterEach(() => { wrapper?.unmount(); vi.unstubAllGlobals() })
async function start() { wrapper = mount(App); await flushPromises(); return wrapper }
describe('recommendations interface', () => {
 it('loads server options and sends the typed payload, preserving server order and synthetic labels', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(respond({ status: 'matched', items, meta, message: 'Найдено два профиля.' }))
  await start()
  await wrapper.get('form').trigger('submit')
  await flushPromises()
  expect(fetch).toHaveBeenNthCalledWith(1, '/api/v1/catalog/options', expect.any(Object))
  const request = vi.mocked(fetch).mock.calls[2]
  expect(request?.[0]).toBe('/api/v1/recommendations')
  expect(JSON.parse(request?.[1]?.body as string)).toEqual({ city: 'Алматы', category: 'Фотограф', event_format: 'свадьба', event_date: '2026-10-10', budget_kzt: 6000000 })
  expect(wrapper.findAll('.contractor-card h3').map(node => node.text())).toEqual(['Первый', 'Второй'])
  expect(wrapper.text()).toContain('Синтетический профиль')
 expect(wrapper.text()).toContain('Свободен на выбранную дату.')
 })
 it('opens a contractor profile, shows backend facts and closes with Escape', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(respond({ status: 'matched', items, meta, message: 'Найдено два профиля.' }))
  await start()
  await wrapper.get('form').trigger('submit')
  await flushPromises()
  await wrapper.get('.contractor-card').trigger('click')
  expect(document.body.textContent).toContain('Почему этот профиль в подборке')
  expect(document.body.textContent).toContain('Свободен на выбранную дату.')
  expect(document.body.textContent).toContain('Параметры этого подбора')
  expect(document.querySelector('#method')).toBeNull()
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
  await wrapper.vm.$nextTick()
  expect(document.querySelector('.profile-drawer')).toBeNull()
 })
 it('selects a city on the interactive map and sends it to the backend', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(respond({ status: 'matched', items, meta, message: 'Найдено.' }))
  await start()
  const astana = wrapper.findAll('.city-marker').find(marker => marker.text().includes('Астана'))
  expect(astana).toBeTruthy()
  await astana!.trigger('click')
  await flushPromises()
  const request = vi.mocked(fetch).mock.calls[2]
  expect(JSON.parse(request?.[1]?.body as string).city).toBe('Астана')
  expect((wrapper.get('#city').element as HTMLSelectElement).value).toBe('Астана')
 })
 it('runs the no-result Definition of Done scenario with real request parameters', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(respond({ status: 'no_eligible_candidates', items: [], meta, message: 'Бюджет не прошёл.' }))
  await start()
  const scenario = wrapper.findAll('.scenario-button').find(button => button.text().includes('Без результата'))
  expect(scenario).toBeTruthy()
  await scenario!.trigger('click')
  await flushPromises()
  const request = JSON.parse(vi.mocked(fetch).mock.calls[2]?.[1]?.body as string)
  expect(request).toEqual({ city: 'Алматы', event_date: '2026-10-10', event_format: 'свадьба', category: 'Фотограф', budget_kzt: 1 })
  expect(wrapper.text()).toContain('На эти условия пока нет совпадений')
 })
 it.each(['category_not_found', 'no_eligible_candidates'])('renders the %s business outcome', async status => {
  vi.mocked(fetch).mockResolvedValueOnce(respond({ status, items: [], meta, message: 'Нет подходящих профилей.' }))
  await start(); await wrapper.get('form').trigger('submit'); await flushPromises()
  expect(wrapper.text()).toContain(status === 'category_not_found' ? 'В этом городе пока нет такой категории' : 'На эти условия пока нет совпадений')
  expect(wrapper.findAll('.contractor-card')).toHaveLength(0)
 })
 it('keeps form values on failure and retries the submitted request', async () => {
  vi.mocked(fetch).mockRejectedValueOnce(new TypeError('network')).mockResolvedValueOnce(respond({ status: 'matched', items, meta, message: 'Найдено.' }))
  await start(); await wrapper.get('#budget').setValue('200000'); await wrapper.get('form').trigger('submit'); await flushPromises()
  expect(wrapper.text()).toContain('Не удалось связаться с сервером')
  expect((wrapper.get('#budget').element as HTMLInputElement).value).toBe('200000')
  await wrapper.get('.error-state button').trigger('click'); await flushPromises()
  expect(wrapper.findAll('.contractor-card')).toHaveLength(2)
 })
 it('does not send invalid budget, duration or dates', async () => {
  await start()
  for (const [selector, value] of [['#budget', '0'], ['#budget', '1.5'], ['#date', '2027-01-01'], ['#duration', '25']]) {
   await wrapper.get(selector!).setValue(value!)
   await wrapper.get('form').trigger('submit')
  }
  expect(fetch).toHaveBeenCalledTimes(2)
  expect(wrapper.find('[role="alert"]').exists()).toBe(true)
 })
 it('shows structured FastAPI validation errors', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(respond({ detail: [{ loc: ['body', 'event_date'], msg: 'Value error, date is outside the dataset window' }] }, 422))
  await start(); await wrapper.get('form').trigger('submit'); await flushPromises()
  expect(wrapper.text()).toContain('Проверьте параметры запроса')
  expect(wrapper.text()).toContain('date is outside the dataset window')
 })
 it('shows degraded mode when only the Redis cache is unavailable', async () => {
  vi.mocked(fetch).mockReset()
   .mockResolvedValueOnce(respond(options))
   .mockResolvedValueOnce(respond({ status: 'not_ready', dependencies: { catalog: true, cache: false } }, 503))
  await start()
  expect(wrapper.text()).toContain('Каталог доступен без кэша')
 })
 it('disables search when catalog options fail and offers a retry', async () => {
  vi.mocked(fetch).mockReset()
   .mockResolvedValueOnce(respond({ detail: 'Каталог временно недоступен.' }, 503))
   .mockResolvedValueOnce(respond({ status: 'not_ready', dependencies: { catalog: false, cache: true } }, 503))
   .mockResolvedValueOnce(respond(options))
  await start()
  expect(wrapper.text()).toContain('Каталог временно недоступен.')
  expect((wrapper.get('fieldset').element as HTMLFieldSetElement).disabled).toBe(true)
  await wrapper.get('.error-notice button').trigger('click'); await flushPromises()
  expect((wrapper.get('fieldset').element as HTMLFieldSetElement).disabled).toBe(false)
 })
})
