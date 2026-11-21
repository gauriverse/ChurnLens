import { Link, useParams } from 'react-router-dom'
import { apiPath } from '../api/client'
import CustomerProfileView from '../components/CustomerProfileView'
import LoadState from '../components/LoadState'
import PageHeader from '../components/PageHeader'
import { useApi } from '../hooks/useApi'

export default function CustomerProfile() {
  const { customerId } = useParams()
  const { data, error, loading, waking, reload } = useApi(
    apiPath(`/customers/${encodeURIComponent(customerId)}`),
  )

  return (
    <section>
      <Link to="/customers" className="mb-3 inline-block text-accent underline-offset-2 hover:underline">
        Back to Customer Intelligence
      </Link>
      <PageHeader title={customerId} subtitle="Customer profile" />
      <LoadState loading={loading} waking={waking} error={error} onRetry={reload}>
        {data && <CustomerProfileView profile={data} />}
      </LoadState>
    </section>
  )
}