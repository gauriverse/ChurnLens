import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Placeholder from './components/Placeholder'
import CustomerIntelligence from './pages/CustomerIntelligence'
import CustomerProfile from './pages/CustomerProfile'
import Overview from './pages/Overview'
import Segments from './pages/Segments'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Overview />} />
        <Route path="customers" element={<CustomerIntelligence />} />
        <Route path="customers/:customerId" element={<CustomerProfile />} />
        <Route path="segments" element={<Segments />} />
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