import React, { useState, useEffect, useMemo } from 'react';
import { fetchInspections } from '../services/api';
import { GridContainer, Card, CardHeader, CardBody, ListRow, StatValue } from '../components/Primitives';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, Activity, ArrowRight, Loader, Pause, Play, Clock, Search, AlertTriangle } from 'lucide-react';

function DashboardPage() {
  const navigate = useNavigate();
  const [data, setData] = useState([]);
  const [isLive, setIsLive] = useState(true);
  const [time, setTime] = useState(new Date());
  const [processedCount, setProcessedCount] = useState(37);
  const [feedItems, setFeedItems] = useState([
    { id: 1, time: new Date(Date.now() - 1000 * 45), text: 'SKU-IN-104 (Blinkit) - Flagged: Rule 12 Non-Standard Unit (\'mltr\')', type: 'violation' },
    { id: 2, time: new Date(Date.now() - 1000 * 120), text: 'SKU-IN-103 (Zepto) - Auto-Cleared: Fully Compliant', type: 'compliant' },
    { id: 3, time: new Date(Date.now() - 1000 * 200), text: 'Officer Verma uploaded Field Scan (Atta 5kg) - Queued for OCR', type: 'info' }
  ]);

  useEffect(() => {
    fetchInspections().then(res => setData(res));
  }, []);

  useEffect(() => {
    let timer;
    if (isLive) {
      timer = setInterval(() => {
        setTime(new Date());
        
        // Simulate processing
        if (Math.random() > 0.3) {
           setProcessedCount(prev => (prev < 50 ? prev + 1 : 12));
        }

        // Simulate incoming event
        if (Math.random() > 0.8) {
          setFeedItems(prev => {
            const isVi = Math.random() > 0.6;
            const newItem = {
              id: Date.now(),
              time: new Date(),
              text: `SKU-IN-${Math.floor(Math.random() * 100 + 200)} (Amazon) - ${!isVi ? 'Auto-Cleared: Fully Compliant' : 'Flagged: Rule 6(1)(e)'}`,
              type: !isVi ? 'compliant' : 'violation'
            };
            return [newItem, ...prev].slice(0, 5);
          });
        }
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isLive]);

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
      
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Dashboard</h1>
          <div className="flex flex-wrap items-center gap-4 mt-2">
            <p className="text-[11px] text-text-muted uppercase tracking-widest font-bold">Real-time Compliance Monitoring</p>
            {/* Live Telemetry Ping */}
            <div className="flex items-center gap-2 bg-card border border-border-subtle px-3 py-1 rounded-full shadow-sm">
               <div className="relative flex h-2.5 w-2.5">
                 {isLive && <div className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 animate-ping"></div>}
                 <div className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isLive ? 'bg-emerald-500' : 'bg-status-err-text'}`}></div>
               </div>
               <span className="text-[10px] font-bold text-text-primary tracking-wider uppercase">
                 {isLive ? 'Live Feed Active' : 'Feed Paused'}
               </span>
               <span className="text-[10px] text-text-muted px-2 border-l border-border-subtle hidden sm:inline">Worker Pool: 4/4 Online</span>
               <span className="text-[10px] text-text-muted px-2 border-l border-border-subtle hidden sm:inline">Auto-refresh: 15s</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-card border border-border-subtle px-4 py-2 rounded-xl shadow-sm text-xs font-bold text-text-primary">
            <Clock className="w-4 h-4 text-primary" />
            Live Surveillance Time: {time.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false })} IST
          </div>
          <button 
            onClick={() => setIsLive(!isLive)}
            className="p-2 bg-card border border-border-subtle rounded-xl hover:bg-canvas transition-colors shadow-sm"
            title={isLive ? "Pause Stream" : "Resume Stream"}
          >
            {isLive ? <Pause className="w-4 h-4 text-text-secondary" /> : <Play className="w-4 h-4 text-status-err-text" />}
          </button>
        </div>
      </div>

      <GridContainer>
        
        {/* 1. KPI Row */}
        <Card className="col-span-1 md:col-span-2 lg:col-span-3">
          <CardBody className="flex flex-col items-center justify-center text-center">
             <div className="text-[11px] font-bold text-text-muted uppercase tracking-widest mb-3">Overall Compliance</div>
             <div className="relative w-24 h-24 mb-2">
               <svg viewBox="0 0 36 36" className="w-full h-full text-canvas">
                 <path className="text-border-subtle" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="4" />
                 <path className="text-status-ok-text" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="4" strokeDasharray={`${complianceRate}, 100`} />
               </svg>
               <div className="absolute inset-0 flex flex-col items-center justify-center">
                 <span className="text-xl font-bold text-text-primary">{complianceRate}%</span>
               </div>
             </div>
             <div className="text-[10px] text-text-primary font-bold flex items-center justify-center gap-1 mt-2">
               {totalScans} SKUs Scanned
             </div>
          </CardBody>
        </Card>

        <Card className="col-span-1 md:col-span-2 lg:col-span-3">
          <CardBody className="flex flex-col justify-center">
            <StatValue label="Needs Review" value={needsReviewCount} />
            <div className="text-[10px] text-text-muted font-bold mt-4">Awaiting officer sign-off</div>
          </CardBody>
        </Card>

        <Card className="col-span-1 md:col-span-2 lg:col-span-3">
          <CardBody className="flex flex-col justify-center">
            <StatValue label="Violations (This Wk)" value={violationsCount} trend="+2%" trendDir="up" />
            <div className="text-[10px] text-text-muted font-bold mt-4">Vs. last week baseline</div>
          </CardBody>
        </Card>

        <Card className="col-span-1 md:col-span-2 lg:col-span-3">
          <CardBody className="flex flex-col justify-center">
            <StatValue label="Active Ingestion Jobs" value={1} trend="Live" trendDir="up" />
            <div className="text-[10px] text-text-muted font-bold mt-4">E-commerce crawler active</div>
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
              <div className="flex items-center gap-2 text-[10px] font-bold text-text-muted uppercase tracking-widest"><span className="w-2 h-2 rounded-full bg-secondary"></span> Total Scans</div>
              <div className="flex items-center gap-2 text-[10px] font-bold text-text-muted uppercase tracking-widest"><span className="w-2 h-2 rounded-full bg-status-err-border"></span> Violations</div>
            </div>
            
            <div className="w-full h-40 border-b-2 border-border-subtle flex items-end justify-between px-2 sm:px-6">
              {/* Simulated bars */}
              {[60, 45, 80, 50, 95, 75, 40].map((h, i) => (
                <div key={i} className="flex gap-1 items-end h-full">
                  <div className="w-4 sm:w-6 rounded-t-sm bg-secondary transition-all hover:opacity-80" style={{ height: `${h}%` }}></div>
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
          <Card className="flex-1 bg-primary text-white border-0 flex flex-col h-[380px]">
            <CardBody className="flex flex-col justify-center h-full">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Loader className="w-5 h-5 animate-spin text-white" />
                  <h3 className="font-bold text-sm tracking-widest uppercase">Active Ingestion</h3>
                </div>
                <div className="text-[10px] font-bold bg-white/20 px-2 py-1 rounded-full uppercase tracking-widest">
                  ~12 SKUs / sec
                </div>
              </div>
              
              <div className="bg-primary-dark/40 rounded-xl p-3 mb-6">
                <div className="text-[10px] text-white/70 font-bold uppercase tracking-widest mb-1">Current Batch</div>
                <div className="text-sm text-white font-bold font-mono">Blinkit_Staples_Batch_04.csv</div>
              </div>
              
              <div className="w-full bg-primary-dark rounded-full h-2.5 mb-2 overflow-hidden">
                <div className="bg-white h-full rounded-full transition-all duration-500 ease-out relative" style={{ width: `${(processedCount / 50) * 100}%` }}>
                  <div className="absolute inset-0 bg-white/30 animate-pulse"></div>
                </div>
              </div>
              <div className="flex justify-between text-[10px] font-bold text-white uppercase tracking-widest mb-4">
                <span>{Math.round((processedCount / 50) * 100)}% Complete</span>
                <span>{processedCount} / 50 SKUs</span>
              </div>
              
              <div className="text-[10px] font-bold bg-white/10 border border-white/20 text-white px-3 py-1.5 rounded-lg mb-6 flex items-center gap-2 animate-pulse">
                <div className="w-1.5 h-1.5 bg-white rounded-full"></div>
                [Rule Engine: Evaluating Rule 12 & Rule 6(1)(e)]
              </div>
              
              <button onClick={() => navigate('/bulk-upload')} className="w-full py-2 bg-white text-primary text-xs font-bold rounded-lg hover:bg-canvas transition-colors flex items-center justify-center gap-2 mt-auto">
                View Queue <ArrowRight className="w-3 h-3" />
              </button>
            </CardBody>
          </Card>
        </div>

        <div className="col-span-1 md:col-span-2 lg:col-span-4 flex flex-col gap-6">
          <Card className="flex-1 flex flex-col h-[380px]">
            <CardHeader actions={
              <div className="flex items-center gap-1.5 text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 uppercase tracking-widest">
                <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping"></div> Live
              </div>
            }>
              Live Enforcement Stream
            </CardHeader>
            <CardBody noPadding className="flex flex-col overflow-hidden relative">
              <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
                {feedItems.map((item) => (
                  <div key={item.id} className="flex gap-3 text-xs bg-canvas rounded-xl p-3 border border-border-subtle animate-in slide-in-from-top-2 fade-in duration-300">
                    <div className="text-text-muted font-mono shrink-0 font-bold">
                      [{item.time.toLocaleTimeString('en-IN', { hour12: false }).slice(0, 8)}]
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-text-primary mb-1">
                        {item.text.split('-')[0]} <span className="text-text-muted">- {item.text.split('-').slice(1).join('-')}</span>
                      </div>
                      <div className="flex items-center justify-between mt-2">
                        {item.type === 'violation' ? (
                          <span className="text-[9px] font-bold bg-rose-50 text-rose-700 border border-rose-200 px-1.5 py-0.5 rounded uppercase tracking-widest">Rose Badge</span>
                        ) : item.type === 'compliant' ? (
                          <span className="text-[9px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 px-1.5 py-0.5 rounded uppercase tracking-widest">Emerald Badge</span>
                        ) : (
                          <span className="text-[9px] font-bold bg-slate-100 text-slate-700 border border-slate-200 px-1.5 py-0.5 rounded uppercase tracking-widest">Slate Badge</span>
                        )}
                        <button onClick={() => navigate('/inspection/SKU-104')} className="text-[10px] font-bold text-primary hover:underline flex items-center gap-1">
                           Inspect <Search className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-card to-transparent pointer-events-none"></div>
            </CardBody>
          </Card>
        </div>

      </GridContainer>
    </div>
  );
}

export default DashboardPage;
