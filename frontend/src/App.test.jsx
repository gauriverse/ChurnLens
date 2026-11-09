import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import App from './App'


vi.mock('./api/client', async (importOriginal) => {
  const actual = await importOriginal()
  return { ...actual, api: { get: vi.fn(() => new Promise(() => {})) } }
})

function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('app shell', () => {
  it('lists every main page in the menu', () => {
    renderAt('/')
    const menu = screen.getByRole('navigation', { name: 'Main' })
    const labels = Array.from(menu.querySelectorAll('a')).map((link) => link.textContent)
    expect(labels).toEqual([
      'Overview',
      'Customer Intelligence',
      'Customer Segments',
      'Retention Simulator',
      'Model Health',
      'Upload & Analyze',
      'Analysis History',
    ])
  })

  it('marks the current page in the menu', () => {
    renderAt('/segments')
    expect(screen.getByRole('heading', { name: 'Customer Segments' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Customer Segments' })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('link', { name: 'Overview' })).not.toHaveAttribute('aria-current')
  })

  it('shows the profile page for a customer address and keeps Customer Intelligence highlighted', () => {
    renderAt('/customers/7590-VHVEG')
    expect(screen.getByRole('heading', { name: 'Customer Profile' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Customer Intelligence' })).toHaveAttribute('aria-current', 'page')
  })

  it('shows a not-found page for an unknown address', () => {
    renderAt('/nonsense')
    expect(screen.getByRole('heading', { name: 'Page not found' })).toBeInTheDocument()
  })
})