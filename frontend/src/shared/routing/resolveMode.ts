import { type DocMode } from './modes'

/**
 * Doc workspace mode resolution under feature flags (#210, updated #263,
 * #264, #225).
 *
 * The router consults this when a user opens `/docs/:id?mode=<mode>`:
 *
 *   - If the requested mode is enabled, return it.
 *   - Otherwise, return the first enabled mode in `MODE_PRIORITY`.
 *   - If no mode is enabled, return `null` (the router redirects to
 *     the docs library with a flash message).
 *
 * Priority: `parse` first (extraction is the natural landing for a
 * freshly parsed doc), then `chunk`, then `ingest`.
 */
export const MODE_PRIORITY: readonly DocMode[] = ['parse', 'chunk', 'ingest'] as const

export function resolveMode(
  requested: DocMode | undefined,
  enabled: Record<DocMode, boolean>,
): DocMode | null {
  if (requested && enabled[requested]) return requested
  return MODE_PRIORITY.find((m) => enabled[m]) ?? null
}
