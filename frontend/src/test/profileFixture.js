export const PROFILE = {
  analysis_run_id: 2,
  customer_id: '6496-SLWHQ',
  tenure: 2,
  monthly_charges: 105,
  total_charges: 200,
  contract: 'Month-to-month',
  payment_method: 'Electronic check',
  observed_churn: true,
  model: {
    name: 'churn',
    version: 'v1',
    algorithm: 'logistic_regression + sigmoid calibration',
    decision_threshold: 0.2,
    risk_category_definition:
      'Low below 0.20, Medium 0.20 to 0.50, High 0.50 and above (display cutoffs, not statistics)',
  },
  prediction: {
    churn_probability: 0.8161,
    risk_category: 'High',
    prediction_source: 'holdout_test',
    estimated_revenue_exposure: 1028.29,
    exposure_horizon_months: 12,
    exposure_note: 'Exposure note from the API.',
  },
  explanation: {
    unit: 'log-odds',
    reason_text:
      "Factors raising this customer's churn risk score: tenure and billing (2 months, $105.00/month, strongly).",
    top_reasons: [
      { rank: 1, feature: 'tenure', label: 'tenure', value: '2 months', contribution: 1.48, direction: 'raises', strength: 'strongly' },
      { rank: 2, feature: 'Contract', label: 'contract type', value: 'Month-to-month', contribution: 0.3, direction: 'raises', strength: 'moderately' },
      { rank: 3, feature: 'InternetService', label: 'internet service', value: 'DSL', contribution: -0.66, direction: 'lowers', strength: 'strongly' },
    ],
    note: 'Explanation note from the API.',
  },
  segment: {
    cluster_id: 3,
    persona_name: 'Newer fiber, month-to-month',
    size: 1932,
    churn_rate: 0.563,
    retention_priority: 1,
    priority_tier: 'High',
  },
  recommendation: {
    priority_rank: 1,
    expected_value: 268.28,
    reason_codes: ['NEW_CUSTOMER', 'MONTH_TO_MONTH'],
    suggested_action: 'Contact this newer customer early. Review contract renewal options.',
    why_prioritized:
      'Rank 1: churn probability 82% on $105.00/month gives an expected net value of $268 under the assumed $40 offer cost and 30% success rate.',
    assumptions: { offer_cost: 40, success_rate: 0.3, horizon_months: 12, margin: 1 },
    basis: 'Hypothetical: based on an assumed offer cost and success rate, not on measured outcomes.',
  },
  probability_note:
    'A churn probability is a calibrated estimate of risk, not a certainty about this customer.',
  notes: [
    { level: 'info', text: 'This customer was held out of training; the probability comes from a model that never saw them.' },
    { level: 'warning', text: 'Only 38 customers with known outcomes fall in this probability band, so the observed rate is noisy.' },
  ],
}