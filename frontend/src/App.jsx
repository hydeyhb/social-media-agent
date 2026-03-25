import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import BrandPersona from './pages/BrandPersona'
import ContentLibrary from './pages/ContentLibrary'
import GenerateContent from './pages/GenerateContent'
import ImageCaption from './pages/ImageCaption'
import ThreadBuilder from './pages/ThreadBuilder'
import Analytics from './pages/Analytics'
import PostingTimes from './pages/PostingTimes'
import Optimization from './pages/Optimization'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
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
      </Routes>
    </BrowserRouter>
  )
}
