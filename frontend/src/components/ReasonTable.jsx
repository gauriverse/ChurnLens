import { EMPTY, formatSigned } from '../format'
import { reasonBars, sentenceCase } from '../profile'

export default function ReasonTable({ reasons }) {
  const bars = reasonBars(reasons)
  return (
    <div className="mt-3 overflow-x-auto">
      <table className="w-full text-left">
        <caption className="sr-only">Largest contributions to this customer's risk score</caption>
        <thead className="text-xs text-muted">
          <tr>
            <th scope="col" className="py-1.5 pr-3 font-medium">Factor</th>
            <th scope="col" className="px-3 py-1.5 font-medium">This customer</th>
            <th scope="col" className="px-3 py-1.5 font-medium">Effect on the score</th>
            <th scope="col" className="py-1.5 pl-3 font-medium">
              <span className="sr-only">Size of the effect</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {reasons.map((reason, index) => {
            const bar = bars[index]
            const effect = reason.direction === 'raises' ? 'Raises risk' : 'Lowers risk'
            return (
              <tr key={reason.rank} className="border-t border-line">
                <th scope="row" className="py-2 pr-3 font-normal">{sentenceCase(reason.label)}</th>
                <td className="px-3 py-2">{reason.value ?? EMPTY}</td>
                <td className="whitespace-nowrap px-3 py-2 tabular-nums">
                  {`${effect} · ${reason.strength} (${formatSigned(reason.contribution)})`}
                </td>
                <td className="py-2 pl-3">
                  <div className="relative h-3 w-40" aria-hidden="true">
                    <div className="absolute inset-y-0 left-1/2 w-px bg-line" />
                    <div
                      className={`absolute inset-y-0 rounded-sm ${
                        bar.side === 'right' ? 'left-1/2 bg-risk-high' : 'right-1/2 bg-accent'
                      }`}
                      style={{ width: `${bar.width}%` }}
                    />
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-muted">
        Bars to the right raise the risk score and bars to the left lower it. Longer bars mean a bigger effect.
      </p>
    </div>
  )
}