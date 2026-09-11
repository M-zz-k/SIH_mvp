import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Download, Upload } from 'lucide-react';
import { fetchInspections, addInspection } from '../services/api';
import { GridContainer, Card, CardHeader, CardBody, StatusChip } from '../components/Primitives';

function BulkUploadPage() {
  const navigate = useNavigate();
  const [data, setData] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStats, setUploadStats] = useState({ current: 0, total: 0 });
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchInspections().then(res => setData(res));
  }, []);

  const handleFilesSelected = (e) => {
    const files = Array.from(e.target.files || e.dataTransfer.files);
    if (files.length === 0) return;
    simulateUpload(files);
  };

  const simulateUpload = (files) => {
    setIsUploading(true);
    setUploadProgress(0);
    setUploadStats({ current: 0, total: files.length });
    
    let current = 0;
    const interval = setInterval(async () => {
      current++;
      setUploadProgress(Math.round((current / files.length) * 100));
      setUploadStats({ current, total: files.length });
      
      const isViol = Math.random() > 0.5;
      const mockEntry = {
        id: `BCH-${Math.floor(Math.random()*10000)}`,
        date: new Date().toISOString().split('T')[0],
        status: isViol ? 'Likely Violation' : 'Likely Compliant',
        violationType: isViol ? 'Rule 6(1)(a) Missing Details' : null,
        productName: files[current-1].name,
        brand: 'Uploaded Batch',
        marketplace: 'Local Device',
        category: 'Scanned',
        image: 'https://placehold.co/400x400/E9EEF4/1B2B44?text=Uploaded+File'
      };
      
      const added = await addInspection(mockEntry);
      setData(prev => [added, ...prev]);
      
      if (current >= files.length) {
        clearInterval(interval);
        setTimeout(() => setIsUploading(false), 1500);
      }
    }, 1200);
  };

  const handleExportCSV = () => {
    if (!data || data.length === 0) return;
    const headers = ['Docket ID', 'Brand', 'Product', 'Status', 'Violation Type', 'Date'];
    const csvContent = [
      headers.join(','),
      ...data.map(item => [
        `"${item.id}"`,
        `"${item.brand || ''}"`,
        `"${item.productName || ''}"`,
        `"${item.status || ''}"`,
        `"${item.violationType || ''}"`,
        `"${item.date || ''}"`
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `bulk_results_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

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
              } ${isUploading ? 'opacity-50 pointer-events-none' : 'cursor-pointer'}`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => { e.preventDefault(); setIsDragging(false); handleFilesSelected(e); }}
            >
               <input type="file" multiple ref={fileInputRef} className="hidden" onChange={handleFilesSelected} />
               <Upload className="w-10 h-10 text-text-muted mb-4" />
               <div className="text-sm font-bold text-text-primary">Drag & Drop CSV / ZIP / Images</div>
               <div className="text-xs text-text-secondary mt-1 mb-4">Click here or drag files to upload</div>
               <button className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-bold shadow-sm hover:bg-primary-dark transition-colors" onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}>
                 Browse Files
               </button>
             </div>
             
             {isUploading && (
               <div className="p-4 bg-primary-light/10 border border-primary/20 rounded-xl animate-in fade-in slide-in-from-bottom-2 duration-300">
                 <div className="flex justify-between text-xs font-bold text-primary-dark mb-2">
                   <span>Processing {uploadStats.current} of {uploadStats.total}...</span>
                   <span>{uploadProgress}%</span>
                 </div>
                 <div className="w-full bg-primary-light/30 rounded-full h-2">
                   <div className="bg-primary h-2 rounded-full transition-all duration-500" style={{ width: `${uploadProgress}%` }}></div>
                 </div>
                 <div className="flex justify-between text-[10px] font-bold text-primary uppercase tracking-widest mt-2">
                   <span className="animate-pulse">Parsing → Rule Engine</span>
                   <span>{uploadStats.current}/{uploadStats.total} Items</span>
                 </div>
               </div>
             )}
          </CardBody>
        </Card>

        <Card className="col-span-1 md:col-span-1 lg:col-span-7 flex flex-col h-[600px]">
          <CardHeader actions={
            <button onClick={handleExportCSV} className="text-xs font-bold text-white flex items-center gap-1 hover:bg-secondary-dark bg-secondary px-3 py-1.5 rounded-lg transition-colors shadow-sm">
              <Download className="w-3.5 h-3.5" /> Export Results
            </button>
          }>
            Processed Results Stream
          </CardHeader>
          <CardBody noPadding className="overflow-y-auto">
             {data.map((item) => (
               <div key={item.id} onClick={() => navigate(`/inspection/${item.id}`)} className="flex items-start gap-4 p-4 border-b border-border-subtle hover:bg-canvas cursor-pointer transition-colors group">
                 <div className="w-12 h-12 rounded-lg bg-canvas border border-border-subtle overflow-hidden shrink-0">
                    <img 
                      src={item.image} 
                      onError={(e) => e.target.src = "https://placehold.co/150x150/E9EEF4/1B2B44?text=Img"}
                      alt="thumb" 
                      className="w-full h-full object-cover" 
                    />
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
