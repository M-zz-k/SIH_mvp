import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Layers, FolderOpen, ScanLine, 
  Scale, BarChart3, BookOpen, Settings, 
  Search, Bell, UserCircle, ChevronRight, Menu, X, LogOut
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Executive Command', icon: <LayoutDashboard className="w-5 h-5" /> },
  { to: '/bulk-upload', label: 'Bulk Ingestion', icon: <Layers className="w-5 h-5" /> },
  { to: '/repository', label: 'Field Dossiers', icon: <FolderOpen className="w-5 h-5" /> },
  { to: '/scan', label: 'Single Scan', icon: <ScanLine className="w-5 h-5" /> },
  { to: '/analytics', label: 'Regional Analytics', icon: <BarChart3 className="w-5 h-5" /> },
];

const SETTINGS_ITEMS = [
  { to: '/legal', label: 'Legal Decisions', icon: <Scale className="w-5 h-5" /> },
  { to: '/statutory', label: 'Statutory Rules', icon: <BookOpen className="w-5 h-5" /> },
  { to: '/settings', label: 'Settings', icon: <Settings className="w-5 h-5" /> },
];

export function AppLayout({ children, userRole }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const currentNav = [...NAV_ITEMS, ...SETTINGS_ITEMS].find(n => n.to === location.pathname) || { label: 'Detail View' };

  const handleLogout = () => {
    localStorage.removeItem('userRole');
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row w-full bg-canvas text-text-secondary">
      
      {/* 1. Sidebar - Desktop */}
      <aside className="hidden md:flex flex-col w-[80px] lg:w-[280px] bg-sidebar text-white shrink-0 h-screen sticky top-0 z-50 transition-all duration-300 shadow-xl">
        
        {/* Profile / Brand Header */}
        <div className="h-24 flex items-center justify-center lg:justify-start lg:px-6 border-b border-white/10 shrink-0">
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
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.label}
              to={item.to}
              className={({ isActive }) => `
                flex items-center gap-4 px-3 py-3 rounded-xl text-[13px] font-bold transition-all
                ${isActive ? 'bg-primary-dark/40 text-white' : 'text-primary-light opacity-80 hover:text-white hover:bg-white/5'}
              `}
            >
              <div className={`p-2 rounded-full shrink-0 transition-colors ${
                location.pathname === item.to ? 'bg-primary text-white' : 'bg-transparent text-primary-light'
              }`}>
                {item.icon}
              </div>
              <span className="hidden lg:block">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Pinned Bottom Navigation */}
        <div className="p-3 border-t border-white/10 flex flex-col gap-1 mb-2">
           {SETTINGS_ITEMS.map((item) => (
            <NavLink
              key={item.label}
              to={item.to}
              className={({ isActive }) => `
                flex items-center gap-4 px-3 py-2 rounded-xl text-[12px] font-bold transition-all
                ${isActive ? 'bg-primary-dark/40 text-white' : 'text-primary-light opacity-70 hover:text-white hover:bg-white/5'}
              `}
            >
              <div className="p-1.5 shrink-0">
                {item.icon}
              </div>
              <span className="hidden lg:block">{item.label}</span>
            </NavLink>
          ))}
          <button onClick={handleLogout} className="flex items-center gap-4 px-3 py-2 rounded-xl text-[12px] font-bold text-primary-light opacity-70 hover:text-white hover:bg-white/5 transition-all mt-2">
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

          <div className="flex items-center gap-4 shrink-0">
            <div className="relative hidden md:block">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="w-4 h-4 text-text-muted" />
              </div>
              <input
                type="text"
                placeholder="Search dossiers..."
                className="w-64 pl-10 pr-4 py-2 bg-card border-0 shadow-sm rounded-full text-[13px] font-medium focus:outline-none focus:ring-2 focus:ring-primary transition-shadow"
              />
            </div>
            
            <button className="text-text-muted hover:text-text-secondary relative p-2 bg-card rounded-full shadow-sm">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-status-err-text rounded-full border-2 border-card"></span>
            </button>
          </div>
        </header>

        {/* 3. Main Page Canvas */}
        <main className="flex-1 w-full max-w-[1440px] mx-auto px-4 sm:px-8 pb-10 overflow-y-auto">
          {children}
        </main>
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-text-primary/40 backdrop-blur-sm" onClick={() => setMobileOpen(false)}></div>
          <aside className="relative w-[280px] max-w-[80%] bg-sidebar text-white h-full flex flex-col shadow-2xl">
             <div className="h-24 flex items-center px-6 border-b border-white/10 shrink-0 justify-between">
                <div className="flex items-center gap-3">
                   <div className="w-10 h-10 bg-primary-light rounded-full flex items-center justify-center border-2 border-white/20 shrink-0">
                     <UserCircle className="w-6 h-6 text-white" />
                   </div>
                   <div>
                      <div className="text-sm font-bold tracking-wide">
                        {userRole === 'supervisor' ? 'K. Sharma' : 'Field Officer'}
                      </div>
                   </div>
                </div>
                <button onClick={() => setMobileOpen(false)} className="text-primary-light p-2"><X className="w-5 h-5" /></button>
             </div>
             
             <nav className="flex-1 py-8 overflow-y-auto flex flex-col gap-2 px-3">
              {NAV_ITEMS.map((item) => (
                <NavLink
                  key={item.label}
                  to={item.to}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) => `
                    flex items-center gap-4 px-3 py-3 rounded-xl text-[13px] font-bold transition-all
                    ${isActive ? 'bg-primary-dark/40 text-white' : 'text-primary-light opacity-80'}
                  `}
                >
                  <div className={`p-2 rounded-full shrink-0 transition-colors ${
                    location.pathname === item.to ? 'bg-primary text-white' : 'bg-transparent text-primary-light'
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
