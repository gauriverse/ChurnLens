import BasisTag from './BasisTag'

export default function KpiDefinitions({ kpis, basisNote }) {
  return (
    <details className="rounded-lg border border-line bg-panel p-4">
      <summary className="cursor-pointer font-medium">How each number is calculated</summary>
      <p className="mt-3 text-muted">{basisNote}</p>
      <dl className="mt-4 space-y-3">
        {kpis.map((kpi) => (
          <div key={kpi.key}>
            <dt className="flex flex-wrap items-center gap-2 font-medium">
              {kpi.label}
              <BasisTag basis={kpi.basis} />
            </dt>
            <dd className="mt-1 text-muted">{kpi.definition}</dd>
          </div>
        ))}
      </dl>
    </details>
  )
}