<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'
const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>
<template><span :class="cn('inline-flex items-center rounded-md border border-border px-2 py-1 text-xs font-medium', props.class)"><slot /></span></template>