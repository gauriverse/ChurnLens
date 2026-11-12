import { Link } from 'react-router-dom'
import { SOURCE_LABELS } from '../constants'
import { EMPTY, formatCurrency, formatInteger, formatMoney, formatPercent } from '../format'
import RiskBadge from './RiskBadge'

const COLUMNS = [
  { key: 'customer', label: 'Customer ID' },
  { key: 'churn_probability', label: 'Churn probability', sortable: true, align: 'right' },
  { key: 'risk', label: 'Risk' },
  { key: 'monthly_charges', label: 'Monthly charges', sortable: true, align: 'right' },
  { key: 'tenure', label: 'Tenure (months)', sortable: true, align: 'right' },
  { key: 'contract', label: 'Contract' },
  { key: 'estimated_revenue_exposure', label: 'Revenue exposure (12 mo)', sortable: true, align: 'right' },
]

function HeaderCell({ column, query, onSort }) {
  const align = column.align === 'right' ? 'text-right' : 'text-left'
  const base = `px-3 py-2 font-medium ${align}`
  if (!column.sortable) {
    return <th scope="col" className={base}>{column.label}</th>
  }
  const active = query.sort === column.key
  const ariaSort = active ? (query.order === 'asc' ? 'ascending' : 'descending') : 'none'
  return (
    <th scope="col" aria-sort={ariaSort} className={base}>
      <button type="button" onClick={() => onSort(column.key)} className="inline-flex items-center gap-1 hover:text-ink">
        {column.label}
        <span aria-hidden="true" className="w-3 text-[10px]">
          {active ? (query.order === 'asc' ? '▲' : '▼') : ''}
        </span>
      </button>
    </th>
  )
}

export default function CustomerTable({ rows, query, onSort }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-line bg-panel">
      <table className="w-full whitespace-nowrap tabular-nums">
        <caption className="sr-only">Customers ranked by estimated churn risk</caption>
        <thead className="bg-canvas text-xs text-muted">
          <tr>
            {COLUMNS.map((column) => (
              <HeaderCell key={column.key} column={column} query={query} onSort={onSort} />
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.customer_id} className="border-t border-line hover:bg-canvas">
              <th scope="row" className="px-3 py-2 text-left font-medium">
                <Link
                  to={`/customers/${encodeURIComponent(row.customer_id)}`}
                  className="text-accent underline-offset-2 hover:underline"
                >
                  {row.customer_id}
                </Link>
              </th>
              <td className="px-3 py-2 text-right" title={SOURCE_LABELS[row.prediction_source]}>
                {formatPercent(row.churn_probability)}
              </td>
              <td className="px-3 py-2">
                <RiskBadge category={row.risk_category} />
              </td>
              <td className="px-3 py-2 text-right">{formatMoney(row.monthly_charges)}</td>
              <td className="px-3 py-2 text-right">{formatInteger(row.tenure)}</td>
              <td className="px-3 py-2">{row.contract ?? EMPTY}</td>
              <td className="px-3 py-2 text-right">{formatCurrency(row.estimated_revenue_exposure)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}