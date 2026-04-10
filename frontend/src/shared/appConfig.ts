import { ref } from 'vue'
import type { Locale } from './types'

/**
 * App-wide reactive configuration — populated by feature stores,
 * consumed by shared utilities and other features.
 * Breaks the dependency cycle between features and shared.
 */
export const appLocale = ref<Locale>('fr')
export const appMaxFileSizeMb = ref<number>(0)
export const appMaxPageCount = ref<number>(0)
