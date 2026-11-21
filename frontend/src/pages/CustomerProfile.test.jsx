import { render, screen } from '@testing-library/react'
import { AxiosError } from 'axios'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it } from 'vitest'
import { api } from '../api/client'
import { PROFILE } from '../test/profileFixture'
import CustomerProfile from './CustomerProfile'

const originalAdapter = api.defaults.adapter
afterEach(() => {
  api.defaults.adapter = originalAdapter
})


function serve(payload) {
  const urls = []
  api.defaults.adapter = async (config) => {
    urls.push(config.url)
    return { data: payload, status: 200, statusText: 'OK', headers: {}, config }
  }
  return urls
}

function renderPage(path = '/customers/6496-SLWHQ') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/customers/:customerId" element={<CustomerProfile />} />
        <Route path="/customers" element={<p>Customer list</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('CustomerProfile page', () => {
  it('shows the customer ID at once and the profile when it arrives', async () => {
    const urls = serve(PROFILE)
    renderPage()
    expect(screen.getByRole('heading', { name: '6496-SLWHQ' })).toBeInTheDocument()
    expect(await screen.findByText('81.6%')).toBeInTheDocument()
    expect(urls).toEqual(['/api/v1/customers/6496-SLWHQ'])
  })

  it('encodes unusual characters when asking the API', async () => {
    const urls = serve({ ...PROFILE, customer_id: 'AB 12' })
    renderPage('/customers/AB%2012')
    expect(await screen.findByText('81.6%')).toBeInTheDocument()
    expect(urls).toEqual(['/api/v1/customers/AB%2012'])
    expect(screen.getByRole('heading', { name: 'AB 12' })).toBeInTheDocument()
  })

  it('shows the API message when the customer is not found', async () => {
    api.defaults.adapter = async (config) => {
      throw new AxiosError('Request failed with status code 404', 'ERR_BAD_RESPONSE', config, null, {
        status: 404,
        statusText: 'Not Found',
        headers: {},
        config,
        data: { detail: 'customer not found in this analysis run' },
      })
    }
    renderPage('/customers/NOPE')
    expect(await screen.findByRole('alert')).toHaveTextContent('customer not found in this analysis run')
    expect(screen.getByRole('heading', { name: 'NOPE' })).toBeInTheDocument()
  })

    it('links back to the customer list', async () => {
    serve(PROFILE)
    renderPage()
    expect(await screen.findByText('81.6%')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back to Customer Intelligence' })).toHaveAttribute(
      'href',
      '/customers',
    )
  })
})