import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { SEGMENTS } from '../test/segmentsFixture'
import SegmentCards from './SegmentCards'

describe('SegmentCards', () => {
  it('shows each persona with its priority and its description', () => {
    render(<SegmentCards segments={SEGMENTS.segments} />)
    const cards = screen.getAllByRole('listitem')
    expect(cards).toHaveLength(5)
    const first = within(cards[0])
    expect(first.getByRole('heading', { name: 'Newer fiber, month-to-month' })).toBeInTheDocument()
    expect(first.getByText('High priority')).toBeInTheDocument()
    expect(first.getByText(SEGMENTS.segments[0].description)).toBeInTheDocument()
  })

  it('says so when a segment has no description', () => {
    const segments = [{ ...SEGMENTS.segments[0], description: null }]
    render(<SegmentCards segments={segments} />)
    expect(screen.getByText('No description is stored for this segment.')).toBeInTheDocument()
  })
})