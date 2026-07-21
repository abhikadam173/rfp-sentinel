import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import ProtectedRoute from './components/ProtectedRoute'
import Landing from './pages/Landing'
import BuyerLogin from './pages/BuyerLogin'
import BuyerDashboard from './pages/BuyerDashboard'
import ComingSoon from './pages/ComingSoon'

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<BuyerLogin />} />
            <Route
              path="/buyer/dashboard"
              element={
                <ProtectedRoute>
                  <BuyerDashboard />
                </ProtectedRoute>
              }
            />
            <Route path="/bidder/dashboard" element={<ComingSoon role="Bidder" />} />
            <Route path="/admin/dashboard" element={<ComingSoon role="Admin" />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}
