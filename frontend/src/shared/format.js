/**
 * Format a byte count as a human-readable size string.
 * @param {number|null|undefined} bytes
 * @returns {string}
 */
export function formatSize(bytes) {
  if (!bytes) return ''
  const mb = bytes / (1024 * 1024)
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(0)} KB`
}
