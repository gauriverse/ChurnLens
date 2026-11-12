import { formatInteger } from '../format'

const button =
  'rounded-md border border-line bg-panel px-3 py-1.5 font-medium hover:bg-canvas disabled:cursor-not-allowed disabled:opacity-50'

export default function Pagination({ page, pageCount, onPage }) {
  return (
    <nav aria-label="Pagination" className="flex items-center justify-end gap-3">
      <button type="button" className={button} disabled={page <= 1} onClick={() => onPage(page - 1)}>
        Previous
      </button>
      <span className="tabular-nums text-muted">
        Page {formatInteger(page)} of {formatInteger(pageCount)}
      </span>
      <button type="button" className={button} disabled={page >= pageCount} onClick={() => onPage(page + 1)}>
        Next
      </button>
    </nav>
  )
}