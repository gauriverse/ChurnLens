export default function ContractFilter({ value, options, onChange }) {
  return (
    <label className="flex items-center gap-2">
      <span className="text-muted">Contract</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-md border border-line bg-panel px-2 py-1.5"
      >
        <option value="">All contracts</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  )
}