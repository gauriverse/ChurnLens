export default function Panel({ title, tag, className = '', children }) {
  return (
    <section className={`rounded-lg border border-line bg-panel p-4 ${className}`}>
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="font-medium">{title}</h2>
        {tag}
      </div>
      <div className="mt-3">{children}</div>
    </section>
  )
}