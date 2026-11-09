import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Placeholder from './components/Placeholder'
import Overview from './pages/Overview'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Overview />} />
        <Route
          path="customers"
          element={<Placeholder title="Customer Intelligence">Risk-ranked customers with search and filters.</Placeholder>}
        />
        <Route
          path="customers/:customerId"
          element={<Placeholder title="Customer Profile">One customer: probability, reasons, segment and recommendation.</Placeholder>}
        />
        <Route
          path="segments"
          element={<Placeholder title="Customer Segments">The five segments with their size, churn and revenue at risk.</Placeholder>}
        />
        <Route
          path="simulator"
          element={<Placeholder title="Retention Simulator">What-if retention campaigns. Every figure is hypothetical.</Placeholder>}
        />
        <Route
          path="model-health"
          element={<Placeholder title="Model Health">Data quality, drift and model evaluation.</Placeholder>}
        />
        <Route
          path="upload"
          element={<Placeholder title="Upload & Analyze">CSV upload and validation. Planned after the core pages.</Placeholder>}
        />
        <Route
          path="history"
          element={<Placeholder title="Analysis History">Past analysis runs.</Placeholder>}
        />
        <Route
          path="*"
          element={<Placeholder title="Page not found">That address does not exist. Use the menu to go back.</Placeholder>}
        />
      </Route>
    </Routes>
  )
}