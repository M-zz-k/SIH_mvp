import React from 'react';
import { GridContainer, Card, CardHeader, CardBody, StatValue } from '../components/Primitives';
import { BarChart3, TrendingUp, TrendingDown, MapPin, Download } from 'lucide-react';

function AnalyticsPage() {
  return (
    <div className="flex flex-col gap-6">
      
      {/* Top Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Regional Analytics & Trends</h1>
          <p className="text-[11px] text-text-muted mt-1 uppercase tracking-widest font-bold">Enforcement Data Visualization</p>
        </div>
        <div className="flex gap-3">
          <select className="bg-card border border-border-subtle rounded-lg px-4 py-2 text-sm font-bold shadow-sm focus:outline-none focus:border-primary text-text-secondary">
            <option>All Regions</option>
            <option>North Zone</option>
            <option>West Zone</option>
          </select>
          <select className="bg-card border border-border-subtle rounded-lg px-4 py-2 text-sm font-bold shadow-sm focus:outline-none focus:border-primary text-text-secondary">
            <option>Last 30 Days</option>
            <option>Q3 2026</option>
            <option>YTD</option>
          </select>
          <button className="px-4 py-2 bg-primary text-white text-sm font-bold rounded-lg shadow-sm hover:bg-primary-dark transition-colors flex items-center gap-2">
            <Download className="w-4 h-4" /> Export
          </button>
        </div>
      </div>

      <GridContainer>
        
        {/* KPI Row */}
        <Card className="col-span-1 md:col-span-1 lg:col-span-4">
          <CardBody>
            <div className="flex items-start justify-between mb-2">
              <div className="p-2 bg-primary-light/10 text-primary-dark rounded-lg">
                <BarChart3 className="w-5 h-5" />
              </div>
            </div>
            <StatValue label="Total Non-Compliant Products" value="12,482" trend="-8%" trendDir="up" />
          </CardBody>
        </Card>

        <Card className="col-span-1 md:col-span-1 lg:col-span-4">
          <CardBody>
            <div className="flex items-start justify-between mb-2">
              <div className="p-2 bg-status-err-bg text-status-err-text rounded-lg">
                <TrendingUp className="w-5 h-5" />
              </div>
            </div>
            <StatValue label="Repeat Offenders" value="482" trend="+12%" trendDir="down" />
          </CardBody>
        </Card>

        <Card className="col-span-1 md:col-span-2 lg:col-span-4">
          <CardBody>
            <div className="flex items-start justify-between mb-2">
              <div className="p-2 bg-status-ok-bg text-status-ok-text rounded-lg">
                <TrendingDown className="w-5 h-5" />
              </div>
            </div>
            <StatValue label="Average Resolution Time" value="4.2 Days" trend="-1.5 Days" trendDir="up" />
          </CardBody>
        </Card>

        {/* Charts Row */}
        <Card className="col-span-1 md:col-span-2 lg:col-span-8 min-h-[400px]">
          <CardHeader>
            <span className="text-[11px] font-bold uppercase tracking-widest text-text-muted">Violations by Rule Categories Over Time</span>
          </CardHeader>
          <CardBody className="flex flex-col items-center justify-center bg-canvas">
            {/* Simulated Chart */}
            <div className="w-full max-w-2xl h-64 border-b-2 border-l-2 border-border-strong relative flex items-end justify-between px-4 pb-0">
               {/* Grid lines */}
               <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
                 <div className="w-full h-px bg-border-subtle"></div>
                 <div className="w-full h-px bg-border-subtle"></div>
                 <div className="w-full h-px bg-border-subtle"></div>
                 <div className="w-full h-px bg-border-subtle"></div>
               </div>
               
               {/* Bars (Rule 6 vs Rule 12) */}
               <div className="flex gap-1 items-end z-10 w-12 h-[40%]"><div className="w-full h-full bg-primary rounded-t"></div><div className="w-full h-[60%] bg-status-review-text rounded-t"></div></div>
               <div className="flex gap-1 items-end z-10 w-12 h-[55%]"><div className="w-full h-full bg-primary rounded-t"></div><div className="w-full h-[70%] bg-status-review-text rounded-t"></div></div>
               <div className="flex gap-1 items-end z-10 w-12 h-[35%]"><div className="w-full h-full bg-primary rounded-t"></div><div className="w-full h-[80%] bg-status-review-text rounded-t"></div></div>
               <div className="flex gap-1 items-end z-10 w-12 h-[65%]"><div className="w-full h-full bg-primary rounded-t"></div><div className="w-full h-[50%] bg-status-review-text rounded-t"></div></div>
               <div className="flex gap-1 items-end z-10 w-12 h-[80%]"><div className="w-full h-full bg-primary rounded-t"></div><div className="w-full h-[40%] bg-status-review-text rounded-t"></div></div>
               <div className="flex gap-1 items-end z-10 w-12 h-[75%]"><div className="w-full h-full bg-primary rounded-t"></div><div className="w-full h-[45%] bg-status-review-text rounded-t"></div></div>
            </div>
            
            <div className="flex gap-6 mt-6">
              <div className="flex items-center gap-2 text-xs font-bold text-text-secondary"><div className="w-3 h-3 bg-primary rounded-sm"></div> Rule 6 (Declarations)</div>
              <div className="flex items-center gap-2 text-xs font-bold text-text-secondary"><div className="w-3 h-3 bg-status-review-text rounded-sm"></div> Rule 12 (Units)</div>
            </div>
          </CardBody>
        </Card>

        <Card className="col-span-1 md:col-span-2 lg:col-span-4 min-h-[400px]">
          <CardHeader>
            <span className="text-[11px] font-bold uppercase tracking-widest text-text-muted flex items-center gap-2"><MapPin className="w-3.5 h-3.5 text-primary-dark" /> State-wise Non-Compliance %</span>
          </CardHeader>
          <CardBody>
            <div className="space-y-5">
              {[
                { label: 'Maharashtra', val: 18.2, color: 'bg-status-err-text' },
                { label: 'Delhi NCR', val: 14.5, color: 'bg-status-err-text/80' },
                { label: 'Karnataka', val: 11.1, color: 'bg-status-review-text' },
                { label: 'Gujarat', val: 8.4, color: 'bg-status-review-text/80' },
                { label: 'Tamil Nadu', val: 5.2, color: 'bg-status-ok-text' },
              ].map((item) => (
                <div key={item.label} className="w-full">
                  <div className="flex justify-between text-xs font-bold text-text-primary mb-2">
                    <span>{item.label}</span>
                    <span>{item.val}%</span>
                  </div>
                  <div className="h-2 w-full bg-canvas rounded-full overflow-hidden shadow-inner">
                    <div className={`h-full ${item.color}`} style={{ width: `${item.val * 3}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

      </GridContainer>
    </div>
  );
}

export default AnalyticsPage;
