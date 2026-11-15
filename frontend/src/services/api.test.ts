import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from './api'

afterEach(() => vi.unstubAllGlobals())

describe('api client', () => {
  it('attaches the analyst access token to requests', async () => {
    vi.stubGlobal('localStorage', { getItem: () => 'test-token' })
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) =>
      new Response(JSON.stringify({ status: 'ok' }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(api<{ status: string }>('/health')).resolves.toEqual({ status: 'ok' })
    const options = fetchMock.mock.calls[0][1]
    expect(new Headers(options?.headers).get('Authorization')).toBe('Bearer test-token')
  })

  it('surfaces API authorization errors instead of hiding them', async () => {
    vi.stubGlobal('localStorage', { getItem: () => null })
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ detail: 'Analyst access required' }), {
      status: 403,
      headers: { 'Content-Type': 'application/json' },
    })))

    await expect(api('/entities')).rejects.toThrow('Analyst access required')
  })
})
