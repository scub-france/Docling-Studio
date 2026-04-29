<template>
  <ComingSoonShell
    :title="t('comingSoon.title')"
    :subtitle="t('comingSoon.subtitle.docWorkspace')"
    :hint="hint"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../shared/i18n'

import { type DocMode } from '../shared/routing/modes'
import ComingSoonShell from '../shared/ui/ComingSoonShell.vue'

/**
 * Doc workspace placeholder. Receives the doc id (from `:id` path param)
 * and the resolved mode (from `?mode=` query param, parsed by the
 * router via `parseMode`). The full workspace is built by #216 (E4)
 * on top of #218-#224 (E5 chunks editor).
 */
const props = defineProps<{ id: string; mode: DocMode }>()

const { t } = useI18n()

const hint = computed(() => t('comingSoon.hint.docWorkspace', { id: props.id, mode: props.mode }))
</script>
