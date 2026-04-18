import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import useAuthStore from './store/authStore'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'
import BrandPersona from './pages/BrandPersona'
import ContentLibrary from './pages/ContentLibrary'
import GenerateContent from './pages/GenerateContent'
import ImageCaption from './pages/ImageCaption'
import ThreadBuilder from './pages/ThreadBuilder'
import Analytics from './pages/Analytics'
import PostingTimes from './pages/PostingTimes'
import Optimization from './pages/Optimization'

function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="brand" element={<BrandPersona />} />
            <Route path="library" element={<ContentLibrary />} />
            <Route path="generate" element={<GenerateContent />} />
            <Route path="image" element={<ImageCaption />} />
            <Route path="thread" element={<ThreadBuilder />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="timing" element={<PostingTimes />} />
            <Route path="optimize" element={<Optimization />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
