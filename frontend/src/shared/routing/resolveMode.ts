import { type DocMode } from './modes'

/**
 * Doc workspace mode resolution under feature flags (#210, updated #263, #264).
 *
 * The router consults this when a user opens `/docs/:id?mode=<mode>`:
 *
 *   - If the requested mode is enabled, return it.
 *   - Otherwise, return the first enabled mode in `MODE_PRIORITY`.
 *   - If no mode is enabled, return `null` (the router redirects to
 *     the docs library with a flash message).
 *
 * Priority: `parse` first (the extraction view is the natural landing
 * for a freshly parsed doc), then `chunk`.
 */
export const MODE_PRIORITY: readonly DocMode[] = ['parse', 'chunk'] as const

export function resolveMode(
  requested: DocMode | undefined,
  enabled: Record<DocMode, boolean>,
): DocMode | null {
  if (requested && enabled[requested]) return requested
  return MODE_PRIORITY.find((m) => enabled[m]) ?? null
}
