import { useSearchParams } from 'react-router-dom'
import { apiPath } from '../api/client'
import BreakdownPanel from '../components/BreakdownPanel'
import ContractFilter from '../components/ContractFilter'
import KpiDefinitions from '../components/KpiDefinitions'
import KpiStrip from '../components/KpiStrip'
import LoadState from '../components/LoadState'
import PageHeader from '../components/PageHeader'
import SurvivalPanel from '../components/SurvivalPanel'
import { CONTRACTS } from '../constants'
import { useApi } from '../hooks/useApi'

export default function Overview() {
  const [searchParams, setSearchParams] = useSearchParams()
  const requested = searchParams.get('contract') ?? ''
  const contract = CONTRACTS.includes(requested) ? requested : ''

  const { data, error, loading, waking, reload } = useApi(
    apiPath('/insights'),
    contract ? { contract } : null,
  )

  const changeContract = (value) => setSearchParams(value ? { contract: value } : {})
  const subtitle = data
    ? `${data.dataset_name} · ${data.model_version} · analysis run ${data.analysis_run_id}`
    : 'Customer churn at a glance'

  return (
    <section>
      <PageHeader
        title="Overview"
        subtitle={subtitle}
        actions={<ContractFilter value={contract} options={CONTRACTS} onChange={changeContract} />}
      />
      <LoadState loading={loading} waking={waking} error={error} onRetry={reload}>
        {data && (
          <div className="space-y-6">
            {contract && (
              <p className="rounded-md bg-accent-soft px-3 py-2 text-accent">
                Showing {contract} customers only. Survival figures use that contract's own curve
                when available.
              </p>
            )}
            <KpiStrip kpis={data.kpis} />
            <KpiDefinitions kpis={data.kpis} basisNote={data.basis_note} />
            <SurvivalPanel survival={data.survival} contract={contract} />
            <div>
              <h2 className="mb-2 text-sm font-medium text-muted">Churn breakdowns</h2>
              <div className="grid gap-4 lg:grid-cols-2">
                {!contract && (
                  <BreakdownPanel title="Churn by contract type" rows={data.breakdowns.by_contract} />
                )}
                <BreakdownPanel title="Churn by tenure (months)" rows={data.breakdowns.by_tenure} />
                <BreakdownPanel title="Churn by payment method" rows={data.breakdowns.by_payment_method} />
                <BreakdownPanel
                  title="Churn by customer segment"
                  rows={data.breakdowns.by_segment}
                  layout="rows"
                />
              </div>
            </div>
          </div>
        )}
      </LoadState>
    </section>
  )
}