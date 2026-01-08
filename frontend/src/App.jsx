import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

// Auth Pages
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';

// Admin Pages
import AdminDashboard from './pages/admin/AdminDashboard';
import LoanApplicationsPage from './pages/admin/LoanApplicationsPage';
import RiskAnalysisPage from './pages/admin/RiskAnalysisPage';
import AdminGrievancesPage from './pages/admin/GrievancesPage';

// User Pages
import UserDashboard from './pages/user/UserDashboard';
import ApplyLoanPage from './pages/user/ApplyLoanPage';
import MyLoansPage from './pages/user/MyLoansPage';
import UserGrievancesPage from './pages/user/GrievancesPage';
import ProfilePage from './pages/user/ProfilePage';

function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }
  
  if (!user) {
    return <Navigate to="/login" />;
  }
  
  if (adminOnly && user.role !== 'admin') {
    return <Navigate to="/dashboard" />;
  }
  
  return children;
}

function AppRoutes() {
  const { user } = useAuth();
  
  return (
    <Routes>
      {/* Auth Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      
      {/* Admin Routes */}
      <Route path="/admin" element={<ProtectedRoute adminOnly><AdminDashboard /></ProtectedRoute>} />
      <Route path="/admin/loans" element={<ProtectedRoute adminOnly><LoanApplicationsPage /></ProtectedRoute>} />
      <Route path="/admin/risk-analysis" element={<ProtectedRoute adminOnly><RiskAnalysisPage /></ProtectedRoute>} />
      <Route path="/admin/grievances" element={<ProtectedRoute adminOnly><AdminGrievancesPage /></ProtectedRoute>} />
      
      {/* User Routes */}
      <Route path="/dashboard" element={<ProtectedRoute><UserDashboard /></ProtectedRoute>} />
      <Route path="/apply-loan" element={<ProtectedRoute><ApplyLoanPage /></ProtectedRoute>} />
      <Route path="/my-loans" element={<ProtectedRoute><MyLoansPage /></ProtectedRoute>} />
      <Route path="/grievances" element={<ProtectedRoute><UserGrievancesPage /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
      
      {/* Default */}
      <Route path="/" element={
        user ? <Navigate to={user.role === 'admin' ? '/admin' : '/dashboard'} /> : <Navigate to="/login" />
      } />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}