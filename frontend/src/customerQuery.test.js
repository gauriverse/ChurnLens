import { describe, expect, it } from 'vitest'
import {
  nextSort, pageCount, pageRange, readQuery, toApiParams, toSearchParams,
} from './customerQuery'

const read = (text) => readQuery(new URLSearchParams(text))
const DEFAULTS = { search: '', contract: '', risk: '', sort: 'churn_probability', order: 'desc', page: 1 }

describe('readQuery', () => {
  it('uses the defaults for an empty address', () => {
    expect(read('')).toEqual(DEFAULTS)
  })

  it('reads valid values', () => {
    expect(read('search=7590&contract=One%20year&risk=High&sort=tenure&order=asc&page=3')).toEqual({
      search: '7590', contract: 'One year', risk: 'High', sort: 'tenure', order: 'asc', page: 3,
    })
  })

  it('ignores unknown or unsafe values', () => {
    expect(read('contract=Weekly&risk=Extreme&sort=password&order=sideways&page=-4')).toEqual(DEFAULTS)
    expect(read('sort=constructor').sort).toBe('churn_probability')
  })

  it('keeps the page within sensible bounds', () => {
    expect(read('page=abc').page).toBe(1)
    expect(read('page=0').page).toBe(1)
    expect(read('page=99999999999999999999').page).toBe(100000)
  })

  it('trims and limits the search text', () => {
    expect(read('search=%20%207590%20%20').search).toBe('7590')
    expect(read(`search=${'x'.repeat(150)}`).search).toHaveLength(100)
  })
})

describe('toSearchParams', () => {
  it('leaves out the defaults', () => {
    expect(toSearchParams(DEFAULTS)).toEqual({})
  })

  it('includes everything that differs from the defaults', () => {
    expect(
      toSearchParams({ search: '7590', contract: 'One year', risk: 'High', sort: 'tenure', order: 'asc', page: 3 }),
    ).toEqual({ search: '7590', contract: 'One year', risk: 'High', sort: 'tenure', order: 'asc', page: '3' })
  })
})

describe('toApiParams', () => {
  it('always sends sorting and paging', () => {
    expect(toApiParams(DEFAULTS)).toEqual({ sort_by: 'churn_probability', order: 'desc', page: 1, page_size: 25 })
  })

  it('adds the filters that are set', () => {
    expect(toApiParams({ ...DEFAULTS, search: '75', contract: 'Two year', risk: 'Low', sort: 'tenure', page: 2 })).toEqual({
      sort_by: 'tenure', order: 'desc', page: 2, page_size: 25, search: '75', contract: 'Two year', risk: 'Low',
    })
  })
})

describe('nextSort', () => {
  it('reverses the order when the same column is clicked again', () => {
    const first = nextSort({ ...DEFAULTS, page: 4 }, 'churn_probability')
    expect(first).toMatchObject({ sort: 'churn_probability', order: 'asc', page: 1 })
    expect(nextSort(first, 'churn_probability').order).toBe('desc')
  })

  it('starts a new column highest first and goes back to the first page', () => {
    expect(nextSort({ ...DEFAULTS, order: 'asc', page: 3 }, 'tenure')).toMatchObject({
      sort: 'tenure', order: 'desc', page: 1,
    })
  })
})

describe('paging arithmetic', () => {
  it('counts pages', () => {
    expect(pageCount(0)).toBe(1)
    expect(pageCount(25)).toBe(1)
    expect(pageCount(26)).toBe(2)
    expect(pageCount(7043)).toBe(282)
  })

  it('works out which rows are on the page', () => {
    expect(pageRange(1, 25)).toEqual({ from: 1, to: 25 })
    expect(pageRange(282, 18)).toEqual({ from: 7026, to: 7043 })
    expect(pageRange(3, 0)).toEqual({ from: 0, to: 0 })
  })
})