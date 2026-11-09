import { describe, expect, it } from 'vitest'
import { apiPath, describeError } from './client'

const failure = (status, data) => ({ response: { status, data } })

describe('describeError', () => {
  it('ignores requests we cancelled ourselves', () => {
    expect(describeError({ code: 'ERR_CANCELED' })).toBeNull()
  })

  it('explains a timeout', () => {
    expect(describeError({ code: 'ECONNABORTED' })).toContain('too long')
  })

  it('explains an unreachable server', () => {
    expect(describeError({ message: 'Network Error' })).toContain('Cannot reach the server')
  })

  it('shows the API detail for a 404', () => {
    expect(describeError(failure(404, { detail: 'customer not found in this analysis run' }))).toBe(
      'customer not found in this analysis run',
    )
  })

  it('has a fallback for a 404 without detail', () => {
    expect(describeError(failure(404, {}))).toBe('Not found.')
  })

  it('shows the API detail for a 503 and has a fallback', () => {
    expect(describeError(failure(503, { detail: 'database temporarily unavailable, please retry' }))).toBe(
      'database temporarily unavailable, please retry',
    )
    expect(describeError(failure(503, {}))).toContain('temporarily unavailable')
  })

  it('joins a list of text messages', () => {
    expect(describeError(failure(422, { detail: ["Contract: 'Weekly' is not accepted", 'Another problem'] }))).toBe(
      "Contract: 'Weekly' is not accepted; Another problem",
    )
  })

  it('reads the msg field of FastAPI validation errors', () => {
    expect(describeError(failure(422, { detail: [{ msg: 'Field required' }, { msg: 'Input should be a number' }] }))).toBe(
      'Field required; Input should be a number',
    )
  })

  it('names the status for other server errors', () => {
    expect(describeError(failure(500, { detail: 'Internal Server Error' }))).toBe('Internal Server Error')
    expect(describeError(failure(500, null))).toContain('error 500')
  })
})

describe('apiPath', () => {
  it('adds the version prefix', () => {
    expect(apiPath('/insights')).toBe('/api/v1/insights')
  })
})