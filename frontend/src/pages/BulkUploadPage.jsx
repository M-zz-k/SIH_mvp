import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Download, Upload } from 'lucide-react';
import { fetchInspections } from '../services/api';
import { GridContainer, Card, CardHeader, CardBody, StatusChip } from '../components/Primitives';

function BulkUploadPage() {
  const navigate = useNavigate();
  const [data, setData] = useState([]);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    fetchInspections().then(res => setData(res));
  }, []);

  return (
    <div className="flex flex-col gap-6">
      
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Bulk Ingestion</h1>
          <p className="text-[11px] text-text-muted mt-1 uppercase tracking-widest font-bold">Req 1: Drag-drop CSV/ZIP + Live Queue</p>
        </div>
      </div>

      <GridContainer>
        <Card className="col-span-1 md:col-span-1 lg:col-span-5 flex flex-col h-[600px]">
          <CardHeader>Upload Batch</CardHeader>
          <CardBody className="flex flex-col gap-6">
             <div 
              className={`flex-1 border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-6 text-center transition-all ${
                isDragging ? 'border-primary bg-primary-light/10' : 'border-border-strong hover:border-text-muted bg-canvas'
              }`}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => { e.preventDefault(); setIsDragging(false); }}
            >
               <Upload className="w-10 h-10 text-text-muted mb-4" />
               <div className="text-sm font-bold text-text-primary">Drag & Drop CSV / ZIP</div>
               <div className="text-xs text-text-secondary mt-1 mb-4">E-commerce listings or batch field photos</div>
               <button className="px-4 py-2 bg-card border border-border-strong text-text-secondary rounded-lg text-sm font-bold shadow-sm hover:bg-canvas transition-colors">
                 Browse Files
               </button>
             </div>
             
             <div className="p-4 bg-primary-light/10 border border-primary/20 rounded-xl">
               <div className="flex justify-between text-xs font-bold text-primary-dark mb-2">
                 <span>Batch processing...</span>
                 <span>78%</span>
               </div>
               <div className="w-full bg-primary-light/30 rounded-full h-2">
                 <div className="bg-primary h-2 rounded-full" style={{ width: '78%' }}></div>
               </div>
               <div className="flex justify-between text-[10px] font-bold text-primary uppercase tracking-widest mt-2">
                 <span>Parsing → Queuing → Rule Engine</span>
                 <span>45/58 Items</span>
               </div>
             </div>
          </CardBody>
        </Card>

        <Card className="col-span-1 md:col-span-1 lg:col-span-7 flex flex-col h-[600px]">
          <CardHeader actions={
            <button className="text-xs font-bold text-text-secondary flex items-center gap-1 hover:text-text-primary bg-canvas px-3 py-1.5 rounded-lg transition-colors">
              <Download className="w-3.5 h-3.5" /> Export Results
            </button>
          }>
            Processed Results Stream
          </CardHeader>
          <CardBody noPadding className="overflow-y-auto">
             {data.map((item) => (
               <div key={item.id} onClick={() => navigate(`/inspection/${item.id}`)} className="flex items-start gap-4 p-4 border-b border-border-subtle hover:bg-canvas cursor-pointer transition-colors group">
                 <div className="w-12 h-12 rounded-lg bg-canvas border border-border-subtle overflow-hidden shrink-0">
                    <img src={item.image} alt="thumb" className="w-full h-full object-cover" />
                 </div>
                 <div className="flex-1 min-w-0">
                   <div className="flex items-center justify-between mb-1">
                     <span className="text-[11px] font-bold text-text-muted uppercase tracking-widest">{item.id}</span>
                     <StatusChip 
                       status={item.status === 'Likely Compliant' ? 'compliant' : item.status === 'Needs Officer Review' ? 'review' : 'violation'} 
                       label={item.status === 'Likely Compliant' ? 'Compliant' : item.status === 'Needs Officer Review' ? 'Review' : 'Flagged'} 
                     />
                   </div>
                   <div className="text-sm font-bold text-text-primary truncate">{item.productName}</div>
                   <div className="text-xs text-text-secondary truncate">{item.brand} • {item.marketplace}</div>
                   {item.violationType && (
                     <div className="text-[10px] font-bold text-status-err-text mt-2 bg-status-err-bg inline-block px-2 py-0.5 rounded border border-status-err-border">
                       {item.violationType}
                     </div>
                   )}
                 </div>
               </div>
             ))}
          </CardBody>
        </Card>
      </GridContainer>
    </div>
  );
}

export default BulkUploadPage;
