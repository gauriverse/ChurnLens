import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import LoadState from './LoadState'

describe('LoadState', () => {
  it('shows a loading message', () => {
    render(<LoadState loading>content</LoadState>)
    expect(screen.getByRole('status')).toHaveTextContent('Loading')
    expect(screen.queryByText('content')).not.toBeInTheDocument()
  })

  it('explains a slow server', () => {
    render(<LoadState loading waking>content</LoadState>)
    expect(screen.getByRole('status')).toHaveTextContent('free tier')
  })

  it('shows the error and lets the user retry', () => {
    const onRetry = vi.fn()
    render(<LoadState error="Cannot reach the server." onRetry={onRetry}>content</LoadState>)
    expect(screen.getByRole('alert')).toHaveTextContent('Cannot reach the server.')
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('shows the content when everything worked', () => {
    render(<LoadState>content</LoadState>)
    expect(screen.getByText('content')).toBeInTheDocument()
  })
})