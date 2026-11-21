import { describe, expect, it } from 'vitest'
import {
  describeAssumptions, orderNotes, outcomeLabel, reasonBars, reasonCodeLabel, sentenceCase,
} from './profile'

describe('reasonBars', () => {
  it('scales bars to the largest contribution and puts raising effects on the right', () => {
    const bars = reasonBars([
      { rank: 1, contribution: 2, direction: 'raises' },
      { rank: 2, contribution: -1, direction: 'lowers' },
      { rank: 3, contribution: 0.5, direction: 'raises' },
    ])
    expect(bars).toEqual([
      { rank: 1, side: 'right', width: 50 },
      { rank: 2, side: 'left', width: 25 },
      { rank: 3, side: 'right', width: 12.5 },
    ])
  })

  it('handles no reasons and all-zero contributions', () => {
    expect(reasonBars([])).toEqual([])
    expect(reasonBars([{ rank: 1, contribution: 0, direction: 'raises' }])).toEqual([
      { rank: 1, side: 'right', width: 0 },
    ])
  })
})

describe('reasonCodeLabel', () => {
  it('translates known codes and shows unknown ones as they are', () => {
    expect(reasonCodeLabel('MONTH_TO_MONTH')).toBe('Month-to-month contract')
    expect(reasonCodeLabel('SOMETHING_NEW')).toBe('SOMETHING_NEW')
    expect(reasonCodeLabel('constructor')).toBe('constructor')
  })
})

describe('describeAssumptions', () => {
  it('lists the assumptions that are present', () => {
    expect(describeAssumptions({ offer_cost: 40, success_rate: 0.3, horizon_months: 12, margin: 1 })).toBe(
      'offer cost $40.00, 30% success rate, 12 months of revenue kept',
    )
  })

  it('mentions a margin only when it is not 1', () => {
    expect(describeAssumptions({ offer_cost: 40, margin: 0.5 })).toBe('offer cost $40.00, 50% margin')
  })

  it('returns null when there is nothing to show', () => {
    expect(describeAssumptions(null)).toBeNull()
    expect(describeAssumptions({})).toBeNull()
  })
})

describe('orderNotes', () => {
  it('puts warnings first and keeps the original order otherwise', () => {
    const notes = [
      { level: 'info', text: 'a' },
      { level: 'warning', text: 'b' },
      { level: 'info', text: 'c' },
      { level: 'warning', text: 'd' },
    ]
    expect(orderNotes(notes).map((note) => note.text)).toEqual(['b', 'd', 'a', 'c'])
    expect(notes[0].text).toBe('a') // the original list is not changed
  })
})

describe('outcomeLabel', () => {
  it('turns the recorded outcome into words', () => {
    expect(outcomeLabel(true)).toBe('Churned')
    expect(outcomeLabel(false)).toBe('Stayed')
    expect(outcomeLabel(null)).toBe('Not known')
  })
})

describe('sentenceCase', () => {
  it('capitalises the first letter only', () => {
    expect(sentenceCase('contract type')).toBe('Contract type')
    expect(sentenceCase('')).toBe('')
  })
})