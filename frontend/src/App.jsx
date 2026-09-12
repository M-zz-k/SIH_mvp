import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';

import { AppLayout } from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import BulkUploadPage from './pages/BulkUploadPage';
import ScanPage from './pages/ScanPage';
import InspectionPage from './pages/InspectionPage';
import RepositoryPage from './pages/RepositoryPage';
import AnalyticsPage from './pages/AnalyticsPage';
import SettingsPage from './pages/SettingsPage';

import LegalDecisionsPage from './pages/LegalDecisionsPage';
import StatutoryRulesPage from './pages/StatutoryRulesPage';
import ECommerceAuditPage from './pages/ECommerceAuditPage';

function App() {
  const [userRole, setUserRole] = useState(localStorage.getItem('userRole'));
  const location = useLocation();

  // Route protection
  useEffect(() => {
    const role = localStorage.getItem('userRole');
    setUserRole(role);
  }, [location.pathname]);

  if (!userRole && location.pathname !== '/login') {
    return <Navigate to="/login" replace />;
  }

  if (location.pathname === '/login') {
    return <LoginPage onLogin={(role) => {
      localStorage.setItem('userRole', role);
      setUserRole(role);
    }} />;
  }

  return (
    <AppLayout userRole={userRole}>
      <Routes>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/scan" element={<ScanPage />} />
        <Route path="/bulk-upload" element={
          userRole === 'inspector' ? <Navigate to="/dashboard" replace /> : <BulkUploadPage />
        } />
        <Route path="/ecommerce-audit" element={
          userRole === 'inspector' ? <Navigate to="/dashboard" replace /> : <ECommerceAuditPage />
        } />
        <Route path="/inspection/:id" element={<InspectionPage />} />
        <Route path="/repository" element={<RepositoryPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        
        {/* Statutory & Legal Vault routes */}
        <Route path="/legal" element={<LegalDecisionsPage />} />
        <Route path="/statutory" element={<StatutoryRulesPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AppLayout>
  );
}


export default App;
