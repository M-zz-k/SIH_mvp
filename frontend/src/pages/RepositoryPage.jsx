import React, { useEffect, useState } from 'react';
import { Search, Filter, Download } from 'lucide-react';
import { fetchInspections } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { GridContainer, Card, CardHeader, CardBody, StatusChip } from '../components/Primitives';

function RepositoryPage() {
  const [data, setData] = useState([]);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('All');
  const navigate = useNavigate();

  useEffect(() => {
    fetchInspections().then((res) => setData(res));
  }, []);

  const filteredData = data.filter(item => {
    const matchesSearch = item.productName.toLowerCase().includes(search.toLowerCase()) || 
                          item.id.toLowerCase().includes(search.toLowerCase()) ||
                          item.brand.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = filterStatus === 'All' || item.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="flex flex-col gap-6">
      
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Repository (Req 7 & 10)</h1>
          <p className="text-[11px] text-text-muted mt-1 uppercase tracking-widest font-bold">Searchable Dossier Archive</p>
        </div>
        <button className="px-4 py-2 bg-card text-text-secondary border border-border-subtle text-sm font-bold rounded-xl hover:bg-canvas transition-colors shadow-sm flex items-center justify-center gap-2">
           <Download className="w-4 h-4 text-text-muted" /> Export CSV
        </button>
      </div>

      <Card>
        <CardBody className="flex flex-col lg:flex-row lg:items-center gap-4">
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Search className="w-5 h-5 text-text-muted" />
            </div>
            <input 
              type="text" 
              placeholder="Search by Docket ID, Brand, or Keyword..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-canvas border border-border-subtle rounded-xl text-sm font-medium shadow-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
            />
          </div>
          
          <div className="flex items-center gap-3">
            <Filter className="w-5 h-5 text-text-muted" />
            <select 
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-card border border-border-subtle rounded-xl text-sm py-3 px-4 shadow-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-text-secondary font-bold min-w-[160px]"
            >
              <option value="All">All Statuses</option>
              <option value="Likely Compliant">Compliant</option>
              <option value="Needs Officer Review">Review Pending</option>
              <option value="Likely Violation">Violation</option>
            </select>
          </div>
        </CardBody>
      </Card>

      <GridContainer>
        {filteredData.length === 0 ? (
          <Card className="col-span-1 md:col-span-2 lg:col-span-12 py-20 text-center text-text-muted bg-canvas">
            <p className="font-bold text-sm tracking-wide">No dossiers match your criteria.</p>
          </Card>
        ) : (
          filteredData.map((item) => (
            <Card 
              key={item.id} 
              className="col-span-1 md:col-span-1 lg:col-span-4 xl:col-span-3 hover:border-primary hover:shadow-md transition-all cursor-pointer group h-auto"
            >
              <div className="h-full flex flex-col" onClick={() => navigate(`/inspection/${item.id}`)}>
                <CardBody className="flex flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between mb-4">
                      <StatusChip 
                        status={item.status === 'Likely Compliant' ? 'compliant' : item.status === 'Needs Officer Review' ? 'review' : 'violation'}
                        label={item.status === 'Likely Compliant' ? 'Resolved' : item.status === 'Needs Officer Review' ? 'Pending' : 'Violation'}
                      />
                      <span className="text-[11px] font-mono font-bold text-text-muted border border-border-subtle bg-canvas px-2 py-0.5 rounded-md">
                        {item.id}
                      </span>
                    </div>
                    
                    {/* Task 4: Show a small thumbnail per card */}
                    <div className="w-full h-32 rounded-lg bg-canvas border border-border-subtle overflow-hidden mb-4 flex items-center justify-center p-2 relative">
                       {item.evidenceImages && item.evidenceImages.length > 0 ? (
                         <>
                           <img src={item.evidenceImages[0].url} className="max-w-full max-h-full object-contain group-hover:scale-105 transition-transform" />
                           {item.evidenceImages.length > 1 && (
                             <div className="absolute bottom-2 right-2 bg-text-primary/70 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
                               +{item.evidenceImages.length - 1} photos
                             </div>
                           )}
                         </>
                       ) : (
                         <img src={item.image} className="max-w-full max-h-full object-contain group-hover:scale-105 transition-transform" />
                       )}
                    </div>

                    <h3 className="font-bold text-text-primary text-sm line-clamp-1 mb-1">{item.brand}</h3>
                    <p className="text-xs text-text-secondary font-medium line-clamp-1 mb-4">{item.productName}</p>
                  </div>
                  
                  <div className="pt-4 border-t border-border-subtle mt-auto flex items-center justify-between">
                    {item.violationType ? (
                      <div className="text-[10px] font-bold text-status-err-text line-clamp-1 uppercase tracking-widest bg-status-err-bg border border-status-err-border px-2 py-1 rounded">
                        {item.violationType}
                      </div>
                    ) : (
                      <div className="text-[10px] font-bold text-status-ok-text line-clamp-1 uppercase tracking-widest bg-status-ok-bg border border-status-ok-border px-2 py-1 rounded">
                        Compliant
                      </div>
                    )}
                  </div>
                </CardBody>
              </div>
            </Card>
          ))
        )}
      </GridContainer>
    </div>
  );
}

export default RepositoryPage;
