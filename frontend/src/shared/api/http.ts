interface FetchOptions extends RequestInit {
  skipContentType?: boolean
}

export async function apiFetch<T = unknown>(url: string, options: FetchOptions = {}): Promise<T> {
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) }

  if (!options.skipContentType) {
    headers['Content-Type'] = 'application/json'
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })
  if (!response.ok) throw new Error(`API error: ${response.status}`)
  if (response.status === 204) return null as T
  return response.json() as Promise<T>
}
