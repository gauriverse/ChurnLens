export default function PageHeader({ title, subtitle,actions }) {
  return (
    <header className="mb-6 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
      {subtitle && <p className="mt-1 text-muted">{subtitle}</p>}
      </div>
      {actions}
    </header>
  )
}