import { EMPTY, formatInteger, formatPercent } from '../format'
import { visibleCurves } from '../survival'
import BasisTag from './BasisTag'
import SurvivalChart from './SurvivalChart'

const MILESTONES = ['12', '24', '48', '72']

function SurvivalTable({ curves }) {
  return (
    <div className="mt-2 overflow-x-auto">
      <table className="w-full text-left tabular-nums">
        <thead className="text-xs text-muted">
          <tr>
            <th className="py-1.5 pr-3 font-medium">Group</th>
            <th className="px-3 py-1.5 text-right font-medium">Customers</th>
            <th className="px-3 py-1.5 text-right font-medium">Churned</th>
            {MILESTONES.map((months) => (
              <th key={months} className="px-3 py-1.5 text-right font-medium">
                Active at {months} mo
              </th>
            ))}
            <th
              className="py-1.5 pl-3 text-right font-medium"
              title="Area under the curve: the expected number of active months within the observed window (up to 72 months)"
            >
              Expected active months
            </th>
          </tr>
        </thead>
        <tbody>
          {curves.map((curve) => (
            <tr key={curve.group} className="border-t border-line">
              <th scope="row" className="py-1.5 pr-3 font-normal">{curve.group}</th>
              <td className="px-3 py-1.5 text-right">{formatInteger(curve.customers)}</td>
              <td className="px-3 py-1.5 text-right">{formatInteger(curve.events)}</td>
              {MILESTONES.map((months) => (
                <td key={months} className="px-3 py-1.5 text-right">
                  {curve.survival_at?.[months] == null ? EMPTY : formatPercent(curve.survival_at[months])}
                </td>
              ))}
              <td className="py-1.5 pl-3 text-right">{curve.expected_active_months.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function SurvivalPanel({ survival, contract }) {
  const curves = survival.available ? visibleCurves(survival.curves, contract) : []
  const names = curves.map((curve) => curve.group).join(', ')

  return (
    <section className="rounded-lg border border-line bg-panel p-4" aria-labelledby="survival-title">
      <div className="flex flex-wrap items-center gap-2">
        <h2 id="survival-title" className="font-medium">Survival curves</h2>
        <BasisTag basis="survival_estimate" />
      </div>
      <p className="mt-1 text-xs text-muted">Share of customers still active after each month of tenure.</p>

      {curves.length === 0 ? (
        <p className="mt-3 rounded-md border border-dashed border-line p-4 text-muted">
          {survival.available ? 'No survival curves are available for this selection.' : survival.note}
        </p>
      ) : (
        <>
          <div
            role="img"
            aria-label={`Line chart of the share of customers still active by months of tenure for: ${names}`}
          >
            <SurvivalChart curves={curves} />
          </div>
          <p className="mt-2 text-xs text-muted">{survival.note}</p>
          <details className="mt-3">
            <summary className="cursor-pointer text-muted">Show the numbers</summary>
            <SurvivalTable curves={curves} />
          </details>
        </>
      )}
    </section>
  )
}