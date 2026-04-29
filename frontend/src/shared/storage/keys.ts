/**
 * Centralised localStorage keys.
 *
 * Every key the frontend writes to `localStorage` lives here so we have a
 * single place to audit naming, namespace collisions, or migrations. All
 * keys share the `docling-` prefix to avoid clashing with other apps that
 * might be served from the same origin (e.g. on Hugging Face Spaces).
 */
export const STORAGE_KEYS = {
  theme: 'docling-theme',
  locale: 'docling-locale',
} as const

export type StorageKey = (typeof STORAGE_KEYS)[keyof typeof STORAGE_KEYS]
