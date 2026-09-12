import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Layers, FolderOpen, ScanLine, 
  Scale, BarChart3, BookOpen, Settings, Globe,
  Search, Bell, UserCircle, ChevronRight, Menu, X, LogOut
} from 'lucide-react';

const ALL_NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" />, roles: ['inspector', 'supervisor', 'admin'] },
  { to: '/scan', label: 'Single Scan', icon: <ScanLine className="w-5 h-5" />, roles: ['inspector', 'admin'] },
  { to: '/bulk-upload', label: 'Bulk Ingestion', icon: <Layers className="w-5 h-5" />, roles: ['supervisor', 'admin'] },
  { to: '/ecommerce-audit', label: 'E-Commerce Audit', icon: <Globe className="w-5 h-5" />, roles: ['supervisor', 'admin'] },
  { to: '/repository', label: 'Field Dossiers', icon: <FolderOpen className="w-5 h-5" />, roles: ['inspector', 'supervisor', 'admin'] },
  { to: '/analytics', label: 'Regional Analytics', icon: <BarChart3 className="w-5 h-5" />, roles: ['supervisor', 'admin'] },
];

const SETTINGS_ITEMS = [
  { to: '/legal', label: 'Legal Decisions', icon: <Scale className="w-5 h-5" />, roles: ['inspector', 'supervisor', 'admin'] },
  { to: '/statutory', label: 'Statutory Rules', icon: <BookOpen className="w-5 h-5" />, roles: ['inspector', 'supervisor', 'admin'] },
  { to: '/settings', label: 'Settings', icon: <Settings className="w-5 h-5" />, roles: ['admin', 'supervisor', 'inspector'] },
];

export function AppLayout({ children, userRole }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const currentRole = userRole || 'inspector';
  const navItems = ALL_NAV_ITEMS.filter(item => item.roles.includes(currentRole));
  const settingsItems = SETTINGS_ITEMS.filter(item => item.roles.includes(currentRole));
  
  const currentNav = [...ALL_NAV_ITEMS, ...SETTINGS_ITEMS].find(n => n.to === location.pathname) || { label: 'Detail View' };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('userRole');
    localStorage.removeItem('userEmail');
    window.location.href = '/login';
  };

  const handleSwitchRole = (newRole) => {
    localStorage.setItem('userRole', newRole);
    window.location.reload();
  };


  return (
    <div className="min-h-screen flex w-full bg-[var(--color-canvas-outer)] text-text-secondary p-4 md:p-6 gap-6">
      
      {/* 1. Sidebar - Desktop */}
      <aside className="hidden md:flex flex-col w-[80px] lg:w-[280px] bg-sidebar text-white shrink-0 h-[calc(100vh-48px)] sticky top-6 z-50 transition-all duration-300 shadow-[0_8px_25px_rgba(12,45,55,0.15)] rounded-3xl overflow-hidden">
        
        {/* Profile / Brand Header */}
        <div className="h-28 pt-4 flex items-center justify-center lg:justify-start lg:px-6 shrink-0 bg-[#0A2229] border-b border-white/5 relative z-10">
          <div className="flex items-center gap-3">
             <div className="w-10 h-10 bg-primary-light rounded-full flex items-center justify-center border-2 border-white/20 shrink-0">
               <UserCircle className="w-6 h-6 text-white" />
             </div>
             <div className="hidden lg:block">
                <div className="text-sm font-bold tracking-wide text-white">
                  {userRole === 'supervisor' ? 'K. Sharma' : userRole === 'admin' ? 'System Admin' : 'Field Officer'}
                </div>
                <div className="text-[10px] text-primary-light font-bold uppercase tracking-widest mt-0.5">
                  {userRole === 'supervisor' ? 'HQ Supervisor' : userRole === 'admin' ? 'DoCA Central' : 'Inspector'}
                </div>
             </div>
          </div>
        </div>
        
        {/* Navigation items - Circular icon pins */}
        <nav className="flex-1 py-8 overflow-y-auto flex flex-col gap-2 px-3">
          {navItems.map((item) => (
            <NavLink
              key={item.label}
              to={item.to}
              className={({ isActive }) => `
                flex items-center gap-4 px-3 py-3 rounded-2xl text-[15px] font-bold transition-all duration-200
                ${isActive ? 'bg-white text-[#0E5E73] shadow-sm ml-2' : 'text-[#B2CBD3] hover:text-white hover:bg-white/10 mx-2'}
              `}
            >
              <div className={`p-2 rounded-xl shrink-0 transition-colors ${
                location.pathname === item.to ? 'text-[#0E5E73]' : 'bg-transparent text-[#B2CBD3]'
              }`}>
                {item.icon}
              </div>
              <span className="hidden lg:block">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Pinned Bottom Navigation */}
        <div className="p-3 border-t border-white/10 flex flex-col gap-1 mb-2">
           {settingsItems.map((item) => (
            <NavLink
              key={item.label}
              to={item.to}
              className={({ isActive }) => `
                flex items-center gap-4 px-3 py-2.5 rounded-xl text-[14px] font-bold transition-all hover:translate-x-1 duration-200
                ${isActive ? 'bg-primary-dark/40 text-white' : 'text-white hover:text-primary-light hover:bg-white/10'}
              `}
            >
              <div className="p-1.5 shrink-0">
                {item.icon}
              </div>
              <span className="hidden lg:block">{item.label}</span>
            </NavLink>
          ))}
          <button onClick={handleLogout} className="flex items-center gap-4 px-3 py-2.5 rounded-xl text-[14px] font-bold text-white hover:text-status-err-text hover:bg-white/10 transition-all hover:translate-x-1 duration-200 mt-2 cursor-pointer">
            <div className="p-1.5 shrink-0"><LogOut className="w-5 h-5" /></div>
            <span className="hidden lg:block">Log Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* 2. Top Bar (Minimal) */}
        <header className="h-16 bg-transparent flex items-center justify-between px-4 sm:px-8 shrink-0 z-40 mt-2">
          
          <div className="flex items-center gap-4 flex-1">
            <button className="md:hidden p-2 -ml-2 text-text-muted bg-card rounded-lg shadow-sm" onClick={() => setMobileOpen(true)}>
              <Menu className="w-5 h-5" />
            </button>
            
            <div className="hidden sm:flex items-center text-[12px] font-bold text-text-muted uppercase tracking-widest">
              <span>Metroscan AI</span>
              <ChevronRight className="w-4 h-4 mx-2 text-border-strong" />
              <span className="text-text-primary">{currentNav.label}</span>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {/* Quick Role Switcher Pill */}
            <div className="flex items-center gap-1.5 bg-card border border-border-subtle p-1 rounded-xl shadow-sm text-xs font-bold">
              <span className="text-[10px] text-text-muted uppercase tracking-wider px-2 hidden lg:inline">Role:</span>
              <button 
                onClick={() => handleSwitchRole('inspector')} 
                className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer text-xs ${currentRole === 'inspector' ? 'bg-primary text-white' : 'text-text-secondary hover:bg-canvas'}`}
              >
                Inspector
              </button>
              <button 
                onClick={() => handleSwitchRole('supervisor')} 
                className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer text-xs ${currentRole === 'supervisor' ? 'bg-primary text-white' : 'text-text-secondary hover:bg-canvas'}`}
              >
                Supervisor
              </button>
              <button 
                onClick={() => handleSwitchRole('admin')} 
                className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer text-xs ${currentRole === 'admin' ? 'bg-primary text-white' : 'text-text-secondary hover:bg-canvas'}`}
              >
                Admin
              </button>
            </div>

            <button className="text-text-muted hover:text-text-secondary relative p-2 bg-card rounded-full shadow-sm cursor-pointer">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-status-err-text rounded-full border-2 border-card"></span>
            </button>
          </div>
        </header>

        {/* 3. Main Page Canvas with fade-in animation */}
        <main className="flex-1 w-full max-w-[1440px] mx-auto px-4 sm:px-8 pb-10 overflow-y-auto animate-in fade-in duration-500 bg-canvas rounded-3xl shadow-[0_8px_25px_rgba(12,45,55,0.06)] mt-4 pt-8">
          {children}
        </main>
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-text-primary/40 backdrop-blur-sm" onClick={() => setMobileOpen(false)}></div>
          <aside className="relative w-[280px] max-w-[80%] bg-sidebar text-white h-full flex flex-col shadow-2xl rounded-r-3xl overflow-hidden">
             <div className="h-28 pt-4 flex items-center px-6 shrink-0 justify-between bg-primary-dark/50 border-b border-white/5 relative z-10">
                <div className="flex items-center gap-3">
                   <div className="w-10 h-10 bg-primary-light rounded-full flex items-center justify-center border-2 border-white/20 shrink-0">
                     <UserCircle className="w-6 h-6 text-white" />
                   </div>
                   <div>
                      <div className="text-sm font-bold tracking-wide capitalize">
                        {currentRole}
                      </div>
                   </div>
                </div>
                <button onClick={() => setMobileOpen(false)} className="text-primary-light p-2"><X className="w-5 h-5" /></button>
             </div>
             
             <nav className="flex-1 py-8 overflow-y-auto flex flex-col gap-2 px-3">
              {navItems.map((item) => (
                <NavLink
                  key={item.label}
                  to={item.to}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) => `
                    flex items-center gap-4 px-3 py-3 rounded-2xl text-[13px] font-bold transition-all
                    ${isActive ? 'bg-white text-primary shadow-sm ml-2' : 'text-white/60 hover:text-white mx-2'}
                  `}
                >
                  <div className={`p-2 rounded-xl shrink-0 transition-colors ${
                    location.pathname === item.to ? 'text-primary' : 'bg-transparent text-white/60'
                  }`}>
                    {item.icon}
                  </div>
                  <span>{item.label}</span>
                </NavLink>
              ))}
             </nav>
          </aside>
        </div>
      )}
    </div>
  );
}
