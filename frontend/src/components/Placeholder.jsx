import PageHeader from './PageHeader'

export default function Placeholder({ title, children }) {
  return (
    <section>
      <PageHeader title={title} />
      <div className="rounded-lg border border-dashed border-line bg-panel p-8 text-muted">
        {children}
      </div>
    </section>
  )
}