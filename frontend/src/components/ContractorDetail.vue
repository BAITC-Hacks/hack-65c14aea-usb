<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  Languages,
  MapPin,
  Sparkles,
  WalletCards,
  X,
} from 'lucide-vue-next'

import type { Contractor, RecommendationRequest } from '@/types/api'

const props = defineProps<{
  contractor: Contractor
  request: RecommendationRequest | null
  rank: number
}>()

const emit = defineEmits<{ close: [] }>()
const closeButton = ref<HTMLButtonElement | null>(null)

const money = new Intl.NumberFormat('ru-RU')
const price = computed(() => `${money.format(props.contractor.price_from_kzt)} ₸`)
const budget = computed(() => props.request ? `${money.format(props.request.budget_kzt)} ₸` : 'Не указан')
const eventDate = computed(() => {
  if (!props.request) return ''
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
    .format(new Date(`${props.request.event_date}T00:00:00`))
})

function close() {
  emit('close')
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') close()
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  document.body.style.overflow = 'hidden'
  closeButton.value?.focus()
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <div class="profile-overlay" @click.self="close">
      <aside
        class="profile-drawer"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="`profile-title-${contractor.id}`"
      >
        <header class="profile-header">
          <div class="profile-toolbar">
            <span>Рекомендация 0{{ rank }}</span>
            <button ref="closeButton" type="button" aria-label="Закрыть профиль" @click="close">
              <X :size="20" />
            </button>
          </div>

          <div class="profile-avatar">
            {{ contractor.name.split(' ').map(part => part[0]).slice(0, 2).join('') }}
          </div>
          <p>{{ contractor.categories.join(' · ') }}</p>
          <h2 :id="`profile-title-${contractor.id}`">{{ contractor.name }}</h2>
          <span class="profile-id">{{ contractor.id }}</span>

          <div class="profile-source" :class="{ synthetic: contractor.synthetic }">
            <Sparkles v-if="contractor.synthetic" :size="13" />
            <CheckCircle2 v-else :size="13" />
            {{ contractor.synthetic ? 'Синтетический профиль' : 'Профиль из датасета' }}
          </div>
        </header>

        <div class="profile-body">
          <section class="profile-reason">
            <span><CheckCircle2 :size="18" /> Почему этот профиль в подборке</span>
            <p>{{ contractor.explanation }}</p>
          </section>

          <div class="profile-facts">
            <div>
              <MapPin :size="18" />
              <span>Город</span>
              <strong>{{ contractor.city }}</strong>
            </div>
            <div>
              <WalletCards :size="18" />
              <span>Стоимость от</span>
              <strong>{{ price }}</strong>
            </div>
            <div>
              <Sparkles :size="18" />
              <span>Категория</span>
              <strong>{{ contractor.categories.join(', ') }}</strong>
            </div>
            <div>
              <CheckCircle2 :size="18" />
              <span>Источник</span>
              <strong>{{ contractor.synthetic ? 'Синтетические данные' : 'Основной датасет' }}</strong>
            </div>
          </div>

          <section v-if="request" class="profile-request">
            <h3>Параметры этого подбора</h3>
            <div>
              <span><CalendarDays :size="15" /> {{ eventDate }}</span>
              <span><WalletCards :size="15" /> бюджет до {{ budget }}</span>
              <span>{{ request.event_format }}</span>
              <span v-if="request.language"><Languages :size="15" /> {{ request.language }}</span>
              <span v-if="request.duration_hours"><Clock3 :size="15" /> {{ request.duration_hours }} ч</span>
            </div>
          </section>

          <p class="profile-note">
            Профиль показан как рекомендация. Бронирование и отправка заявок не входят в задачу сервиса.
          </p>

          <button type="button" class="profile-back" @click="close">Вернуться к подборке</button>
        </div>
      </aside>
    </div>
  </Teleport>
</template>
