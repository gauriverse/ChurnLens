import { describe, expect, it } from 'vitest'
import { EMPTY, formatMoney, formatPercent, formatValue } from './format'

describe('formatValue', () => {
  it('formats each unit', () => {
    expect(formatValue(7043, 'customers')).toBe('7,043')
    expect(formatValue(0.26537, 'share')).toBe('26.5%')
    expect(formatValue(1682239.4, 'currency')).toBe('$1,682,239')
    expect(formatValue(55.64, 'months')).toBe('55.6 months')
  })

  it('shows a dash when a value is missing', () => {
    for (const unit of ['customers', 'share', 'currency', 'months']) {
      expect(formatValue(null, unit)).toBe(EMPTY)
    }
    expect(formatValue(undefined, 'share')).toBe(EMPTY)
  })

  it('falls back to plain text for an unknown unit', () => {
    expect(formatValue(5, 'widgets')).toBe('5')
  })
})

describe('formatPercent', () => {
  it('uses the precision you ask for', () => {
    expect(formatPercent(0.4271)).toBe('42.7%')
    expect(formatPercent(0.4271, 0)).toBe('43%')
    expect(formatPercent(0, 1)).toBe('0.0%')
  })
})

describe('formatMoney', () => {
  it('always shows cents', () => {
    expect(formatMoney(29.85)).toBe('$29.85')
    expect(formatMoney(105)).toBe('$105.00')
    expect(formatMoney(null)).toBe(EMPTY)
  })
})