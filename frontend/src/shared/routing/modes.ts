/**
 * Doc workspace mode parsing.
 *
 * The doc workspace at `/docs/:id` exposes three modes via the `?mode=`
 * query param. Anything missing or unknown resolves to the default,
 * `ask`, so a malformed URL never produces a broken page.
 *
 * #210 layers feature-flag-aware redirection on top: if the requested
 * mode is disabled for the current tenant, the router replaces it with
 * the first enabled mode (priority `ask` > `chunks` > `inspect`).
 */

export type DocMode = 'ask' | 'inspect' | 'chunks'

export const DEFAULT_MODE: DocMode = 'ask'
export const ALL_MODES: readonly DocMode[] = ['ask', 'inspect', 'chunks'] as const

export function isDocMode(value: unknown): value is DocMode {
  return value === 'ask' || value === 'inspect' || value === 'chunks'
}

export function parseMode(raw: unknown): DocMode {
  return isDocMode(raw) ? raw : DEFAULT_MODE
}
