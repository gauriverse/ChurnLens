import { apiPath } from '../api/client'
import LoadState from '../components/LoadState'
import PageHeader from '../components/PageHeader'
import { useApi } from '../hooks/useApi'

export default function Overview() {
  const { data, error, loading, waking, reload } = useApi(apiPath('/insights'))
  const value = (key) => data?.kpis.find((kpi) => kpi.key === key)?.value

  return (
    <section>
      <PageHeader
        title="Overview"
        subtitle="A first live check of the connection to the API. The full dashboard is built in the next step."
      />
      <LoadState loading={loading} waking={waking} error={error} onRetry={reload}>
        {data && (
          <dl className="grid max-w-md grid-cols-[1fr_auto] gap-x-6 gap-y-2 rounded-lg border border-line bg-panel p-5">
            <dt className="text-muted">Customers</dt>
            <dd className="text-right font-medium tabular-nums">
              {value('total_customers').toLocaleString()}
            </dd>
            <dt className="text-muted">Churn rate (observed)</dt>
            <dd className="text-right font-medium tabular-nums">
              {(value('churn_rate') * 100).toFixed(1)}%
            </dd>
            <dt className="text-muted">Revenue at risk, 12 months (model estimate)</dt>
            <dd className="text-right font-medium tabular-nums">
              ${Math.round(value('revenue_at_risk_12m')).toLocaleString()}
            </dd>
          </dl>
        )}
      </LoadState>
    </section>
  )
}