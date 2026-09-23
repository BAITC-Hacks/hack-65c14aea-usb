<script setup lang="ts">
import { computed } from 'vue'
import { MapPin, MousePointerClick, Navigation } from 'lucide-vue-next'

const props = defineProps<{
  cities: string[]
  selectedCity: string
  loading?: boolean
}>()

const emit = defineEmits<{ selectCity: [city: string] }>()

const coordinates: Record<string, { x: number; y: number; note: string }> = {
  Астана: { x: 56, y: 32, note: 'север и центр' },
  Алматы: { x: 72, y: 73, note: 'юго-восток' },
  Зарубежье: { x: 15, y: 66, note: 'выездные команды' },
}

const markers = computed(() =>
  props.cities
    .filter(city => coordinates[city])
    .map(city => ({ city, ...coordinates[city] })),
)
</script>

<template>
  <div class="kazakhstan-map">
    <div class="map-toolbar">
      <span><Navigation :size="15" /> География каталога</span>
      <span><MousePointerClick :size="14" /> Нажмите на город</span>
    </div>

    <div class="map-stage" aria-label="Интерактивная карта выбора города">
      <svg class="country-shape" viewBox="0 0 820 430" aria-hidden="true">
        <defs>
          <linearGradient id="mapFill" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#eef1f8" />
            <stop offset="1" stop-color="#e3e8f2" />
          </linearGradient>
          <filter id="mapShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="#26334d" flood-opacity=".08" />
          </filter>
        </defs>
        <path
          filter="url(#mapShadow)"
          fill="url(#mapFill)"
          stroke="#d3dae8"
          stroke-width="2"
          d="M169 91 229 65 293 78 345 62 408 82 464 72 514 99 575 95 604 123 674 132 700 163 746 183 733 218 689 235 676 268 622 279 599 315 544 329 503 353 454 340 405 365 349 342 309 356 269 330 220 324 202 291 157 275 137 242 95 219 111 184 86 153 121 126 133 101Z"
        />
        <path d="M210 126 278 108M314 119 361 94M477 112 532 126M164 217 222 224M366 281 414 329M579 180 650 169" stroke="#d8deea" stroke-width="2" stroke-linecap="round" />
        <circle cx="430" cy="206" r="96" fill="none" stroke="#d9deeb" stroke-dasharray="5 9" />
        <circle cx="430" cy="206" r="154" fill="none" stroke="#e2e6ef" stroke-dasharray="3 12" />
      </svg>

      <button
        v-for="marker in markers"
        :key="marker.city"
        type="button"
        class="city-marker"
        :class="{ active: marker.city === selectedCity }"
        :style="{ left: marker.x + '%', top: marker.y + '%' }"
        :disabled="loading"
        :aria-pressed="marker.city === selectedCity"
        :aria-label="`Выбрать город ${marker.city} и обновить подбор`"
        @click="emit('selectCity', marker.city)"
      >
        <span class="marker-pin"><MapPin :size="15" /></span>
        <span class="marker-copy">
          <strong>{{ marker.city }}</strong>
          <small>{{ marker.city === selectedCity ? 'выбран' : marker.note }}</small>
        </span>
      </button>
    </div>

    <div class="map-cities" aria-label="Доступные города">
      <button
        v-for="city in cities"
        :key="city"
        type="button"
        :class="{ active: city === selectedCity }"
        :disabled="loading"
        @click="emit('selectCity', city)"
      >
        <span />
        {{ city }}
      </button>
    </div>
  </div>
</template>
