export default function AssumedTag({ children = 'Hypothetical' }) {
  return (
    <span className="inline-block rounded border border-transparent bg-assumed-soft px-1.5 py-0.5 text-[11px] font-medium leading-none text-assumed">
      {children}
    </span>
  )
}