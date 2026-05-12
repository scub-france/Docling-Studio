/**
 * Doc workspace mode parsing.
 *
 * The doc workspace at `/docs/:id` exposes its content via the `?mode=`
 * query param. Anything missing or unknown resolves to the default,
 * `parse`, so a malformed URL never produces a broken page.
 *
 * #210 layers feature-flag-aware redirection on top: if the requested
 * mode is disabled for the current tenant, the router replaces it with
 * the first enabled mode (priority `parse` > `chunk`).
 *
 * Naming history:
 *   - #263 renamed the legacy `chunks` mode to `linked` and dropped
 *     `ask` from the workspace.
 *   - #264 reshuffled the two views: `parse` shows the Docling
 *     extraction graph (Structure tree + bboxes), `chunk` shows the
 *     chunk-centric editor. The Compare view (#270) is rendered as a
 *     disabled button in the switcher — no mode value, no route segment.
 *
 * Backward compatibility: `?mode=chunks`, `?mode=linked`, and
 * `?mode=inspect` are accepted and silently mapped to their current
 * equivalents so existing bookmarks keep working.
 */

export type DocMode = 'parse' | 'chunk'

export const DEFAULT_MODE: DocMode = 'parse'
export const ALL_MODES: readonly DocMode[] = ['parse', 'chunk'] as const

const LEGACY_ALIASES: Readonly<Record<string, DocMode>> = {
  // Pre-#264 names. `linked` mapped to the chunks-aligned preview, which
  // is now `chunk`. `inspect` was the old Markdown/Elements/Images tab,
  // which is now subsumed by `parse` (Docling extraction graph).
  linked: 'chunk',
  chunks: 'chunk',
  inspect: 'parse',
}

export function isDocMode(value: unknown): value is DocMode {
  return value === 'parse' || value === 'chunk'
}

export function parseMode(raw: unknown): DocMode {
  if (typeof raw === 'string' && raw in LEGACY_ALIASES) {
    return LEGACY_ALIASES[raw]
  }
  return isDocMode(raw) ? raw : DEFAULT_MODE
}
