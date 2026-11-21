import { render, screen } from '@testing-library/react'
import { AxiosError } from 'axios'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from '../api/client'
import { SEGMENTS } from '../test/segmentsFixture'
import Segments from './Segments'

vi.mock('../components/ConcentrationChart', () => ({ default: () => null })) // charts need a real screen size

const originalAdapter = api.defaults.adapter
afterEach(() => {
  api.defaults.adapter = originalAdapter
})

function serve(payload) {
  api.defaults.adapter = async (config) => ({
    data: payload,
    status: 200,
    statusText: 'OK',
    headers: {},
    config,
  })
}

function renderPage() {
  return render(
    <MemoryRouter>
      <Segments />
    </MemoryRouter>,
  )
}

describe('Segments page', () => {
  it('shows the table, the concentration summary and the segment descriptions', async () => {
    serve(SEGMENTS)
    renderPage()
    expect(await screen.findByText('7,043 customers in 5 segments · analysis run 2')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Segment comparison' })).toBeInTheDocument()
    expect(screen.getByRole('rowheader', { name: 'Newer fiber, month-to-month' })).toBeInTheDocument()
    expect(
      screen.getByText('Newer fiber, month-to-month: 27% of customers, 67% of the revenue at risk.'),
    ).toBeInTheDocument()
    expect(screen.getByText(SEGMENTS.segments[0].description)).toBeInTheDocument()
    expect(screen.getByRole('img', { name: /share of customers with its share of the revenue at risk/ })).toBeInTheDocument()
  })

  it('shows the notes written by the API', async () => {
    serve(SEGMENTS)
    renderPage()
    expect(await screen.findByText('Method note from the API.')).toBeInTheDocument()
    expect(screen.getByText('Priority note from the API.')).toBeInTheDocument()
    expect(screen.getByText(/The last column counts revenue from customers who actually churned/)).toBeInTheDocument()
  })

  it('says "1 segment" for a single segment', async () => {
    serve({ ...SEGMENTS, total_customers: 1932, segments: [SEGMENTS.segments[0]] })
    renderPage()
    expect(await screen.findByText('1,932 customers in 1 segment · analysis run 2')).toBeInTheDocument()
  })

  it('explains an empty result', async () => {
    serve({ ...SEGMENTS, total_customers: 0, segments: [] })
    renderPage()
    expect(await screen.findByText('No segments are stored for this analysis run.')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('shows the error from the API with a retry button', async () => {
    api.defaults.adapter = async (config) => {
      throw new AxiosError('Request failed with status code 503', 'ERR_BAD_RESPONSE', config, null, {
        status: 503,
        statusText: 'Error',
        headers: {},
        config,
        data: { detail: 'database temporarily unavailable, please retry' },
      })
    }
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('database temporarily unavailable, please retry')
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
  })
})