<script setup lang="ts">
import { MapPin, Check, Sparkles, ArrowUpRight } from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import type { Contractor } from '@/types/api'
defineProps<{ contractor: Contractor; index: number }>()
const money = (value: number) => new Intl.NumberFormat('ru-RU').format(value)
</script>
<template>
 <article class="contractor-card">
  <div class="card-top"><span class="profile-avatar">{{ contractor.name.split(' ').map(s => s[0]).slice(0, 2).join('') }}</span><span class="match-index">0{{ index + 1 }} <ArrowUpRight :size="16" /></span></div>
  <div class="categories">{{ contractor.categories.join(' · ') }}</div>
  <h3>{{ contractor.name }}</h3>
  <p class="location"><MapPin :size="14" />{{ contractor.city }} <span>· {{ contractor.id }}</span></p>
  <Badge v-if="contractor.synthetic" class="synthetic"><Sparkles :size="12" /> Синтетический профиль</Badge>
  <div class="price"><span>Стоимость от</span><strong>{{ money(contractor.price_from_kzt) }} <small>₸</small></strong></div>
  <div class="explanation"><span><Check :size="16" /> Почему подходит</span><p>{{ contractor.explanation }}</p></div>
 </article>
</template>