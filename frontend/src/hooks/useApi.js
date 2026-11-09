import { useCallback, useEffect, useState } from 'react'
import { api, describeError } from '../api/client'

export function useApi(path, params = null, { slowAfterMs = 5000 } = {}) {
  const paramsKey = JSON.stringify(params ?? null)
  const [reloadCount, setReloadCount] = useState(0)
  const requestKey = `${path}|${paramsKey}|${reloadCount}`

  const [result, setResult] = useState({ key: null, data: null, error: null })
  const [slowKey, setSlowKey] = useState(null)

  useEffect(() => {
    const controller = new AbortController()
    const timer = setTimeout(() => setSlowKey(requestKey), slowAfterMs)

    api
      .get(path, { params: JSON.parse(paramsKey) ?? undefined, signal: controller.signal })
      .then((response) => setResult({ key: requestKey, data: response.data, error: null }))
      .catch((error) => {
        const message = describeError(error)
        if (message) setResult({ key: requestKey, data: null, error: message })
      })
      .finally(() => clearTimeout(timer))

    return () => {
      controller.abort()
      clearTimeout(timer)
    }
  }, [path, paramsKey, requestKey, slowAfterMs])

  const reload = useCallback(() => setReloadCount((n) => n + 1), [])

  
  const loading = result.key !== requestKey
  return {
    data: loading ? null : result.data,
    error: loading ? null : result.error,
    loading,
    waking: loading && slowKey === requestKey,
    reload,
  }
}