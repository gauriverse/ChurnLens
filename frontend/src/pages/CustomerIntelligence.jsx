import { useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { apiPath } from '../api/client'
import CustomerFilters from '../components/CustomerFilters'
import CustomerTable from '../components/CustomerTable'
import LoadState from '../components/LoadState'
import PageHeader from '../components/PageHeader'
import Pagination from '../components/Pagination'
import { nextSort, pageCount, pageRange, readQuery, toApiParams, toSearchParams } from '../customerQuery'
import { formatInteger } from '../format'
import { useApi } from '../hooks/useApi'

function summaryText(total, count, range) {
  if (total === 0) return 'No customers'
  if (count === 0) return '0 customers on this page'
  return `Showing ${formatInteger(range.from)}–${formatInteger(range.to)} of ${formatInteger(total)} customers`
}

function EmptyResults({ total, filtering, onShowAll, onFirstPage }) {
  const pastEnd = total > 0
  const message = pastEnd
    ? 'This page is past the end of the results.'
    : filtering
      ? 'No customers match these filters.'
      : 'No customers found in this analysis run.'
  const action = pastEnd
    ? { label: 'Go to the first page', run: onFirstPage }
    : filtering
      ? { label: 'Show all customers', run: onShowAll }
      : null
  return (
    <div className="rounded-lg border border-dashed border-line bg-panel p-8 text-center text-muted">
      <p>{message}</p>
      {action && (
        <button type="button" onClick={action.run} className="mt-3 font-medium text-accent underline">
          {action.label}
        </button>
      )}
    </div>
  )
}

export default function CustomerIntelligence() {
  const [searchParams, setSearchParams] = useSearchParams()
  const query = useMemo(() => readQuery(searchParams), [searchParams])
  const { data, error, loading, refreshing, waking, reload } = useApi(
    apiPath('/customers'),
    toApiParams(query),
    { keepPrevious: true },
  )

  const go = (next) => setSearchParams(toSearchParams(next))
  const update = (changes) => go({ ...query, ...changes, page: 1 })
  const clearFilters = () => go({ ...query, search: '', contract: '', risk: '', page: 1 })
  const filtering = Boolean(query.search || query.contract || query.risk)

  const rows = data?.items ?? []
  const total = data?.total ?? 0
  const range = pageRange(query.page, rows.length)

  return (
    <section>
      <PageHeader
        title="Customer Intelligence"
        subtitle="Customers ranked by estimated churn risk. Probabilities are calibrated estimates, not certainties."
      />
      <CustomerFilters query={query} onChange={update} onClear={clearFilters} />
      <LoadState loading={loading} waking={waking} error={error} onRetry={reload}>
        {data && (
          <div className="space-y-3">
            <p role="status" className="text-muted">
              {summaryText(total, rows.length, range)}
              {refreshing && ' · Updating…'}
            </p>
            {rows.length === 0 ? (
              <EmptyResults
                total={total}
                filtering={filtering}
                onShowAll={clearFilters}
                onFirstPage={() => go({ ...query, page: 1 })}
              />
            ) : (
              <>
                <CustomerTable rows={rows} query={query} onSort={(column) => go(nextSort(query, column))} />
                <Pagination
                  page={query.page}
                  pageCount={pageCount(total)}
                  onPage={(page) => go({ ...query, page })}
                />
              </>
            )}
            <p className="text-xs text-muted">{data.exposure_note}</p>
            <p className="text-xs text-muted">
              Risk levels are display cutoffs on the model's probability, not statistical thresholds.
              The exact cutoffs are shown on each customer's profile. Hover over a probability to see
              how it was estimated.
            </p>
          </div>
        )}
      </LoadState>
    </section>
  )
}