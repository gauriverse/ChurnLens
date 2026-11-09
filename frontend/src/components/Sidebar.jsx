import { NavLink } from 'react-router-dom'
import { NAV_ITEMS } from '../nav'
import ConnectionStatus from './ConnectionStatus'

const linkClass = ({ isActive }) =>
  [
    'whitespace-nowrap rounded-md px-3 py-2 font-medium',
    isActive ? 'bg-accent-soft text-accent' : 'text-muted hover:bg-canvas hover:text-ink',
  ].join(' ')

export default function Sidebar() {
  return (
    <aside className="border-b border-line bg-panel md:sticky md:top-0 md:flex md:h-screen md:w-60 md:shrink-0 md:flex-col md:border-b-0 md:border-r">
      <div className="px-4 py-4 md:px-5 md:py-6">
        <div className="text-base font-semibold tracking-tight">ChurnLens</div>
        <div className="text-xs text-muted">Customer churn intelligence</div>
        <ConnectionStatus />
      </div>
      <nav
        aria-label="Main"
        className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-col md:overflow-visible"
      >
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={linkClass}>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}