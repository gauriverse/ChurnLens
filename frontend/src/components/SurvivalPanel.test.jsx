import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import SurvivalPanel from './SurvivalPanel'

vi.mock('./SurvivalChart', () => ({ default: () => null })) 

const curve = (group, customers, events, expected, survivalAt) => ({
  group,
  customers,
  events,
  horizon_months: 72,
  expected_active_months: expected,
  survival_at: survivalAt,
  points: [{ month: 0, survival: 1 }],
})

const SURVIVAL = {
  available: true,
  method: 'Kaplan-Meier',
  note: 'Kaplan-Meier estimates from tenure and churn flags.',
  curves: [
    curve('All customers', 7032, 1869, 55.6, { 12: 0.843, 24: 0.789, 48: 0.709, 72: 0.593 }),
    curve('Month-to-month', 3875, 1655, 40.1, { 12: 0.7, 24: 0.6, 48: 0.5, 72: 0.4 }),
    curve('One year', 1473, 166, 66.0, { 12: 0.99 }),
  ],
}

describe('SurvivalPanel', () => {
  it('shows the API note, the table and a description of the chart', () => {
    render(<SurvivalPanel survival={SURVIVAL} contract="" />)
    expect(screen.getByRole('heading', { name: 'Survival curves' })).toBeInTheDocument()
    expect(screen.getByText('Survival estimate')).toBeInTheDocument()
    expect(screen.getByText('Kaplan-Meier estimates from tenure and churn flags.')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: /All customers, Month-to-month, One year/ })).toBeInTheDocument()
    expect(screen.getByText('7,032')).toBeInTheDocument()
    expect(screen.getByText('84.3%')).toBeInTheDocument()
    expect(screen.getByText('55.6')).toBeInTheDocument()
    expect(screen.getAllByText('—')).toHaveLength(3) // One year has no 24, 48 or 72 month values
  })

  it('narrows to the overall curve and the selected contract', () => {
    render(<SurvivalPanel survival={SURVIVAL} contract="One year" />)
    expect(screen.getByRole('img', { name: /All customers, One year/ })).toBeInTheDocument()
    expect(screen.getByRole('rowheader', { name: 'One year' })).toBeInTheDocument()
    expect(screen.queryByRole('rowheader', { name: 'Month-to-month' })).not.toBeInTheDocument()
  })

  it('passes on the API message when the curves were never computed', () => {
    const note = 'Survival curves have not been computed for this analysis run.'
    render(<SurvivalPanel survival={{ available: false, method: 'Kaplan-Meier', note, curves: [] }} contract="" />)
    expect(screen.getByText(note)).toBeInTheDocument()
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })

  it('says so when there are no curves for the selection', () => {
    render(<SurvivalPanel survival={{ ...SURVIVAL, curves: [] }} contract="" />)
    expect(screen.getByText('No survival curves are available for this selection.')).toBeInTheDocument()
  })
})