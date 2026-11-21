import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { SEGMENTS } from '../test/segmentsFixture'
import SegmentTable from './SegmentTable'

// Queries limited to the table row of one segment
const rowOf = (name) => within(screen.getByRole('rowheader', { name }).closest('tr'))

describe('SegmentTable', () => {
  it('lists the segments in the order given, with the totals row last', () => {
    render(<SegmentTable segments={SEGMENTS.segments} />)
    expect(screen.getAllByRole('rowheader').map((cell) => cell.textContent)).toEqual([
      'Newer fiber, month-to-month',
      'Long-tenured fiber, longer contracts',
      'Newer DSL, short contracts',
      'Long-tenured DSL, longer contracts',
      'No-internet customers',
      'All segments',
    ])
  })

  it('shows each number for a segment with its priority in words', () => {
    render(<SegmentTable segments={SEGMENTS.segments} />)
    const first = rowOf('Newer fiber, month-to-month')
    for (const text of [
      '#1', 'High priority', '1,932', '27.4% of customers', '56.3%', '$85.06',
      '$1,119,304', '66.5% of total', '66.6%',
    ]) {
      expect(first.getByText(text)).toBeInTheDocument()
    }
    const second = rowOf('Long-tenured fiber, longer contracts')
    expect(second.getByText('#2')).toBeInTheDocument()
    expect(second.getByText('Medium priority')).toBeInTheDocument()
    expect(second.getByText('$259,205')).toBeInTheDocument()
    expect(rowOf('No-internet customers').getByText('Low priority')).toBeInTheDocument()
  })

  it('adds up customers and revenue at risk, and shows a dash when the historical share is missing', () => {
    const segments = SEGMENTS.segments.map((segment, index) =>
      index === 0 ? { ...segment, characteristics: null } : segment,
    )
    render(<SegmentTable segments={segments} />)
    const totals = rowOf('All segments')
    expect(totals.getByText('7,043')).toBeInTheDocument()
    expect(totals.getByText('$1,682,240')).toBeInTheDocument()
    expect(rowOf('Newer fiber, month-to-month').getByText('—')).toBeInTheDocument()
    expect(rowOf('Newer DSL, short contracts').getByText('13.7%')).toBeInTheDocument()
  })
})