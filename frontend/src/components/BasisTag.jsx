const BASIS = {
  observed: { label: 'Observed', className: 'border-line bg-canvas text-muted' },
  model_estimate: { label: 'Model estimate', className: 'border-transparent bg-accent-soft text-accent' },
  survival_estimate: { label: 'Survival estimate', className: 'border-transparent bg-survival-soft text-survival' },
}


export default function BasisTag({ basis }) {
  const style = BASIS[basis] ?? { label: basis, className: 'border-line bg-canvas text-muted' }
  return (
    <span
      className={`inline-block rounded border px-1.5 py-0.5 text-[11px] font-medium leading-none ${style.className}`}
    >
      {style.label}
    </span>
  )
}