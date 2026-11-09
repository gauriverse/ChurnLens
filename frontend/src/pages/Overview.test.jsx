import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from '../api/client'
import Overview from './Overview'

vi.mock('../components/BreakdownChart', () => ({ default: () => null }))

const originalAdapter = api.defaults.adapter
afterEach(() => {
  api.defaults.adapter = originalAdapter
})

const KPIS = [
  ['total_customers', 'Total customers', 7043, 'customers', 'observed'],
  ['churn_rate', 'Churn rate', 0.2654, 'share', 'observed'],
  ['retention_rate', 'Retention rate', 0.7346, 'share', 'observed'],
  ['high_risk_customers', 'High-risk customers', 1200, 'customers', 'model_estimate'],
  ['flagged_customers', 'Customers above the decision threshold', 3423, 'customers', 'model_estimate'],
  ['revenue_at_risk_12m', 'Revenue at risk (12 months)', 1682239.4, 'currency', 'model_estimate'],
  ['avg_tenure_months', 'Average tenure', 32.4, 'months', 'observed'],
  ['expected_active_months', 'Average customer lifetime', 55.6, 'months', 'survival_estimate'],
  ['survival_12m', 'Still active after 12 months', 0.843, 'share', 'survival_estimate'],
  ['survival_24m', 'Still active after 24 months', 0.789, 'share', 'survival_estimate'],
  ['survival_48m', 'Still active after 48 months', null, 'share', 'survival_estimate'],
].map(([key, label, value, unit, basis]) => ({
  key,
  label,
  value,
  unit,
  basis,
  definition: `Definition of ${label}`,
}))

const row = (label, customers, observed, predicted, revenue) => ({
  label,
  customers,
  observed_churn_rate: observed,
  avg_predicted_probability: predicted,
  revenue_at_risk_12m: revenue,
})

const INSIGHTS = {
  analysis_run_id: 2,
  dataset_name: 'Telco Customer Churn',
  model_version: 'churn v1',
  filters: {},
  kpis: KPIS,
  breakdowns: {
    by_contract: [
      row('Month-to-month', 3875, 0.4271, 0.43, 1608000),
      row('One year', 1473, 0.1127, 0.11, 60000),
      row('Two year', 1695, 0.0283, 0.03, 14000),
    ],
    by_tenure: [row('0-6', 1481, 0.4, 0.41, 500000), row('49+', 2239, 0.07, 0.07, 100000)],
    by_payment_method: [
      row('Electronic check', 2365, 0.4529, 0.45, 900000),
      row('Mailed check', 1612, 0.1911, 0.19, 300000),
    ],
    by_segment: [
      row('Newer fiber, month-to-month', 1932, 0.563, 0.566, 1119304),
      row('No-internet customers', 1526, 0.074, 0.073, 27498),
    ],
  },
  survival: { available: true, method: 'Kaplan-Meier', note: '', curves: [] },
  basis_note: 'Observed values are counted from the dataset.',
}


function serve(payload) {
  const calls = []
  api.defaults.adapter = async (config) => {
    calls.push({ url: config.url, params: config.params })
    return { data: payload, status: 200, statusText: 'OK', headers: {}, config }
  }
  return calls
}

function renderOverview(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Overview />
    </MemoryRouter>,
  )
}

describe('Overview', () => {
  it('shows every KPI with its value and where it comes from', async () => {
    serve(INSIGHTS)
    renderOverview()
    expect(await screen.findByText('7,043')).toBeInTheDocument()
    expect(screen.getByText('26.5%')).toBeInTheDocument()
    expect(screen.getByText('$1,682,239')).toBeInTheDocument()
    expect(screen.getByText('55.6 months')).toBeInTheDocument()
    expect(screen.getByText('84.3%')).toBeInTheDocument()
    expect(screen.getAllByText('—')).toHaveLength(1) // the unavailable 48-month survival
    expect(screen.getAllByText('Observed').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Model estimate').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Survival estimate').length).toBeGreaterThan(0)
    expect(screen.getByText(/Telco Customer Churn · churn v1 · analysis run 2/)).toBeInTheDocument()
  })

  it('explains how each number is calculated', async () => {
    serve(INSIGHTS)
    renderOverview()
    await screen.findByText('7,043')
    expect(screen.getByText('How each number is calculated')).toBeInTheDocument()
    expect(screen.getByText('Definition of Churn rate')).toBeInTheDocument()
    expect(screen.getByText('Observed values are counted from the dataset.')).toBeInTheDocument()
  })

  it('asks the API for one contract and hides the contract chart', async () => {
    const calls = serve(INSIGHTS)
    renderOverview()
    expect(await screen.findByRole('heading', { name: 'Churn by contract type' })).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Contract'), { target: { value: 'One year' } })

    expect(await screen.findByText(/Showing One year customers only/)).toBeInTheDocument()
    expect(calls.at(-1).params).toEqual({ contract: 'One year' })
    expect(screen.queryByRole('heading', { name: 'Churn by contract type' })).not.toBeInTheDocument()
    expect(screen.getByLabelText('Contract')).toHaveValue('One year')
  })

  it('reads the filter from the address', async () => {
    const calls = serve(INSIGHTS)
    renderOverview('/?contract=Two%20year')
    expect(await screen.findByText(/Showing Two year customers only/)).toBeInTheDocument()
    expect(calls[0].params).toEqual({ contract: 'Two year' })
  })

  it('ignores an unknown contract in the address', async () => {
    const calls = serve(INSIGHTS)
    renderOverview('/?contract=Weekly')
    expect(await screen.findByText('7,043')).toBeInTheDocument()
    expect(calls[0].params).toBeUndefined()
    expect(screen.getByLabelText('Contract')).toHaveValue('')
  })
})