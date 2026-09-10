import React, { useState, useEffect } from 'react';
import { GridContainer, Card, CardHeader, CardBody } from '../components/Primitives';
import { User, Bell, Shield, Moon, Sun, Monitor } from 'lucide-react';

function SettingsPage() {
  const [profile, setProfile] = useState({
    name: 'K. Sharma',
    email: 'k.sharma@gov.in',
    designation: 'HQ Supervisor'
  });
  const [notifications, setNotifications] = useState({
    highSeverity: true,
    dailyDigest: false,
    weeklyReport: true
  });
  
  const role = localStorage.getItem('userRole') || 'inspector';

  return (
    <div className="flex flex-col gap-6">
      
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">System Settings</h1>
          <p className="text-[11px] text-text-muted mt-1 uppercase tracking-widest font-bold">Preferences & Access Control</p>
        </div>
      </div>

      <GridContainer>
        
        {/* Profile Section */}
        <Card className="col-span-1 md:col-span-2 lg:col-span-6">
          <CardHeader actions={<User className="w-4 h-4 text-text-muted" />}>Profile Details</CardHeader>
          <CardBody className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-text-muted uppercase tracking-widest mb-1.5">Full Name</label>
              <input 
                type="text" 
                value={profile.name} 
                onChange={(e) => setProfile({...profile, name: e.target.value})}
                className="w-full bg-canvas border border-border-subtle rounded-xl px-4 py-2.5 text-sm font-bold text-text-primary focus:outline-none focus:border-primary transition-colors"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-text-muted uppercase tracking-widest mb-1.5">Email Address</label>
                <input 
                  type="email" 
                  value={profile.email} 
                  onChange={(e) => setProfile({...profile, email: e.target.value})}
                  className="w-full bg-canvas border border-border-subtle rounded-xl px-4 py-2.5 text-sm font-bold text-text-primary focus:outline-none focus:border-primary transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-text-muted uppercase tracking-widest mb-1.5">Designation</label>
                <input 
                  type="text" 
                  value={profile.designation} 
                  onChange={(e) => setProfile({...profile, designation: e.target.value})}
                  className="w-full bg-canvas border border-border-subtle rounded-xl px-4 py-2.5 text-sm font-bold text-text-primary focus:outline-none focus:border-primary transition-colors"
                />
              </div>
            </div>
            <div className="pt-4 mt-2 border-t border-border-subtle flex justify-end">
              <button className="px-5 py-2 bg-primary text-white text-xs font-bold rounded-lg shadow-sm hover:bg-primary-dark transition-colors">
                Save Changes
              </button>
            </div>
          </CardBody>
        </Card>

        {/* Role & Access (RBAC) */}
        <Card className="col-span-1 md:col-span-2 lg:col-span-6">
          <CardHeader actions={<Shield className="w-4 h-4 text-text-muted" />}>Role & Access (Read-Only)</CardHeader>
          <CardBody className="flex flex-col h-full">
            <div className="mb-6">
              <div className="text-xs font-bold text-text-muted uppercase tracking-widest mb-2">Current Assigned Role</div>
              <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary-light/10 text-primary-dark text-sm font-bold border border-primary/20 capitalize">
                {role}
              </div>
            </div>
            
            <div className="flex-1 space-y-3">
              <div className="text-xs font-bold text-text-muted uppercase tracking-widest mb-2">Capability Matrix</div>
              
              <CapabilityRow label="View Field Dossiers" granted={true} />
              <CapabilityRow label="Upload Single Scans" granted={true} />
              <CapabilityRow label="Approve / Reject Dockets" granted={role === 'supervisor' || role === 'admin'} />
              <CapabilityRow label="Configure Legal Rules" granted={role === 'admin'} />
              <CapabilityRow label="User Management" granted={role === 'admin'} />
            </div>
          </CardBody>
        </Card>

        {/* Notifications */}
        <Card className="col-span-1 md:col-span-1 lg:col-span-6">
          <CardHeader actions={<Bell className="w-4 h-4 text-text-muted" />}>Notification Preferences</CardHeader>
          <CardBody className="space-y-4">
            <ToggleRow 
              label="Email me on high-severity flags" 
              description="Immediate alerts for major non-compliance events."
              checked={notifications.highSeverity}
              onChange={() => setNotifications({...notifications, highSeverity: !notifications.highSeverity})}
            />
            <ToggleRow 
              label="Daily Summary Digest" 
              description="A daily wrap-up of scans and violations."
              checked={notifications.dailyDigest}
              onChange={() => setNotifications({...notifications, dailyDigest: !notifications.dailyDigest})}
            />
            <ToggleRow 
              label="Weekly Analytical Report" 
              description="Detailed trends and KPIs sent every Monday."
              checked={notifications.weeklyReport}
              onChange={() => setNotifications({...notifications, weeklyReport: !notifications.weeklyReport})}
            />
          </CardBody>
        </Card>

        {/* Appearance */}
        <Card className="col-span-1 md:col-span-1 lg:col-span-6">
          <CardHeader actions={<Monitor className="w-4 h-4 text-text-muted" />}>Appearance</CardHeader>
          <CardBody className="space-y-6">
             <div>
               <div className="text-xs font-bold text-text-primary mb-3">Theme Preference</div>
               <div className="flex gap-4">
                 <button className="flex-1 flex flex-col items-center gap-2 p-4 rounded-xl border-2 border-primary bg-primary-light/5 transition-colors">
                   <Sun className="w-6 h-6 text-primary" />
                   <span className="text-xs font-bold text-primary">Light Mode</span>
                 </button>
                 <button className="flex-1 flex flex-col items-center gap-2 p-4 rounded-xl border-2 border-border-subtle bg-canvas hover:border-border-strong transition-colors opacity-50 cursor-not-allowed">
                   <Moon className="w-6 h-6 text-text-muted" />
                   <span className="text-xs font-bold text-text-muted">Dark Mode (Coming Soon)</span>
                 </button>
               </div>
             </div>
          </CardBody>
        </Card>

      </GridContainer>
    </div>
  );
}

function CapabilityRow({ label, granted }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-border-subtle last:border-0">
      <span className="text-sm font-medium text-text-secondary">{label}</span>
      {granted ? (
        <span className="text-[10px] font-bold uppercase tracking-widest text-status-ok-text bg-status-ok-bg px-2 py-0.5 rounded border border-status-ok-border">Granted</span>
      ) : (
        <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted bg-canvas px-2 py-0.5 rounded border border-border-subtle">Denied</span>
      )}
    </div>
  );
}

function ToggleRow({ label, description, checked, onChange }) {
  return (
    <div className="flex items-start justify-between py-2">
      <div className="pr-4">
        <div className="text-sm font-bold text-text-primary">{label}</div>
        <div className="text-xs font-medium text-text-muted mt-0.5">{description}</div>
      </div>
      <button 
        onClick={onChange}
        className={`w-12 h-6 rounded-full shrink-0 transition-colors relative ${checked ? 'bg-primary' : 'bg-border-strong'}`}
      >
        <div className={`absolute top-1 bg-white w-4 h-4 rounded-full transition-all shadow-sm ${checked ? 'left-7' : 'left-1'}`}></div>
      </button>
    </div>
  );
}

export default SettingsPage;
