import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, Download, CheckCircle, 
  AlertTriangle, ShieldAlert, FileSearch, Hash
} from 'lucide-react';
import { fetchInspectionById } from '../services/api';
import { GridContainer, Card, CardHeader, CardBody, StatusChip } from '../components/Primitives';

function InspectionPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchInspectionById(id).then((res) => setData(res));
  }, [id]);

  if (!data) return null;

  return (
    <div className="flex flex-col gap-6">
      
      {/* Action Bar */}
      <div className="flex flex-wrap sm:flex-nowrap items-center justify-between gap-4 shrink-0 bg-card p-4 rounded-2xl border border-border-subtle shadow-sm sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-canvas rounded-lg text-text-muted transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-lg font-bold text-text-primary tracking-tight flex items-center gap-3">
              Dossier: <span className="font-mono text-text-muted">{data.id}</span>
              <StatusChip 
                status={data.status === 'Likely Compliant' ? 'compliant' : data.status === 'Needs Officer Review' ? 'review' : 'violation'}
                label={data.status}
              />
            </h1>
          </div>
        </div>
        
        <div className="flex gap-3 w-full sm:w-auto">
          <button className="flex-1 sm:flex-none px-4 py-2 bg-secondary text-white text-sm font-bold rounded-xl hover:bg-secondary-dark transition-colors shadow-sm flex items-center justify-center gap-2">
            <Download className="w-4 h-4" /> PDF Memo
          </button>
          <button className="flex-1 sm:flex-none px-4 py-2 bg-secondary text-white text-sm font-bold rounded-xl hover:bg-secondary-dark transition-colors shadow-sm flex items-center justify-center gap-2">
            <Download className="w-4 h-4" /> DOCX
          </button>
          <button className="flex-1 sm:flex-none px-6 py-2 bg-primary text-white border border-primary text-sm font-bold rounded-xl hover:bg-primary-dark transition-colors shadow-sm">
            Sign & Issue Notice
          </button>
        </div>
      </div>

      <GridContainer>
        
        {/* Left Panel: Image Viewer with Font Ratio Flags (Requirement 3) */}
        <Card className="col-span-1 md:col-span-1 lg:col-span-6 h-[700px] flex flex-col">
          <CardHeader actions={<FileSearch className="w-4 h-4 text-text-muted" />}>
             Bounding Box Analyzer (Req 3)
          </CardHeader>
          <CardBody noPadding className="bg-canvas relative overflow-hidden flex items-center justify-center border-b border-border-subtle">
             <div className="relative max-w-full max-h-full p-4">
               <img src={data.image} alt={data.productName} className="max-w-full max-h-full object-contain drop-shadow-md rounded" />
               {data.boundingBoxes?.map((box) => (
                <div
                  key={box.id}
                  className={`absolute border-2 ${
                    box.color === 'green' ? 'border-status-ok-text bg-status-ok-bg/40' :
                    box.color === 'red' ? 'border-status-err-text bg-status-err-bg/40' : 'border-status-review-text bg-status-review-bg/40'
                  } group/box shadow-sm transition-all hover:bg-opacity-80 cursor-pointer`}
                  style={{
                    left: `${box.x}%`,
                    top: `${box.y}%`,
                    width: `${box.width}%`,
                    height: `${box.height}%`
                  }}
                >
                  <div className="absolute top-full left-0 mt-1 bg-sidebar text-white text-[11px] font-bold p-2 rounded shadow-xl opacity-0 group-hover/box:opacity-100 whitespace-nowrap z-10 transition-opacity">
                    <div>{box.type}</div>
                    {box.fontRatio && <div className="text-status-review-border mt-0.5">Font Ratio: {box.fontRatio}</div>}
                    {box.details && <div className="text-primary-light font-medium mt-0.5">{box.details}</div>}
                  </div>
                </div>
              ))}
             </div>
          </CardBody>
          
          {/* Evidence Strip (Requirement 6) */}
          <div className="p-4 bg-card shrink-0">
             <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest mb-3">Supporting Evidence (Req 6)</div>
             <div className="flex gap-4 overflow-x-auto">
               {data.evidenceImages?.map((ev, i) => (
                 <div key={ev.id || i} className="flex gap-3 p-2 border border-border-subtle rounded-xl bg-canvas shrink-0 pr-4">
                   <div className="w-12 h-12 rounded bg-card overflow-hidden shrink-0 border border-border-subtle cursor-pointer hover:opacity-80">
                     <img src={ev.url} className="w-full h-full object-cover" />
                   </div>
                   <div className="flex flex-col justify-center">
                     <span className="text-xs font-bold text-text-secondary">Photo_{ev.id}.jpg</span>
                     <span className="text-[10px] font-mono text-text-muted flex items-center gap-1 mt-0.5"><Hash className="w-3 h-3" />{ev.hash}</span>
                   </div>
                 </div>
               ))}
             </div>
          </div>
        </Card>

        {/* Right Panel: Declarations & Checklist (Requirements 2 & 4) */}
        <div className="col-span-1 md:col-span-1 lg:col-span-6 flex flex-col gap-6">
          <Card>
            <CardHeader>Extracted Metadata</CardHeader>
            <CardBody noPadding>
              <table className="w-full text-left text-sm border-collapse">
                <tbody className="divide-y divide-border-subtle">
                  <tr>
                    <td className="py-4 px-6 text-text-muted font-medium w-1/3">Entity / Brand</td>
                    <td className="py-4 px-6 font-bold text-text-primary">{data.brand}</td>
                  </tr>
                  <tr>
                    <td className="py-4 px-6 text-text-muted font-medium">Product Name</td>
                    <td className="py-4 px-6 font-bold text-text-primary">{data.productName}</td>
                  </tr>
                  <tr>
                    <td className="py-4 px-6 text-text-muted font-medium">Declared Net Qty</td>
                    <td className="py-4 px-6 font-bold text-text-primary">{data.netQuantity}</td>
                  </tr>
                  <tr>
                    <td className="py-4 px-6 text-text-muted font-medium">Declared MRP</td>
                    <td className="py-4 px-6 font-bold text-text-primary">₹{data.mrp}</td>
                  </tr>
                </tbody>
              </table>
            </CardBody>
          </Card>

          <Card className="flex-1">
            <CardHeader>Statutory Checklist (Req 2 & 4)</CardHeader>
            <CardBody className="space-y-4">
              {Object.entries(data.checklist || {}).map(([key, val]) => (
                 <CitationRow 
                    key={key}
                    rule={key.replace(/_/g, ' ').toUpperCase()} 
                    status={val.status} 
                    desc={val.desc}
                 />
              ))}
            </CardBody>
          </Card>
        </div>
      </GridContainer>
    </div>
  );
}

function CitationRow({ rule, desc, status }) {
  const isPass = status === 'compliant';
  const isReview = status === 'review';
  
  return (
    <div className={`p-5 border rounded-xl flex items-start gap-4 shadow-sm ${
      isPass ? 'border-status-ok-border bg-status-ok-bg' : 
      isReview ? 'border-status-review-border bg-status-review-bg' : 
      'border-status-err-border bg-status-err-bg'
    }`}>
      <div className="mt-0.5">
        {isPass ? <CheckCircle className="w-5 h-5 text-status-ok-text" /> : 
         isReview ? <AlertTriangle className="w-5 h-5 text-status-review-text" /> : 
         <ShieldAlert className="w-5 h-5 text-status-err-text" />}
      </div>
      <div>
        <div className="flex items-baseline gap-3 mb-1">
          <span className={`text-sm font-bold ${
            isPass ? 'text-status-ok-text' : isReview ? 'text-status-review-text' : 'text-status-err-text'
          }`}>{rule}</span>
        </div>
        <div className={`text-xs font-medium mt-1 ${isPass ? 'text-status-ok-text/80' : isReview ? 'text-status-review-text/80' : 'text-status-err-text/80'}`}>
           {desc}
        </div>
      </div>
    </div>
  );
}

export default InspectionPage;
