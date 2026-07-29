import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import CalendarPage from './pages/Calendar'
import Payments from './pages/Payments'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/payments" element={<Payments />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
