import { useApi } from '../hooks/useApi'

export default function ConnectionStatus() {
  const { loading, waking, error, reload } = useApi('/health')

  let dot = 'bg-gray-400'
  let text = 'Connecting to the API…'
  if (waking) {
    dot = 'bg-amber-500'
    text = 'Waking the server (free tier, up to a minute)…'
  }
  if (!loading && error) {
    dot = 'bg-red-600'
    text = 'API unreachable'
  }
  if (!loading && !error) {
    dot = 'bg-green-600'
    text = 'API online'
  }

  return (
    <div role="status" className="mt-3 flex items-start gap-2 text-xs text-muted">
      <span aria-hidden="true" className={`mt-1 h-2 w-2 shrink-0 rounded-full ${dot}`} />
      <span>
        {text}
        {!loading && error && (
          <button onClick={reload} className="ml-2 font-medium text-accent underline">
            Retry
          </button>
        )}
      </span>
    </div>
  )
}