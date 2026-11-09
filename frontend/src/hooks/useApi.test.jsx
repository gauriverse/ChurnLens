import { act, renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '../api/client'
import { useApi } from './useApi'

vi.mock('../api/client', async (importOriginal) => {
  const actual = await importOriginal()
  return { ...actual, api: { get: vi.fn() } }
})

beforeEach(() => api.get.mockReset())

describe('useApi', () => {
  it('starts loading, then returns the data', async () => {
    api.get.mockResolvedValue({ data: { total: 7043 } })
    const { result } = renderHook(() => useApi('/x'))
    expect(result.current.loading).toBe(true)
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.data).toEqual({ total: 7043 })
    expect(result.current.error).toBeNull()
  })

  it('turns a failed request into a readable message', async () => {
    api.get.mockRejectedValue({
      response: { status: 503, data: { detail: 'database temporarily unavailable, please retry' } },
    })
    const { result } = renderHook(() => useApi('/x'))
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('database temporarily unavailable, please retry')
    expect(result.current.data).toBeNull()
  })

  it('fetches again when reload is called', async () => {
    api.get.mockResolvedValueOnce({ data: 1 }).mockResolvedValueOnce({ data: 2 })
    const { result } = renderHook(() => useApi('/x'))
    await waitFor(() => expect(result.current.data).toBe(1))
    act(() => result.current.reload())
    await waitFor(() => expect(result.current.data).toBe(2))
    expect(api.get).toHaveBeenCalledTimes(2)
  })
})