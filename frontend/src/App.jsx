import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './context/AuthContext'
import { ConfirmProvider } from './context/ConfirmContext'
import Layout from './components/Layout'
import Home from './pages/Home'
import Login from './pages/Login'
import Signup from './pages/Signup'
import ActivateAccount from './pages/ActivateAccount'
import ResendActivation from './pages/ResendActivation'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import ContentDetail from './pages/ContentDetail'
import CreatorProfile from './pages/CreatorProfile'
import Subscriptions from './pages/Subscriptions'
import Library from './pages/Library'
import CreatorDashboard from './pages/CreatorDashboard'
import Settings from './pages/Settings'
import CollectionDetail from './pages/CollectionDetail'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ConfirmProvider>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/activate/:uid/:token" element={<ActivateAccount />} />
              <Route path="/resend-activation" element={<ResendActivation />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password/:uid/:token" element={<ResetPassword />} />
              <Route element={<Layout />}>
                <Route path="/" element={<Home />} />
                <Route path="/content/:id" element={<ContentDetail />} />
                <Route path="/profile/:id" element={<CreatorProfile />} />
                <Route path="/subscriptions" element={<Subscriptions />} />
                <Route path="/history" element={<Library />} />
                <Route path="/saved" element={<Library />} />
                <Route path="/creator" element={<CreatorDashboard />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/collections/:id" element={<CollectionDetail />} />
              </Route>
            </Routes>
          </ConfirmProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}