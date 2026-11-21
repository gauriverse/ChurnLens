import { Link } from 'react-router-dom'
import { SOURCE_LABELS } from '../constants'
import {
  EMPTY, formatCurrency, formatInteger, formatMoney, formatMonths, formatPercent,
} from '../format'
import { describeAssumptions, outcomeLabel, reasonCodeLabel } from '../profile'
import AssumedTag from './AssumedTag'
import FactList from './FactList'
import NoteList from './NoteList'
import Panel from './Panel'
import ReasonTable from './ReasonTable'
import RiskBadge from './RiskBadge'

function PredictionPanel({ profile }) {
  const { prediction, model } = profile
  const source = SOURCE_LABELS[prediction.prediction_source]
  return (
    <Panel title="Estimated churn risk" className="lg:col-span-2">
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-3xl font-semibold tabular-nums">
          {formatPercent(prediction.churn_probability)}
        </span>
        <RiskBadge category={prediction.risk_category} />
      </div>
      <p className="mt-2 text-muted">{profile.probability_note}</p>
      {source && <p className="mt-1 text-xs text-muted">{source}</p>}
      <p className="mt-1 text-xs text-muted">{model.risk_category_definition}</p>
      <div className="mt-4 border-t border-line pt-3">
        <FactList
          items={[
            {
              label: `Revenue exposure (${prediction.exposure_horizon_months} months)`,
              value: formatCurrency(prediction.estimated_revenue_exposure),
            },
          ]}
        />
        <p className="mt-2 text-xs text-muted">{prediction.exposure_note}</p>
      </div>
      {profile.notes.length > 0 && (
        <div className="mt-4 border-t border-line pt-3">
          <h3 className="mb-2 text-sm font-medium text-muted">Data quality and context</h3>
          <NoteList notes={profile.notes} />
        </div>
      )}
    </Panel>
  )
}

function DetailsPanel({ profile }) {
  return (
    <Panel title="Customer details">
      <FactList
        items={[
          { label: 'Tenure', value: formatMonths(profile.tenure) },
          { label: 'Monthly charges', value: formatMoney(profile.monthly_charges) },
          { label: 'Total charges', value: formatMoney(profile.total_charges) },
          { label: 'Contract', value: profile.contract ?? EMPTY },
          { label: 'Payment method', value: profile.payment_method ?? EMPTY },
          { label: 'Recorded outcome (historical)', value: outcomeLabel(profile.observed_churn) },
        ]}
      />
    </Panel>
  )
}

function ExplanationPanel({ explanation }) {
  return (
    <Panel title="Why the model scored this customer this way" className="lg:col-span-3">
      {explanation.reason_text && <p>{explanation.reason_text}</p>}
      {explanation.top_reasons.length === 0 ? (
        <p className="text-muted">No explanation is stored for this customer.</p>
      ) : (
        <ReasonTable reasons={explanation.top_reasons} />
      )}
      <p className="mt-3 text-xs text-muted">{explanation.note}</p>
    </Panel>
  )
}

function SegmentPanel({ segment }) {
  return (
    <Panel title="Segment">
      {segment ? (
        <>
          <p className="font-medium">{segment.persona_name}</p>
          <div className="mt-3">
            <FactList
              items={[
                { label: 'Customers in segment', value: formatInteger(segment.size) },
                { label: 'Observed churn in segment', value: formatPercent(segment.churn_rate) },
                { label: 'Segment retention priority', value: `#${segment.retention_priority}` },
                { label: 'Priority tier', value: segment.priority_tier },
              ]}
            />
          </div>
          <Link to="/segments" className="mt-3 inline-block text-accent underline-offset-2 hover:underline">
            See all segments
          </Link>
        </>
      ) : (
        <p className="text-muted">This customer is not assigned to a segment in this analysis run.</p>
      )}
    </Panel>
  )
}

function RecommendationPanel({ recommendation }) {
  const assumptions = recommendation ? describeAssumptions(recommendation.assumptions) : null
  return (
    <Panel title="Retention recommendation" tag={<AssumedTag />} className="lg:col-span-2">
      {recommendation ? (
        <>
          {recommendation.suggested_action && (
            <p className="font-medium">{recommendation.suggested_action}</p>
          )}
          {recommendation.reason_codes.length > 0 && (
            <>
              <p className="mt-2 text-xs text-muted">Based on</p>
              <ul className="list-disc pl-5">
                {recommendation.reason_codes.map((code) => (
                  <li key={code}>{reasonCodeLabel(code)}</li>
                ))}
              </ul>
            </>
          )}
          {recommendation.why_prioritized && <p className="mt-3">{recommendation.why_prioritized}</p>}
          <div className="mt-3">
            <FactList
              items={[
                { label: 'Priority rank', value: `#${formatInteger(recommendation.priority_rank)}` },
                { label: 'Expected net value (revenue)', value: formatCurrency(recommendation.expected_value) },
              ]}
            />
          </div>
          {assumptions && <p className="mt-3 text-xs text-muted">{`Assumptions: ${assumptions}.`}</p>}
          <p className="mt-1 text-xs text-muted">{recommendation.basis}</p>
        </>
      ) : (
        <p className="text-muted">
          No recommendation is stored for this customer. In this analysis, recommendations exist only
          for customers whose expected value under the assumed offer cost and success rate is positive.
        </p>
      )}
      <p className="mt-3 text-xs text-muted">
        Suggestions to investigate, not conclusions about why this customer might leave.
      </p>
    </Panel>
  )
}

export default function CustomerProfileView({ profile }) {
  const { model } = profile
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <PredictionPanel profile={profile} />
      <DetailsPanel profile={profile} />
      <ExplanationPanel explanation={profile.explanation} />
      <SegmentPanel segment={profile.segment} />
      <RecommendationPanel recommendation={profile.recommendation} />
      <p className="text-xs text-muted lg:col-span-3">
        {`Scored by ${model.name} ${model.version} (${model.algorithm}) · analysis run ${profile.analysis_run_id}.`}
      </p>
    </div>
  )
}