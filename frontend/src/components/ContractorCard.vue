<script setup lang="ts">
import { BadgeCheck, CircleCheck, MapPin, Sparkles, WalletCards } from 'lucide-vue-next'
import type { Contractor } from '@/types/api'

defineProps<{ contractor: Contractor; index: number }>()

const money = (value: number) => new Intl.NumberFormat('ru-RU').format(value)
</script>

<template>
  <article class="contractor-card">
    <div class="card-header">
      <span class="rank">0{{ index + 1 }}</span>
      <span v-if="contractor.synthetic" class="source-badge source-badge--synthetic">
        <Sparkles :size="12" /> Синтетический профиль
      </span>
      <span v-else class="source-badge">
        <BadgeCheck :size="13" /> Профиль датасета
      </span>
    </div>

    <div class="identity">
      <span class="avatar">{{ contractor.name.split(' ').map(part => part[0]).slice(0, 2).join('') }}</span>
      <div>
        <p class="categories">{{ contractor.categories.join(' · ') }}</p>
        <h3>{{ contractor.name }}</h3>
        <p class="location"><MapPin :size="13" /> {{ contractor.city }} <span>· {{ contractor.id }}</span></p>
      </div>
    </div>

    <div class="price-row">
      <span><WalletCards :size="15" /> Стоимость от</span>
      <strong>{{ money(contractor.price_from_kzt) }} ₸</strong>
    </div>

    <div class="explanation">
      <span><CircleCheck :size="16" /> Почему этот профиль здесь</span>
      <p>{{ contractor.explanation }}</p>
    </div>
  </article>
</template>

<style scoped>
.contractor-card {
  display: flex;
  min-width: 0;
  height: 100%;
  flex-direction: column;
  padding: 22px;
  border: 1px solid #dfe4ec;
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 14px 38px rgb(26 36 62 / 5%);
  transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
}

.contractor-card:hover {
  border-color: #cbd3e1;
  box-shadow: 0 20px 48px rgb(26 36 62 / 9%);
  transform: translateY(-3px);
}

.card-header {
  display: flex;
  min-height: 29px;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.rank {
  color: #8a94a7;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .12em;
}

.source-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 8px;
  border-radius: 999px;
  color: #55705f;
  font-size: 9px;
  font-weight: 700;
  background: #edf6f0;
}

.source-badge--synthetic {
  color: #765d24;
  background: #fbf3df;
}

.identity {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 13px;
  align-items: center;
  margin-top: 18px;
}

.avatar {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  border-radius: 15px;
  color: #fff;
  font-size: 14px;
  font-weight: 800;
  background: linear-gradient(145deg, #263452, #445675);
}

.categories {
  overflow: hidden;
  margin: 0 0 4px;
  color: #78849a;
  font-size: 9px;
  font-weight: 750;
  letter-spacing: .07em;
  text-overflow: ellipsis;
  text-transform: uppercase;
  white-space: nowrap;
}

h3 {
  margin: 0;
  color: #16213a;
  font-size: 18px;
  line-height: 1.2;
  letter-spacing: -.025em;
}

.location {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  margin: 6px 0 0;
  color: #7c879a;
  font-size: 10px;
}

.location span { color: #a1a9b7; }

.price-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 20px;
  padding: 13px 0;
  border-top: 1px solid #edf0f4;
  border-bottom: 1px solid #edf0f4;
}

.price-row span {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #7c879a;
  font-size: 10px;
}

.price-row strong {
  color: #16213a;
  font-size: 16px;
  white-space: nowrap;
}

.explanation {
  flex: 1;
  margin-top: 14px;
  padding: 15px;
  border: 1px solid #dfe8e4;
  border-radius: 14px;
  background: #f4f8f6;
}

.explanation > span {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #356656;
  font-size: 10px;
  font-weight: 800;
}

.explanation p {
  margin: 8px 0 0;
  color: #52645e;
  font-size: 11px;
  line-height: 1.62;
  white-space: pre-line;
}

@media (prefers-reduced-motion: reduce) {
  .contractor-card { transition: none; }
}
</style>
