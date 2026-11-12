import { useState } from 'react'
import { CONTRACTS, RISK_CATEGORIES } from '../constants'
import SelectFilter from './SelectFilter'

export default function CustomerFilters({ query, onChange, onClear }) {
  const [text, setText] = useState(query.search)
  const [seen, setSeen] = useState(query.search)
  if (query.search !== seen) {
    setSeen(query.search)
    setText(query.search)
  }
  const filtering = Boolean(query.search || query.contract || query.risk)

  const submit = (event) => {
    event.preventDefault()
    onChange({ search: text.trim() })
  }

  return (
    <div className="mb-4 flex flex-wrap items-center gap-3">
      <form onSubmit={submit} role="search" className="flex items-center gap-2">
        <input
          type="search"
          value={text}
          onChange={(event) => setText(event.target.value)}
          maxLength={100}
          placeholder="Search customer ID"
          aria-label="Search customer ID"
          className="w-56 rounded-md border border-line bg-panel px-3 py-1.5"
        />
        <button
          type="submit"
          className="rounded-md border border-line bg-panel px-3 py-1.5 font-medium hover:bg-canvas"
        >
          Search
        </button>
      </form>
      <SelectFilter
        label="Contract"
        allLabel="All contracts"
        value={query.contract}
        options={CONTRACTS}
        onChange={(value) => onChange({ contract: value })}
      />
      <SelectFilter
        label="Risk"
        allLabel="All risk levels"
        value={query.risk}
        options={RISK_CATEGORIES}
        onChange={(value) => onChange({ risk: value })}
      />
      {filtering && (
        <button type="button" onClick={onClear} className="font-medium text-accent underline">
          Clear filters
        </button>
      )}
    </div>
  )
}