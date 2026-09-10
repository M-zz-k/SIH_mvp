import React, { useState, useEffect, useMemo } from 'react';
import { fetchInspections } from '../services/api';
import { GridContainer, Card, CardHeader, CardBody, ListRow, StatValue } from '../components/Primitives';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, Activity, ArrowRight, Loader } from 'lucide-react';

function DashboardPage() {
  const navigate = useNavigate();
  const [data, setData] = useState([]);

  useEffect(() => {
    fetchInspections().then(res => setData(res));
  }, []);

  // 1. KPI Calculations
  const totalScans = data.length;
  const compliantCount = data.filter(d => d.status === 'Likely Compliant').length;
  const complianceRate = totalScans ? Math.round((compliantCount / totalScans) * 100) : 0;
  
  const needsReviewCount = data.filter(d => d.status === 'Needs Officer Review').length;
  const violationsCount = data.filter(d => d.status === 'Likely Violation').length;
  
  // 3. Category Breakdown Calculation
  const categoryStats = useMemo(() => {
    const cats = {};
    data.forEach(d => {
      if (!cats[d.category]) cats[d.category] = { total: 0, compliant: 0 };
      cats[d.category].total++;
      if (d.status === 'Likely Compliant') cats[d.category].compliant++;
    });
    return Object.entries(cats).map(([name, stats]) => ({
      name,
      rate: Math.round((stats.compliant / stats.total) * 100),
      total: stats.total
    })).sort((a, b) => b.total - a.total);
  }, [data]);

  // 4. Top Violations Calculation
  const topViolations = useMemo(() => {
    const counts = {};
    data.forEach(d => {
      if (d.violationType) {
        counts[d.violationType] = (counts[d.violationType] || 0) + 1;
      }
    });
    return Object.entries(counts)
      .map(([type, count]) => ({ type, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 4);
  }, [data]);

  // 6. High Priority Alert Calculation
  const urgentItem = data.find(d => d.status === 'Likely Violation' || d.status === 'Needs Officer Review');

  return (
    <div className="flex flex-col gap-6">
      
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Executive Command</h1>
          <p className="text-[11px] text-text-muted mt-1 uppercase tracking-widest font-bold">Real-time Compliance Monitoring</p>
        </div>
      </div>

      <GridContainer>
        
        {/* 1. KPI Row */}
        <Card className="col-span-1 md:col-span-2 lg:col-span-3">
          <CardBody className="flex flex-col items-center justify-center text-center">
             <div className="text-[11px] font-bold text-text-muted uppercase tracking-widest mb-3">Overall Compliance</div>
             <div className="relative w-24 h-24 mb-2">
               <svg viewBox="0 0 36 36" className="w-full h-full text-status-ok-border">
                 <path className="text-canvas" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="4" />
                 <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="4" strokeDasharray={`${complianceRate}, 100`} />
               </svg>
               <div className="absolute inset-0 flex flex-col items-center justify-center">
                 <span className="text-xl font-bold text-text-primary">{complianceRate}%</span>
               </div>
             </div>
             <div className="text-[10px] text-text-secondary font-bold">{totalScans} SKUs Scanned</div>
          </CardBody>
        </Card>

        <Card className="col-span-1 md:col-span-2 lg:col-span-3">
          <CardBody className="flex flex-col justify-center">
            <StatValue label="Needs Review" value={needsReviewCount} />
            <div className="text-[10px] text-text-muted font-medium mt-4">Awaiting officer sign-off</div>
          </CardBody>
        </Card>

        <Card className="col-span-1 md:col-span-2 lg:col-span-3">
          <CardBody className="flex flex-col justify-center">
            <StatValue label="Violations (This Wk)" value={violationsCount} trend="+2%" trendDir="up" />
            <div className="text-[10px] text-text-muted font-medium mt-4">Vs. last week baseline</div>
          </CardBody>
        </Card>

        <Card className="col-span-1 md:col-span-2 lg:col-span-3">
          <CardBody className="flex flex-col justify-center">
            <StatValue label="Active Ingestion Jobs" value={1} trend="Live" trendDir="up" />
            <div className="text-[10px] text-text-muted font-medium mt-4">E-commerce crawler active</div>
          </CardBody>
        </Card>

        {/* 2. Trend Chart */}
        <Card className="col-span-1 md:col-span-2 lg:col-span-8 min-h-[300px] flex flex-col">
          <CardHeader actions={
            <select className="bg-canvas border border-border-subtle rounded-md px-2 py-1 text-[11px] font-bold text-text-secondary outline-none">
               <option>Last 30 Days</option>
               <option>Last 7 Days</option>
               <option>Today</option>
            </select>
          }>
            Scans vs Violations
          </CardHeader>
          <CardBody className="flex flex-col justify-end relative pt-8">
            <div className="absolute top-4 right-6 flex gap-4">
              <div className="flex items-center gap-2 text-[10px] font-bold text-text-muted uppercase tracking-widest"><span className="w-2 h-2 rounded-full bg-primary"></span> Total Scans</div>
              <div className="flex items-center gap-2 text-[10px] font-bold text-text-muted uppercase tracking-widest"><span className="w-2 h-2 rounded-full bg-status-err-border"></span> Violations</div>
            </div>
            
            <div className="w-full h-40 border-b-2 border-border-subtle flex items-end justify-between px-2 sm:px-6">
              {/* Simulated bars */}
              {[60, 45, 80, 50, 95, 75, 40].map((h, i) => (
                <div key={i} className="flex gap-1 items-end h-full">
                  <div className="w-4 sm:w-6 rounded-t-sm bg-primary transition-all hover:opacity-80" style={{ height: `${h}%` }}></div>
                  <div className="w-4 sm:w-6 rounded-t-sm bg-status-err-border transition-all hover:opacity-80" style={{ height: `${h * 0.3}%` }}></div>
                </div>
              ))}
            </div>
            <div className="w-full flex justify-between px-2 sm:px-6 mt-3 text-[10px] font-bold text-text-muted uppercase tracking-widest">
              <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
            </div>
          </CardBody>
        </Card>

        {/* 3. Category Breakdown */}
        <Card className="col-span-1 md:col-span-2 lg:col-span-4 min-h-[300px] flex flex-col">
          <CardHeader>Compliance by Category</CardHeader>
          <CardBody className="flex flex-col gap-4">
            {categoryStats.map(cat => (
              <div 
                key={cat.name} 
                className="group cursor-pointer" 
                onClick={() => navigate('/repository')}
              >
                <div className="flex justify-between text-xs font-bold text-text-primary mb-1 group-hover:text-primary transition-colors">
                  <span>{cat.name}</span>
                  <span>{cat.rate}%</span>
                </div>
                <div className="w-full bg-canvas rounded-full h-2 overflow-hidden border border-border-subtle">
                  <div className={`h-full ${cat.rate > 80 ? 'bg-status-ok-text' : cat.rate > 50 ? 'bg-status-review-text' : 'bg-status-err-text'}`} style={{ width: `${cat.rate}%` }}></div>
                </div>
              </div>
            ))}
          </CardBody>
        </Card>

        {/* 4. Top Violations & 5. Active Ingestion & 6. High Priority */}
        <div className="col-span-1 md:col-span-2 lg:col-span-4 flex flex-col gap-6">
          <Card className="flex-1">
            <CardHeader>Top Violations (This Period)</CardHeader>
            <CardBody className="flex flex-col gap-3">
              {topViolations.map((v, i) => (
                <div key={i} className="flex justify-between items-center text-xs font-bold p-3 bg-canvas rounded-xl border border-border-subtle">
                  <span className="text-text-secondary truncate pr-4">{v.type}</span>
                  <span className="text-text-primary bg-card px-2 py-1 rounded shadow-sm border border-border-subtle shrink-0">{v.count} cases</span>
                </div>
              ))}
              {topViolations.length === 0 && <div className="text-xs text-text-muted font-bold text-center py-4">No violations recorded.</div>}
            </CardBody>
          </Card>
        </div>

        <div className="col-span-1 md:col-span-2 lg:col-span-4 flex flex-col gap-6">
          <Card className="flex-1 bg-primary text-white border-0">
            <CardBody className="flex flex-col justify-center">
              <div className="flex items-center gap-3 mb-2">
                <Loader className="w-5 h-5 animate-spin text-primary-light" />
                <h3 className="font-bold text-sm tracking-widest uppercase">Active Ingestion</h3>
              </div>
              <p className="text-xs text-primary-light font-medium mb-6">Processing E-commerce Batch #9921</p>
              
              <div className="w-full bg-primary-dark rounded-full h-2 mb-2">
                <div className="bg-white h-2 rounded-full w-[78%]"></div>
              </div>
              <div className="flex justify-between text-[10px] font-bold text-primary-light uppercase tracking-widest mb-4">
                <span>78% Complete</span>
                <span>45/58</span>
              </div>
              
              <button onClick={() => navigate('/bulk-upload')} className="w-full py-2 bg-white text-primary text-xs font-bold rounded-lg hover:bg-canvas transition-colors flex items-center justify-center gap-2">
                View Queue <ArrowRight className="w-3 h-3" />
              </button>
            </CardBody>
          </Card>
        </div>

        <div className="col-span-1 md:col-span-2 lg:col-span-4 flex flex-col gap-6">
          {urgentItem ? (
            <Card className="flex-1 border-status-err-border bg-status-err-bg shadow-sm">
              <CardBody className="flex flex-col justify-center">
                <div className="flex items-start gap-3 mb-4">
                  <div className="p-2 bg-white rounded-lg border border-status-err-border shrink-0">
                    <ShieldAlert className="w-6 h-6 text-status-err-text" />
                  </div>
                  <div>
                    <h3 className="font-bold text-status-err-text text-sm">High Priority Alert</h3>
                    <p className="text-xs text-status-err-text/80 font-medium mt-1">
                      {urgentItem.violationType || 'Unresolved Violation'} detected on major SKU.
                    </p>
                  </div>
                </div>
                <div className="p-3 bg-white/60 rounded-lg border border-status-err-border/50 text-xs font-bold text-text-primary mb-4 truncate">
                  {urgentItem.brand} - {urgentItem.productName}
                </div>
                <button onClick={() => navigate(`/inspection/${urgentItem.id}`)} className="w-full py-2 bg-status-err-text text-white text-xs font-bold rounded-lg hover:bg-status-err-text/90 transition-colors">
                  Review Now
                </button>
              </CardBody>
            </Card>
          ) : (
            <Card className="flex-1">
              <CardBody className="flex flex-col items-center justify-center text-center">
                <Activity className="w-8 h-8 text-status-ok-text mb-3" />
                <h3 className="font-bold text-text-primary text-sm">No Urgent Alerts</h3>
                <p className="text-xs text-text-muted mt-1">All high-priority items resolved.</p>
              </CardBody>
            </Card>
          )}
        </div>

      </GridContainer>
    </div>
  );
}

export default DashboardPage;
