<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { Primitive, type PrimitiveProps } from 'reka-ui'
import { cva } from 'class-variance-authority'
import { cn } from '@/lib/utils'
const props = withDefaults(defineProps<PrimitiveProps & { variant?: 'default' | 'outline' | 'ghost'; class?: HTMLAttributes['class'] }>(), { as: 'button', variant: 'default' })
const variants = cva('inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 h-11 px-5', { variants: { variant: { default: 'bg-primary text-primary-foreground hover:bg-primary/90', outline: 'border border-input bg-background hover:bg-muted', ghost: 'hover:bg-muted text-muted-foreground' } }, defaultVariants: { variant: 'default' } })
</script>
<template><Primitive :as="as" :as-child="asChild" :class="cn(variants({ variant }), props.class)"><slot /></Primitive></template>