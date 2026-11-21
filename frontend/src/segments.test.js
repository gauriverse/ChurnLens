import { describe, expect, it } from 'vitest'
import { concentrationRows, historicalShare, segmentTotals, topSegmentSummary } from './segments'
import { SEGMENTS } from './test/segmentsFixture'

describe('segmentTotals', () => {
  it('adds up customers and revenue at risk', () => {
    const totals = segmentTotals(SEGMENTS.segments)
    expect(totals.customers).toBe(7043)
    expect(totals.revenueAtRisk).toBeCloseTo(1682240.06, 2)
  })

  it('starts from zero', () => {
    expect(segmentTotals([])).toEqual({ customers: 0, revenueAtRisk: 0 })
  })
})

describe('concentrationRows', () => {
  it('puts the share of customers next to the share of revenue at risk', () => {
    const rows = concentrationRows(SEGMENTS.segments)
    expect(rows).toHaveLength(5)
    expect(rows[0]).toEqual({ label: 'Newer fiber, month-to-month', customers: 0.2743, revenue: 0.6654 })
  })
})

describe('topSegmentSummary', () => {
  it('names the segment with the largest share of revenue at risk, whatever the order', () => {
    const expected = 'Newer fiber, month-to-month: 27% of customers, 67% of the revenue at risk.'
    expect(topSegmentSummary(SEGMENTS.segments)).toBe(expected)
    expect(topSegmentSummary([...SEGMENTS.segments].reverse())).toBe(expected)
  })

  it('returns nothing when there are no segments', () => {
    expect(topSegmentSummary([])).toBeNull()
  })
})

describe('historicalShare', () => {
  it('reads the stored historical share and tolerates missing characteristics', () => {
    expect(historicalShare(SEGMENTS.segments[0])).toBe(0.666)
    expect(historicalShare({ ...SEGMENTS.segments[0], characteristics: null })).toBeNull()
  })
})