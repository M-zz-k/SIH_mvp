import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, User, Briefcase, Settings } from 'lucide-react';

function LoginPage({ onLogin }) {
  const navigate = useNavigate();

  const handleLogin = (role) => {
    onLogin(role);
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-canvas flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-14 h-14 bg-sidebar rounded-2xl flex items-center justify-center font-bold text-primary text-2xl tracking-widest shadow-sm border border-primary/30">
            M
          </div>
        </div>
        <h2 className="mt-6 text-center text-2xl font-bold tracking-tight text-text-primary">
          METROSCAN AI
        </h2>
        <p className="mt-2 text-center text-sm text-text-secondary font-medium">
          Legal Metrology Enforcement Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-card py-8 px-4 shadow-sm border border-border-subtle sm:rounded-2xl sm:px-10">
          
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest border-b border-border-subtle pb-2 mb-4">
              Select Demo Role (Requirement 8)
            </h3>

            <button
              onClick={() => handleLogin('inspector')}
              className="w-full flex items-center gap-4 p-4 border border-border-subtle rounded-xl hover:border-primary hover:bg-primary-light/10 transition-colors text-left group"
            >
              <div className="bg-canvas border border-border-subtle p-2.5 rounded-lg group-hover:bg-primary-light/20 group-hover:text-primary group-hover:border-primary/30 text-text-muted transition-colors">
                <User className="w-5 h-5" />
              </div>
              <div>
                <div className="font-bold text-text-primary text-sm">Inspector</div>
                <div className="text-xs text-text-secondary mt-0.5">Mobile capture & immediate triage</div>
              </div>
            </button>

            <button
              onClick={() => handleLogin('supervisor')}
              className="w-full flex items-center gap-4 p-4 border border-border-subtle rounded-xl hover:border-primary hover:bg-primary-light/10 transition-colors text-left group"
            >
              <div className="bg-canvas border border-border-subtle p-2.5 rounded-lg group-hover:bg-primary-light/20 group-hover:text-primary group-hover:border-primary/30 text-text-muted transition-colors">
                <Briefcase className="w-5 h-5" />
              </div>
              <div>
                <div className="font-bold text-text-primary text-sm">Supervisor</div>
                <div className="text-xs text-text-secondary mt-0.5">Bulk ingestion & docket approvals</div>
              </div>
            </button>

            <button
              onClick={() => handleLogin('admin')}
              className="w-full flex items-center gap-4 p-4 border border-border-subtle rounded-xl hover:border-primary hover:bg-primary-light/10 transition-colors text-left group"
            >
              <div className="bg-canvas border border-border-subtle p-2.5 rounded-lg group-hover:bg-primary-light/20 group-hover:text-primary group-hover:border-primary/30 text-text-muted transition-colors">
                <Settings className="w-5 h-5" />
              </div>
              <div>
                <div className="font-bold text-text-primary text-sm">System Admin</div>
                <div className="text-xs text-text-secondary mt-0.5">Rule configuration & analytics</div>
              </div>
            </button>
          </div>

          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border-subtle" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="bg-card px-2 text-text-muted text-[10px] uppercase font-bold tracking-widest">
                  Secure Portal
                </span>
              </div>
            </div>
            
            <div className="mt-4 flex items-center justify-center gap-2 text-xs text-text-muted font-medium">
              <Shield className="w-4 h-4 text-status-ok-text" />
              Official Government Use Only
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
