import { formatValue } from '../format'
import BasisTag from './BasisTag'

const GROUPS = [
  {
    title: 'Key figures',
    keys: ['total_customers', 'churn_rate', 'high_risk_customers', 'revenue_at_risk_12m', 'expected_active_months'],
    columns: 'grid-cols-2 md:grid-cols-3 xl:grid-cols-5',
  },
  {
    title: 'Retention indicators',
    keys: ['retention_rate', 'survival_12m', 'survival_24m', 'survival_48m', 'avg_tenure_months', 'flagged_customers'],
    columns: 'grid-cols-2 md:grid-cols-3 xl:grid-cols-6',
  },
]

export default function KpiStrip({ kpis }) {
  const byKey = Object.fromEntries(kpis.map((kpi) => [kpi.key, kpi]))

  return (
    <div className="space-y-5">
      {GROUPS.map((group) => (
        <section key={group.title} aria-label={group.title}>
          <h2 className="mb-2 text-sm font-medium text-muted">{group.title}</h2>
          <div className="overflow-hidden rounded-lg border border-line bg-panel">
            <dl className={`-mb-px -mr-px grid ${group.columns}`}>
              {group.keys
                .filter((key) => byKey[key])
                .map((key) => {
                  const kpi = byKey[key]
                  return (
                    <div key={key} title={kpi.definition} className="border-b border-r border-line p-4">
                      <dt className="text-muted">{kpi.label}</dt>
                      <dd className="mt-1">
                        <span className="block text-xl font-semibold tabular-nums">
                          {formatValue(kpi.value, kpi.unit)}
                        </span>
                        <span className="mt-2 block">
                          <BasisTag basis={kpi.basis} />
                        </span>
                      </dd>
                    </div>
                  )
                })}
            </dl>
          </div>
        </section>
      ))}
    </div>
  )
}