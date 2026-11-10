import { describe, expect, it } from 'vitest'
import { ALL_CUSTOMERS, groupColor, mergeCurves, monthTicks, visibleCurves } from './survival'

const curve = (group, points) => ({
  group,
  points: points.map(([month, survival]) => ({ month, survival })),
})

describe('mergeCurves', () => {
  it('lines the groups up by month and stops a shorter curve with null', () => {
    const rows = mergeCurves([
      curve('A', [[0, 1], [1, 0.9], [2, 0]]),
      curve('B', [[0, 1], [1, 0.5]]),
    ])
    expect(rows).toEqual([
      { month: 0, A: 1, B: 1 },
      { month: 1, A: 0.9, B: 0.5 },
      { month: 2, A: 0, B: null }, 
    ])
  })

  it('combines different month grids in order', () => {
    const rows = mergeCurves([curve('A', [[0, 1], [12, 0.8]]), curve('B', [[0, 1], [6, 0.9]])])
    expect(rows.map((row) => row.month)).toEqual([0, 6, 12])
    expect(rows[1]).toEqual({ month: 6, A: null, B: 0.9 })
  })

  it('returns nothing for no curves', () => {
    expect(mergeCurves([])).toEqual([])
  })
})

describe('monthTicks', () => {
  it('marks every twelve months', () => {
    expect(monthTicks(72)).toEqual([0, 12, 24, 36, 48, 60, 72])
    expect(monthTicks(50)).toEqual([0, 12, 24, 36, 48])
    expect(monthTicks(0)).toEqual([0])
  })
})

describe('visibleCurves', () => {
  const curves = [ALL_CUSTOMERS, 'Month-to-month', 'One year'].map((group) => curve(group, [[0, 1]]))

  it('shows everything when no contract is selected', () => {
    expect(visibleCurves(curves, '')).toHaveLength(3)
  })

  it('keeps the overall curve and the selected contract', () => {
    expect(visibleCurves(curves, 'One year').map((c) => c.group)).toEqual([ALL_CUSTOMERS, 'One year'])
  })

  it('falls back to the overall curve for an unknown contract', () => {
    expect(visibleCurves(curves, 'Weekly').map((c) => c.group)).toEqual([ALL_CUSTOMERS])
  })
})

describe('groupColor', () => {
  it('uses fixed colours for known groups and cycles through spares for others', () => {
    expect(groupColor('One year', 0)).toBe('#1d4ed8')
    expect(groupColor('Mystery', 0)).toBe('#7c3aed')
    expect(groupColor('Mystery', 1)).toBe('#be185d')
    expect(groupColor('Mystery', 3)).toBe('#7c3aed')
  })
})