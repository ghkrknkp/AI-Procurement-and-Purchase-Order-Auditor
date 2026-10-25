import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { Navbar } from './components/Navbar';

// Lazy-loaded pages — each becomes its own JS chunk
const Login = lazy(() => import('./pages/Login').then(m => ({ default: m.Login })));
const Register = lazy(() => import('./pages/Register').then(m => ({ default: m.Register })));
const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const DocumentsList = lazy(() => import('./pages/DocumentsList').then(m => ({ default: m.DocumentsList })));
const DocumentUpload = lazy(() => import('./pages/DocumentUpload').then(m => ({ default: m.DocumentUpload })));
const DocumentDetailPage = lazy(() => import('./pages/DocumentDetail').then(m => ({ default: m.DocumentDetailPage })));

const PageFallback: React.FC = () => (
  <div className="flex items-center justify-center min-h-[60vh]">
    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
  </div>
);

// Layout wrapper for authenticated pages
const AppLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected Routes */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/documents" element={<DocumentsList />} />
                <Route path="/documents/upload" element={<DocumentUpload />} />
                <Route path="/documents/:id" element={<DocumentDetailPage />} />
              </Route>
            </Route>

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
