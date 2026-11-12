import { act, renderHook, waitFor } from '@testing-library/react'
import { AxiosError } from 'axios'
import { afterEach, describe, expect, it } from 'vitest'
import { api } from '../api/client'
import { useApi } from './useApi'

const originalAdapter = api.defaults.adapter

afterEach(() => {
  api.defaults.adapter = originalAdapter
})

const succeedWith = (data) => async (config) => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: {},
  config,
})

const failWith = (status, data) => async (config) => {
  throw new AxiosError(
    `Request failed with status code ${status}`,
    'ERR_BAD_RESPONSE',
    config,
    null,
    { status, statusText: 'Error', headers: {}, config, data },
  )
}

function slowSecondRequest() {
  const control = { calls: 0, release: null }
  api.defaults.adapter = (config) => {
    control.calls += 1
    if (control.calls === 1) return succeedWith('first')(config)
    return new Promise((resolve) => {
      control.release = () =>
        resolve({ data: 'second', status: 200, statusText: 'OK', headers: {}, config })
    })
  }
  return control
}

describe('useApi', () => {
  it('starts loading, then returns the data', async () => {
    api.defaults.adapter = succeedWith({ total: 7043 })
    const { result } = renderHook(() => useApi('/x'))
    expect(result.current.loading).toBe(true)
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.data).toEqual({ total: 7043 })
    expect(result.current.error).toBeNull()
  })

  it('turns a failed request into a readable message', async () => {
    api.defaults.adapter = failWith(503, {
      detail: 'database temporarily unavailable, please retry',
    })
    const { result } = renderHook(() => useApi('/x'))
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('database temporarily unavailable, please retry')
    expect(result.current.data).toBeNull()
  })

  it('fetches again when reload is called', async () => {
    let calls = 0
    api.defaults.adapter = async (config) => {
      calls += 1
      return succeedWith(calls)(config)
    }
    const { result } = renderHook(() => useApi('/x'))
    await waitFor(() => expect(result.current.data).toBe(1))
    act(() => result.current.reload())
    await waitFor(() => expect(result.current.data).toBe(2))
    expect(calls).toBe(2)
  })

    it('keeps the previous data visible while the next request is pending when asked to', async () => {
    const control = slowSecondRequest()
    const { result } = renderHook(() => useApi('/x', null, { keepPrevious: true }))
    await waitFor(() => expect(result.current.data).toBe('first'))

    act(() => result.current.reload())
    expect(result.current.data).toBe('first')
    expect(result.current.loading).toBe(false)
    expect(result.current.refreshing).toBe(true)

    await waitFor(() => expect(control.release).not.toBeNull())
    await act(async () => control.release())
    await waitFor(() => expect(result.current.data).toBe('second'))
    expect(result.current.refreshing).toBe(false)
  })

  it('hides the old data while reloading by default', async () => {
    const control = slowSecondRequest()
    const { result } = renderHook(() => useApi('/x'))
    await waitFor(() => expect(result.current.data).toBe('first'))

    act(() => result.current.reload())
    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(true)
    expect(result.current.refreshing).toBe(false)

    await waitFor(() => expect(control.release).not.toBeNull())
    await act(async () => control.release())
    await waitFor(() => expect(result.current.data).toBe('second'))
  })
})