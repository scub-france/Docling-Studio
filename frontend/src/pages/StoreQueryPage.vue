<template>
  <ComingSoonShell
    :title="t('comingSoon.title')"
    :subtitle="t('comingSoon.subtitle.storeQuery')"
    :hint="hint"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../shared/i18n'

import ComingSoonShell from '../shared/ui/ComingSoonShell.vue'

const props = defineProps<{ store: string }>()

const { t } = useI18n()

const hint = computed(() => t('comingSoon.hint.storeQuery', { store: props.store }))
</script>
