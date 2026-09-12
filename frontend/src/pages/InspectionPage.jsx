import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, Download, CheckCircle, 
  AlertTriangle, ShieldAlert, FileSearch, Hash,
  Timer, Trash2, ShieldCheck
} from 'lucide-react';
import { fetchInspectionById, updateInspectionStatus, toggleEvidencePermanence } from '../services/api';
import { generatePdfMemo, generateDocxNotice } from '../utils/exportNotice';
import { GridContainer, Card, CardHeader, CardBody, StatusChip } from '../components/Primitives';

function InspectionPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [noticeModalOpen, setNoticeModalOpen] = useState(false);
  const [noticeSuccess, setNoticeSuccess] = useState(false);
  const [timeLeft, setTimeLeft] = useState(null);
  const [isPurged, setIsPurged] = useState(false);
  const [officerName, setOfficerName] = useState(
    localStorage.getItem('userRole') === 'supervisor' ? 'K. Sharma (HQ Supervisor)' :
    localStorage.getItem('userRole') === 'admin' ? 'Central Admin (DoCA)' : 'V. Kumar (Field Inspector)'
  );

  useEffect(() => {
    fetchInspectionById(id).then((res) => setData(res));
  }, [id]);

  // Live 5-minute auto-purge countdown
  useEffect(() => {
    if (!data || !data.expiresAt || data.isPermanent) {
      setTimeLeft(null);
      return;
    }

    const checkTimer = () => {
      const remainingMs = data.expiresAt - Date.now();
      if (remainingMs <= 0) {
        setTimeLeft('00:00');
        setIsPurged(true);
      } else {
        const secs = Math.floor(remainingMs / 1000);
        const mins = Math.floor(secs / 60);
        const remSecs = secs % 60;
        setTimeLeft(`${mins}:${remSecs < 10 ? '0' : ''}${remSecs}`);
      }
    };

    checkTimer();
    const interval = setInterval(checkTimer, 1000);
    return () => clearInterval(interval);
  }, [data]);

  const handleTogglePermanence = async () => {
    const updated = await toggleEvidencePermanence(data.id);
    if (updated) {
      setData(prev => ({
        ...prev,
        isPermanent: updated.isPermanent,
        expiresAt: updated.expiresAt
      }));
    }
  };

  const handleDownloadPDF = () => {
    generatePdfMemo(data, officerName);
  };

  const handleDownloadDOCX = () => {
    generateDocxNotice(data, officerName);
  };

  const handleSignAndIssueNotice = async () => {
    const updated = await updateInspectionStatus(data.id, 'Notice Issued - Action Pending', true);
    if (updated) {
      setData(updated);
    } else {
      setData(prev => ({ ...prev, status: 'Notice Issued - Action Pending', noticeIssued: true }));
    }
    setNoticeSuccess(true);
    setTimeout(() => {
      setNoticeModalOpen(false);
      setNoticeSuccess(false);
    }, 1800);
  };

  const getFallbackImage = (item) => {
    if (!item) return '/products/apple_iphone15.jpg';
    const pName = (item.productName || '').toLowerCase();
    const brand = (item.brand || '').toLowerCase();
    if (pName.includes('kitkat') || brand.includes('nestlé') || brand.includes('nestle')) return '/products/nestle_kitkat.jpg';
    if (brand.includes('apple') || pName.includes('iphone')) return '/products/apple_iphone15.jpg';
    if (pName.includes('pillsbury')) return '/products/pillsbury_atta.jpg';
    if (pName.includes('maggi')) return '/products/maggi_noodles.jpg';
    if (pName.includes('himalayan')) return '/products/himalayan_water.jpg';
    if (pName.includes('fortune')) return '/products/fortune_oil.jpg';
    if (pName.includes('tata')) return '/products/tata_salt.jpg';
    if (pName.includes('lindt')) return '/products/lindt_chocolate.jpg';
    return '/products/aashirvaad_atta.jpg';
  };

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[450px] gap-4">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
        <span className="text-xs font-bold uppercase tracking-widest text-text-muted">Loading Inspection Dossier...</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      
      {/* Notice Confirmation Modal */}
      {noticeModalOpen && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-card border border-border-strong rounded-2xl max-w-lg w-full p-6 shadow-2xl animate-in zoom-in-95">
            {!noticeSuccess ? (
              <>
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2.5 bg-primary-light/10 text-primary rounded-xl">
                    <ShieldAlert className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-text-primary">Sign & Issue Statutory Notice</h3>
                    <p className="text-xs text-text-muted">Legal Metrology (Packaged Commodities) Rules, 2011</p>
                  </div>
                </div>

                <div className="bg-canvas border border-border-subtle p-4 rounded-xl mb-4 text-xs space-y-2">
                  <div className="flex justify-between">
                    <span className="text-text-muted font-bold">Docket ID:</span>
                    <span className="font-mono font-bold text-text-primary">{data.id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted font-bold">Target Entity:</span>
                    <span className="font-bold text-text-primary">{data.brand} ({data.productName})</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted font-bold">Alleged Violation:</span>
                    <span className="font-bold text-status-err-text">{data.violationType || 'Rule 12 Standard Unit Non-compliance'}</span>
                  </div>
                </div>

                <div className="mb-4">
                  <label className="block text-xs font-bold text-text-muted uppercase tracking-widest mb-1.5">
                    Signing Authority / Officer
                  </label>
                  <input
                    type="text"
                    value={officerName}
                    onChange={(e) => setOfficerName(e.target.value)}
                    className="w-full bg-canvas border border-border-subtle rounded-xl px-4 py-2 text-sm font-bold text-text-primary focus:outline-none focus:border-primary"
                  />
                </div>

                <div className="flex gap-3 justify-end">
                  <button
                    onClick={() => setNoticeModalOpen(false)}
                    className="px-4 py-2 bg-canvas border border-border-subtle text-text-secondary text-sm font-bold rounded-xl hover:bg-border-subtle transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSignAndIssueNotice}
                    className="px-5 py-2 bg-primary text-white text-sm font-bold rounded-xl hover:bg-primary-dark transition-colors shadow-sm"
                  >
                    Authorize & Issue Notice
                  </button>
                </div>
              </>
            ) : (
              <div className="text-center py-6">
                <CheckCircle className="w-12 h-12 text-status-ok-text mx-auto mb-3" />
                <h3 className="text-lg font-bold text-text-primary">Statutory Notice Issued!</h3>
                <p className="text-xs text-text-muted mt-1">
                  Official notice registered and logged in enforcement repository.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Purged Modal */}
      {isPurged && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-card border border-border-strong rounded-2xl max-w-md w-full p-6 text-center shadow-2xl animate-in zoom-in-95">
            <div className="w-12 h-12 rounded-full bg-rose-500/20 text-rose-500 flex items-center justify-center mx-auto mb-3">
              <Trash2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-text-primary">Evidence Auto-Purged</h3>
            <p className="text-xs text-text-muted mt-2 mb-5 leading-relaxed">
              As per the 5-minute transient data retention policy, this camera photo and temporary inspection evidence have been automatically deleted from local storage.
            </p>
            <button 
              onClick={() => navigate('/scan')}
              className="px-6 py-2.5 bg-primary text-white font-bold rounded-xl text-xs hover:bg-primary-dark transition-colors cursor-pointer"
            >
              Back to Scanner
            </button>
          </div>
        </div>
      )}

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
                status={data.status.includes('Compliant') ? 'compliant' : data.status.includes('Review') ? 'review' : 'violation'}
                label={data.status}
              />
            </h1>
            {/* Live TTL Countdown Badge */}
            {data.expiresAt && !data.isPermanent && (
              <div className="flex items-center gap-1.5 mt-1 text-[11px] font-bold text-amber-600 dark:text-amber-400">
                <Timer className="w-3.5 h-3.5 animate-pulse" />
                <span>Temporary Evidence: Auto-purging in {timeLeft || '5:00'}</span>
                <button
                  onClick={handleTogglePermanence}
                  className="underline hover:text-amber-700 cursor-pointer ml-1 text-[10px]"
                >
                  [Keep in Vault]
                </button>
              </div>
            )}
            {data.isPermanent && (
              <div className="flex items-center gap-1 mt-1 text-[11px] font-bold text-emerald-600 dark:text-emerald-400">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Archived in Permanent Evidence Vault</span>
                <button
                  onClick={handleTogglePermanence}
                  className="underline opacity-70 hover:opacity-100 cursor-pointer ml-1 text-[10px]"
                >
                  [Set 5m Auto-Delete]
                </button>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex gap-3 w-full sm:w-auto">
          <button 
            onClick={handleDownloadPDF} 
            title="Download PDF Memo for this product"
            className="flex-1 sm:flex-none px-4 py-2 bg-secondary text-white text-sm font-bold rounded-xl hover:bg-secondary-dark transition-colors shadow-sm flex items-center justify-center gap-2 cursor-pointer"
          >
            <Download className="w-4 h-4" /> PDF Memo
          </button>
          <button 
            onClick={handleDownloadDOCX} 
            title="Download DOCX Legal Dossier"
            className="flex-1 sm:flex-none px-4 py-2 bg-secondary text-white text-sm font-bold rounded-xl hover:bg-secondary-dark transition-colors shadow-sm flex items-center justify-center gap-2 cursor-pointer"
          >
            <Download className="w-4 h-4" /> DOCX
          </button>
          <button 
            onClick={() => setNoticeModalOpen(true)}
            title="Sign and Issue Legal Notice"
            className="flex-1 sm:flex-none px-6 py-2 bg-primary text-white border border-primary text-sm font-bold rounded-xl hover:bg-primary-dark transition-colors shadow-sm cursor-pointer"
          >
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
          <CardBody noPadding className="bg-canvas relative overflow-hidden flex items-center justify-center border-b border-border-subtle flex-1 min-h-[480px] p-4">
             <div className="relative inline-block max-w-full max-h-[460px]">
               <img 
                 src={data.image || getFallbackImage(data)} 
                 alt={data.productName} 
                 onError={(e) => {
                   e.target.onerror = null;
                   e.target.src = getFallbackImage(data);
                 }}
                 className="max-h-[450px] max-w-full w-auto h-auto object-contain block rounded-xl drop-shadow-md mx-auto" 
               />
               {data.boundingBoxes?.map((box) => (
                <div
                  key={box.id}
                  className={`absolute border-2 ${
                    box.color === 'green' ? 'border-status-ok-text bg-status-ok-bg/30' :
                    box.color === 'red' ? 'border-status-err-text bg-status-err-bg/30' : 'border-status-review-text bg-status-review-bg/30'
                  } group/box shadow-sm transition-all hover:bg-opacity-70 cursor-pointer`}
                  style={{
                    left: `${box.x}%`,
                    top: `${box.y}%`,
                    width: `${box.width}%`,
                    height: `${box.height}%`
                  }}
                >
                  <div className="absolute top-full left-0 mt-1 bg-sidebar text-white text-[11px] font-bold p-2 rounded shadow-xl opacity-0 group-hover/box:opacity-100 whitespace-nowrap z-20 transition-opacity pointer-events-none">
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
                     <img 
                       src={ev.url || getFallbackImage(data)} 
                       alt={`Evidence ${i + 1}`}
                       onError={(e) => {
                         e.target.onerror = null;
                         e.target.src = getFallbackImage(data);
                       }}
                       className="w-full h-full object-cover" 
                     />
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
