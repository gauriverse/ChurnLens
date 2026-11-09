export default function LoadState({ loading, waking, error, onRetry, children }) {
  if (loading) {
    return (
      <div role="status" className="rounded-lg border border-line bg-panel p-6 text-muted">
        {waking
          ? 'Still waiting for the server. On the free tier it sleeps when idle and can take about a minute to wake up.'
          : 'Loading…'}
      </div>
    )
  }
  if (error) {
    return (
      <div role="alert" className="rounded-lg border border-line bg-panel p-6">
        <p className="font-medium">Could not load this page</p>
        <p className="mt-1 text-muted">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-4 rounded-md bg-accent px-3 py-2 font-medium text-white hover:opacity-90"
          >
            Try again
          </button>
        )}
      </div>
    )
  }
  return children
}