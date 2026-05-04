<template>
  <component
    :is="component"
    v-model="config"
    :show-error="showError"
    @valid="(v: boolean) => emit('valid', v)"
  />
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import OpenSearchConfigForm from './OpenSearchConfigForm.vue'
import Neo4jConfigForm from './Neo4jConfigForm.vue'

const props = defineProps<{
  kind: string
  modelValue: Record<string, unknown>
  showError?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, unknown>): void
  (e: 'valid', value: boolean): void
}>()

const config = ref({ ...props.modelValue })

watch(config, (next) => emit('update:modelValue', next), { deep: true })
watch(
  () => props.modelValue,
  (next) => {
    config.value = { ...next }
  },
  { deep: true },
)

const component = computed(() => {
  switch (props.kind) {
    case 'opensearch':
      return OpenSearchConfigForm
    case 'neo4j':
      return Neo4jConfigForm
    default:
      return OpenSearchConfigForm
  }
})
</script>
