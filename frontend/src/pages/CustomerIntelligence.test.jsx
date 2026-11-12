import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { AxiosError } from 'axios'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it } from 'vitest'
import { api } from '../api/client'
import CustomerIntelligence from './CustomerIntelligence'

const originalAdapter = api.defaults.adapter
afterEach(() => {
  api.defaults.adapter = originalAdapter
})

const ROWS = [
  {
    customer_id: '6496-SLWHQ', churn_probability: 0.8161, risk_category: 'High',
    monthly_charges: 105, tenure: 2, contract: 'Month-to-month',
    estimated_revenue_exposure: 1028.29, prediction_source: 'holdout_test',
  },
  {
    customer_id: '7590-VHVEG', churn_probability: 0.3617, risk_category: 'Medium',
    monthly_charges: 29.85, tenure: 1, contract: 'Month-to-month',
    estimated_revenue_exposure: 129.57, prediction_source: 'out_of_fold_train',
  },
]

const listing = (overrides = {}) => ({
  analysis_run_id: 2,
  total: 60,
  page: 1,
  page_size: 25,
  exposure_horizon_months: 12,
  exposure_note: 'Exposure note from the API.',
  items: ROWS,
  ...overrides,
})


function serve(payload = listing()) {
  const calls = []
  api.defaults.adapter = async (config) => {
    calls.push(config.params)
    const data = typeof payload === 'function' ? payload(config.params) : payload
    return { data, status: 200, statusText: 'OK', headers: {}, config }
  }
  return calls
}

function renderPage(path = '/customers') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <CustomerIntelligence />
    </MemoryRouter>,
  )
}

describe('CustomerIntelligence', () => {
  it('shows each customer with formatted values and a link to the profile', async () => {
    serve()
    renderPage()
    expect(await screen.findByText('Showing 1–2 of 60 customers')).toBeInTheDocument()

    const link = screen.getByRole('link', { name: '6496-SLWHQ' })
    expect(link).toHaveAttribute('href', '/customers/6496-SLWHQ')
    const row = within(link.closest('tr'))
    expect(row.getByText('81.6%')).toHaveAttribute('title', expect.stringContaining('held-out'))
    expect(row.getByText('High')).toBeInTheDocument()
    expect(row.getByText('$105.00')).toBeInTheDocument()
    expect(row.getByText('$1,028')).toBeInTheDocument()
    expect(row.getByText('Month-to-month')).toBeInTheDocument()
    expect(screen.getByText('Exposure note from the API.')).toBeInTheDocument()
    expect(screen.getByText(/display cutoffs/)).toBeInTheDocument()
  })

  it('marks the sorted column and starts with the riskiest customers', async () => {
    const calls = serve()
    renderPage()
    await screen.findByText(/Showing 1–2/)
    expect(calls[0]).toEqual({ sort_by: 'churn_probability', order: 'desc', page: 1, page_size: 25 })
    expect(screen.getByRole('columnheader', { name: /Churn probability/ })).toHaveAttribute('aria-sort', 'descending')
    expect(screen.getByRole('columnheader', { name: /Tenure/ })).toHaveAttribute('aria-sort', 'none')
  })

  it('searches by customer ID and starts again from the first page', async () => {
    const calls = serve()
    renderPage('/customers?page=2')
    await screen.findByText(/Showing 26–27/)
    fireEvent.change(screen.getByLabelText('Search customer ID'), { target: { value: ' 7590 ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    await waitFor(() => expect(calls.at(-1)).toMatchObject({ search: '7590', page: 1 }))
    expect(screen.getByRole('button', { name: 'Clear filters' })).toBeInTheDocument()
  })

  it('filters by contract and risk and can clear the filters', async () => {
    const calls = serve()
    renderPage()
    await screen.findByText(/Showing 1–2/)
    fireEvent.change(screen.getByLabelText('Risk'), { target: { value: 'High' } })
    await waitFor(() => expect(calls.at(-1)).toMatchObject({ risk: 'High', page: 1 }))
    fireEvent.change(screen.getByLabelText('Contract'), { target: { value: 'One year' } })
    await waitFor(() => expect(calls.at(-1)).toMatchObject({ risk: 'High', contract: 'One year' }))
    fireEvent.click(screen.getByRole('button', { name: 'Clear filters' }))
    await waitFor(() => expect(calls.at(-1)).not.toHaveProperty('risk'))
    expect(calls.at(-1)).not.toHaveProperty('contract')
    expect(screen.getByLabelText('Risk')).toHaveValue('')
  })

  it('sorts by a column and reverses the order on a second click', async () => {
    const calls = serve()
    renderPage()
    await screen.findByText(/Showing 1–2/)
    fireEvent.click(screen.getByRole('button', { name: /Tenure/ }))
    await waitFor(() => expect(calls.at(-1)).toMatchObject({ sort_by: 'tenure', order: 'desc', page: 1 }))
    expect(screen.getByRole('columnheader', { name: /Tenure/ })).toHaveAttribute('aria-sort', 'descending')
    fireEvent.click(screen.getByRole('button', { name: /Tenure/ }))
    await waitFor(() => expect(calls.at(-1)).toMatchObject({ sort_by: 'tenure', order: 'asc' }))
    expect(screen.getByRole('columnheader', { name: /Tenure/ })).toHaveAttribute('aria-sort', 'ascending')
  })

  it('pages forwards and backwards', async () => {
    const calls = serve()
    renderPage()
    await screen.findByText(/Showing 1–2/)
    expect(screen.getByText('Page 1 of 3')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    await waitFor(() => expect(calls.at(-1)).toMatchObject({ page: 2 }))
    expect(await screen.findByText('Page 2 of 3')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Previous' }))
    await waitFor(() => expect(calls.at(-1)).toMatchObject({ page: 1 }))
  })

  it('disables Next on the last page', async () => {
    serve()
    renderPage('/customers?page=3')
    await screen.findByText('Page 3 of 3')
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Previous' })).toBeEnabled()
  })

  it('ignores unknown values in the address', async () => {
    const calls = serve()
    renderPage('/customers?risk=Extreme&sort=password&order=sideways&page=-3&contract=Weekly')
    await screen.findByText(/Showing 1–2/)
    expect(calls[0]).toEqual({ sort_by: 'churn_probability', order: 'desc', page: 1, page_size: 25 })
    expect(screen.getByLabelText('Risk')).toHaveValue('')
  })

  it('explains an empty result and lets the user show everything again', async () => {
    const calls = serve((params) => (params.risk ? listing({ total: 0, items: [] }) : listing()))
    renderPage('/customers?risk=High')
    expect(await screen.findByText('No customers match these filters.')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('No customers')
    fireEvent.click(screen.getByRole('button', { name: 'Show all customers' }))
    expect(await screen.findByText(/Showing 1–2/)).toBeInTheDocument()
    expect(calls.at(-1)).not.toHaveProperty('risk')
  })

  it('handles a page past the end of the results', async () => {
    const calls = serve((params) => (params.page > 3 ? listing({ items: [] }) : listing()))
    renderPage('/customers?page=9')
    expect(await screen.findByText('This page is past the end of the results.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Go to the first page' }))
    expect(await screen.findByText(/Showing 1–2/)).toBeInTheDocument()
    expect(calls.at(-1)).toMatchObject({ page: 1 })
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