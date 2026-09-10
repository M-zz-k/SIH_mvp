/**
 * METROSCAN AI — App Router
 *
 * Person 1 (Frontend Lead) owns this file.
 * Defines the route structure and top-level layout.
 *
 * Routes:
 *   /           → Login page
 *   /upload     → Upload page (single + bulk)
 *   /results    → Results detail page (renders most recent or by ID)
 *   /repository → Repository / Search page
 */

import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import LoginPage from './pages/LoginPage.jsx'
import UploadPage from './pages/UploadPage.jsx'
import ResultsPage from './pages/ResultsPage.jsx'
import RepositoryPage from './pages/RepositoryPage.jsx'

function App() {
  const location = useLocation()
  const isLoginPage = location.pathname === '/'

  return (
    <div className="min-h-screen flex flex-col">
      {/* Navigation — hidden on login page */}
      {!isLoginPage && (
        <nav className="glass sticky top-0 z-50 px-6 py-3 flex items-center gap-8">
          <div className="flex items-center gap-3 mr-8">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-bold text-sm">
              M
            </div>
            <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-primary-light to-accent bg-clip-text text-transparent">
              METROSCAN AI
            </span>
          </div>

          {[
            { to: '/upload', label: '📤 Upload' },
            { to: '/results', label: '📊 Results' },
            { to: '/repository', label: '🔍 Repository' },
          ].map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-primary/20 text-primary-light'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              {label}
            </NavLink>
          ))}

          <button
            onClick={() => window.location.href = '/'}
            className="ml-auto text-sm text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
          >
            Logout
          </button>
        </nav>
      )}

      {/* Main content */}
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/results/:id" element={<ResultsPage />} />
          <Route path="/repository" element={<RepositoryPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
