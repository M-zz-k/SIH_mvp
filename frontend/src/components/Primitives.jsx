import React from 'react';
import { MoreVertical } from 'lucide-react';

export function GridContainer({ children, className = '' }) {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-4 md:gap-6 ${className}`}>
      {children}
    </div>
  );
}

export function Card({ children, className = '' }) {
  return (
    <div className={`bg-card border border-border-subtle rounded-2xl flex flex-col overflow-hidden ${className}`}>
      {children}
    </div>
  );
}

export function CardHeader({ children, actions, className = '' }) {
  return (
    <div className={`px-6 py-5 border-b border-border-subtle flex items-center justify-between shrink-0 bg-card ${className}`}>
      <div className="flex-1 font-bold text-text-primary text-sm tracking-tight">{children}</div>
      {actions && <div className="flex items-center gap-3 shrink-0 ml-4">{actions}</div>}
    </div>
  );
}

export function CardBody({ children, noPadding = false, className = '' }) {
  return (
    <div className={`flex-1 overflow-auto flex flex-col ${noPadding ? '' : 'p-6'} ${className}`}>
      {children}
    </div>
  );
}

export function StatusChip({ status, label }) {
  const statusMap = {
    'compliant': 'chip-compliant',
    'review': 'chip-review',
    'violation': 'chip-violation'
  };
  
  return (
    <span className={`chip ${statusMap[status] || 'chip-review'}`}>
      {label}
    </span>
  );
}

export function StatValue({ value, label, trend, trendDir = 'up' }) {
  return (
    <div>
      <div className="text-[11px] font-semibold text-text-muted uppercase tracking-widest mb-2">{label}</div>
      <div className="flex items-end gap-3">
        <span className="text-3xl font-bold text-text-primary tracking-tight leading-none">{value}</span>
        {trend && (
          <span className={`text-[11px] font-bold px-1.5 py-0.5 rounded-md flex items-center border ${
            trendDir === 'up' ? 'bg-status-ok-bg text-status-ok-text border-status-ok-border' : 
            trendDir === 'down' ? 'bg-status-review-bg text-status-review-text border-status-review-border' :
            'bg-status-err-bg text-status-err-text border-status-err-border'
          }`}>
            {trend}
          </span>
        )}
      </div>
    </div>
  );
}

export function ListRow({ icon: Icon, title, subtitle, status, statusLabel, date, onClick }) {
  return (
    <div onClick={onClick} className="flex items-center gap-4 px-6 py-4 hover:bg-canvas border-b border-border-subtle last:border-0 cursor-pointer transition-colors group h-16">
      <input type="checkbox" className="w-4 h-4 rounded border-border-strong text-primary focus:ring-primary" onClick={(e) => e.stopPropagation()} />
      <div className="w-8 h-8 rounded-full bg-canvas flex items-center justify-center shrink-0 text-text-muted group-hover:bg-primary-light/20 group-hover:text-primary transition-colors">
        <Icon className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0 flex items-center justify-between">
        <div className="flex flex-col">
          <span className="text-[13px] font-bold text-text-primary line-clamp-1">{title}</span>
          <span className="text-[11px] font-medium text-text-secondary line-clamp-1">{subtitle}</span>
        </div>
        <div className="flex items-center gap-6 shrink-0">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${
              status === 'compliant' ? 'bg-status-ok-text' : 
              status === 'review' ? 'bg-status-review-text' : 'bg-status-err-text'
            }`}></span>
            <span className="text-[11px] font-bold text-text-secondary hidden sm:block w-16">{statusLabel}</span>
          </div>
          <span className="text-[11px] font-bold text-text-muted hidden sm:block w-24 text-right">{date}</span>
          <button className="text-text-muted hover:text-text-secondary p-1" onClick={(e) => e.stopPropagation()}>
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
