import { apiPath } from '../api/client'
import BasisTag from '../components/BasisTag'
import ConcentrationChart from '../components/ConcentrationChart'
import LoadState from '../components/LoadState'
import PageHeader from '../components/PageHeader'
import Panel from '../components/Panel'
import SegmentCards from '../components/SegmentCards'
import SegmentTable from '../components/SegmentTable'
import { formatInteger } from '../format'
import { useApi } from '../hooks/useApi'
import { topSegmentSummary } from '../segments'

export default function Segments() {
  const { data, error, loading, waking, reload } = useApi(apiPath('/segments'))

  const count = data?.segments.length ?? 0
  const subtitle = data
    ? `${formatInteger(data.total_customers)} customers in ${count} segment${count === 1 ? '' : 's'} · analysis run ${data.analysis_run_id}`
    : 'Groups of similar customers and where the revenue at risk sits'

  return (
    <section>
      <PageHeader title="Customer Segments" subtitle={subtitle} />
      <LoadState loading={loading} waking={waking} error={error} onRetry={reload}>
        {data &&
          (count === 0 ? (
            <div className="rounded-lg border border-dashed border-line bg-panel p-8 text-center text-muted">
              No segments are stored for this analysis run.
            </div>
          ) : (
            <div className="space-y-6">
              <p className="text-muted">{data.method_note}</p>

              <Panel title="Segment comparison">
                <SegmentTable segments={data.segments} />
                <p className="mt-3 text-xs text-muted">
                  The last column counts revenue from customers who actually churned (historical). The
                  revenue-at-risk column is a model estimate. Comparing the two shows whether the model's
                  view matches history.
                </p>
                <p className="mt-1 text-xs text-muted">{data.priority_note}</p>
              </Panel>

              <Panel title="Where the revenue at risk sits" tag={<BasisTag basis="model_estimate" />}>
                <p className="text-muted">{topSegmentSummary(data.segments)}</p>
                <div
                  role="img"
                  aria-label="Bar chart comparing each segment's share of customers with its share of the revenue at risk. The numbers are in the table above."
                >
                  <ConcentrationChart segments={data.segments} />
                </div>
              </Panel>

              <div>
                <h2 className="mb-2 text-sm font-medium text-muted">Who is in each segment</h2>
                <SegmentCards segments={data.segments} />
              </div>
            </div>
          ))}
      </LoadState>
    </section>
  )
}