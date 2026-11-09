import axios from 'axios'

const baseURL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

export const api = axios.create({
  baseURL,
  timeout: 90_000, 
})

export const apiPath = (path) => `/api/v1${path}`

function readDetail(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const parts = detail.map((item) => (typeof item === 'string' ? item : item?.msg)).filter(Boolean)
    return parts.length ? parts.join('; ') : null
  }
  return null
}


export function describeError(error) {
  if (error?.code === 'ERR_CANCELED') return null
  if (error?.code === 'ECONNABORTED') {
    return 'The server took too long to answer. It may still be waking up, so try again in a moment.'
  }
  if (!error?.response) {
    return 'Cannot reach the server. Check your connection and the API address in .env.local.'
  }
  const { status, data } = error.response
  const detail = readDetail(data?.detail)
  if (detail) return detail
  if (status === 503) return 'The service is temporarily unavailable. Please try again in a few seconds.'
  if (status === 404) return 'Not found.'
  return `Something went wrong on the server (error ${status}).`
}