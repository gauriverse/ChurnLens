import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { SOURCE_LABELS } from '../constants'
import { PROFILE } from '../test/profileFixture'
import CustomerProfileView from './CustomerProfileView'

function renderView(profile = PROFILE) {
  return render(
    <MemoryRouter>
      <CustomerProfileView profile={profile} />
    </MemoryRouter>,
  )
}

// Queries limited to one panel, found by its heading
const panel = (name) => within(screen.getByRole('heading', { name }).closest('section'))

describe('CustomerProfileView', () => {
  it('shows the probability with its risk level, definition and source', () => {
    renderView()
    const risk = panel('Estimated churn risk')
    expect(risk.getByText('81.6%')).toBeInTheDocument()
    expect(risk.getByText('High')).toBeInTheDocument()
    expect(risk.getByText(PROFILE.probability_note)).toBeInTheDocument()
    expect(risk.getByText(PROFILE.model.risk_category_definition)).toBeInTheDocument()
    expect(risk.getByText(SOURCE_LABELS.holdout_test)).toBeInTheDocument()
    expect(risk.getByText('Revenue exposure (12 months)')).toBeInTheDocument()
    expect(risk.getByText('$1,028')).toBeInTheDocument()
    expect(risk.getByText('Exposure note from the API.')).toBeInTheDocument()
  })

  it('lists the customer facts, with the recorded outcome labelled as historical', () => {
    renderView()
    const details = panel('Customer details')
    for (const text of ['2 months', '$105.00', '$200.00', 'Month-to-month', 'Electronic check', 'Churned']) {
      expect(details.getByText(text)).toBeInTheDocument()
    }
    expect(details.getByText('Recorded outcome (historical)')).toBeInTheDocument()
  })

  it('explains the score in words and with a table of contributions', () => {
    renderView()
    const why = panel('Why the model scored this customer this way')
    expect(why.getByText(PROFILE.explanation.reason_text)).toBeInTheDocument()
    expect(why.getByRole('rowheader', { name: 'Tenure' })).toBeInTheDocument()
    expect(why.getByRole('rowheader', { name: 'Contract type' })).toBeInTheDocument()
    expect(why.getByRole('rowheader', { name: 'Internet service' })).toBeInTheDocument()
    expect(why.getByText('Raises risk · strongly (+1.48)')).toBeInTheDocument()
    expect(why.getByText('Raises risk · moderately (+0.30)')).toBeInTheDocument()
    expect(why.getByText('Lowers risk · strongly (-0.66)')).toBeInTheDocument()
    expect(why.getByText('Explanation note from the API.')).toBeInTheDocument()
  })

  it('says so when no explanation is stored', () => {
    renderView({ ...PROFILE, explanation: { ...PROFILE.explanation, reason_text: null, top_reasons: [] } })
    const why = panel('Why the model scored this customer this way')
    expect(why.getByText('No explanation is stored for this customer.')).toBeInTheDocument()
    expect(why.queryByRole('table')).not.toBeInTheDocument()
  })

  it('shows the segment and links to all segments', () => {
    renderView()
    const segment = panel('Segment')
    expect(segment.getByText('Newer fiber, month-to-month')).toBeInTheDocument()
    expect(segment.getByText('1,932')).toBeInTheDocument()
    expect(segment.getByText('56.3%')).toBeInTheDocument()
    expect(segment.getByText('#1')).toBeInTheDocument()
    expect(segment.getByText('High')).toBeInTheDocument()
    expect(segment.getByRole('link', { name: 'See all segments' })).toHaveAttribute('href', '/segments')
  })

  it('says so when the customer has no segment', () => {
    renderView({ ...PROFILE, segment: null })
    expect(
      panel('Segment').getByText('This customer is not assigned to a segment in this analysis run.'),
    ).toBeInTheDocument()
  })

  it('shows the recommendation with its assumptions and a hypothetical label', () => {
    renderView()
    const rec = panel('Retention recommendation')
    expect(rec.getByText('Hypothetical')).toBeInTheDocument()
    expect(rec.getByText(PROFILE.recommendation.suggested_action)).toBeInTheDocument()
    expect(rec.getByText('Newer customer')).toBeInTheDocument()
    expect(rec.getByText('Month-to-month contract')).toBeInTheDocument()
    expect(rec.getByText(PROFILE.recommendation.why_prioritized)).toBeInTheDocument()
    expect(rec.getByText('#1')).toBeInTheDocument()
    expect(rec.getByText('$268')).toBeInTheDocument()
    expect(
      rec.getByText('Assumptions: offer cost $40.00, 30% success rate, 12 months of revenue kept.'),
    ).toBeInTheDocument()
    expect(rec.getByText(PROFILE.recommendation.basis)).toBeInTheDocument()
    expect(rec.getByText(/not conclusions about why this customer might leave/)).toBeInTheDocument()
  })

  it('shows unknown reason codes as they are', () => {
    renderView({
      ...PROFILE,
      recommendation: { ...PROFILE.recommendation, reason_codes: ['NEW_CUSTOMER', 'SOMETHING_NEW'] },
    })
    expect(panel('Retention recommendation').getByText('SOMETHING_NEW')).toBeInTheDocument()
  })

  it('explains the absence of a recommendation', () => {
    renderView({ ...PROFILE, recommendation: null })
    expect(
      panel('Retention recommendation').getByText(/No recommendation is stored for this customer/),
    ).toBeInTheDocument()
  })

  it('shows warnings before ordinary notes, each labelled', () => {
    renderView()
    const items = panel('Estimated churn risk').getAllByRole('listitem')
    expect(items).toHaveLength(2)
    expect(items[0]).toHaveTextContent('Warning')
    expect(items[0]).toHaveTextContent('Only 38 customers')
    expect(items[1]).toHaveTextContent('Note')
    expect(items[1]).toHaveTextContent('held out of training')
  })

  it('names the model and the analysis run', () => {
    renderView()
    expect(
      screen.getByText('Scored by churn v1 (logistic_regression + sigmoid calibration) · analysis run 2.'),
    ).toBeInTheDocument()
  })
})