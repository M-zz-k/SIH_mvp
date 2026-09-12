import React, { useState, useEffect } from 'react';
import { 
  Globe, Search, ExternalLink, ShieldCheck, AlertTriangle, 
  XCircle, CheckCircle, FileText, Download, Building, 
  Tag, Scale, Sparkles, ArrowUpRight, Copy, Check
} from 'lucide-react';
import { fetchScrapePresets, auditEcommerceListing } from '../services/api';

export default function ECommerceAuditPage() {
  const [urlInput, setUrlInput] = useState('https://www.amazon.in/dp/B07XYZ9999');
  const [loading, setLoading] = useState(false);
  const [auditResult, setAuditResult] = useState(null);
  const [presets, setPresets] = useState([]);
  const [selectedPresetId, setSelectedPresetId] = useState('amazon_oil_violation');
  const [showNoticeModal, setShowNoticeModal] = useState(false);
  const [copiedNotice, setCopiedNotice] = useState(false);

  useEffect(() => {
    async function loadPresets() {
      const data = await fetchScrapePresets();
      setPresets(data);
      // Automatically load the first violation demo for instant impression
      handleRunAudit('https://www.amazon.in/dp/B07XYZ9999', 'amazon_oil_violation');
    }
    loadPresets();
  }, []);

  const handleRunAudit = async (url, presetId = null) => {
    setLoading(true);
    try {
      const result = await auditEcommerceListing(url, presetId);
      setAuditResult(result);
    } catch (err) {
      console.error('Audit failed', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePresetSelect = (preset) => {
    setSelectedPresetId(preset.id);
    setUrlInput(preset.url);
    handleRunAudit(preset.url, preset.id);
  };

  const handleManualSubmit = (e) => {
    e.preventDefault();
    if (!urlInput) return;
    setSelectedPresetId(null);
    handleRunAudit(urlInput, null);
  };

  const handleCopyNotice = () => {
    if (auditResult?.notice_draft) {
      navigator.clipboard.writeText(auditResult.notice_draft);
      setCopiedNotice(true);
      setTimeout(() => setCopiedNotice(false), 2000);
    }
  };

  const isViolation = auditResult?.overall_tier === 'likely_violation';
  const isReview = auditResult?.overall_tier === 'needs_officer_review';

  return (
    <div className="space-y-6 pb-12">
      
      {/* 1. Header Banner */}
      <div className="bg-gradient-to-r from-[#0C2D37] via-[#0E5E73] to-[#124B5A] rounded-3xl p-6 sm:p-8 text-white shadow-lg relative overflow-hidden">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-primary-light text-xs font-bold uppercase tracking-wider mb-3 backdrop-blur-sm border border-white/10">
            <Globe className="w-3.5 h-3.5" />
            Digital Marketplace Statutory Enforcement
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
            E-Commerce Listing Compliance Auditor
          </h1>
          <p className="text-sm text-slate-200 mt-2 leading-relaxed font-normal">
            Automated compliance scanner for online marketplaces (<span className="font-semibold text-white">Amazon, Blinkit, Zepto, Flipkart</span>) enforcing 
            <span className="text-primary-light font-bold"> Rule 6(10)</span> (Country of Origin display) and 
            <span className="text-primary-light font-bold"> Rule 6(1)(e)</span> (prohibition of selling above MRP under Section 36(1)).
          </p>
        </div>
        <div className="absolute right-[-20px] bottom-[-20px] opacity-10 pointer-events-none">
          <Globe className="w-80 h-80 text-white" />
        </div>
      </div>

      {/* 2. URL Input & Platform Controls */}
      <div className="bg-card rounded-3xl p-6 border border-border-subtle shadow-sm space-y-4">
        
        {/* Preset Selector Chips */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-text-muted uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-primary" />
              1-Click Evaluation Presets
            </span>
            <span className="text-[11px] text-text-muted">Click any listing to audit instantly</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
            {presets.map((p) => {
              const isViol = p.status === 'likely_violation';
              const isRev = p.status === 'needs_officer_review';
              const isSelected = selectedPresetId === p.id;
              
              return (
                <button
                  key={p.id}
                  onClick={() => handlePresetSelect(p)}
                  className={`p-3 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex flex-col justify-between ${
                    isSelected 
                      ? 'border-primary bg-primary/5 ring-2 ring-primary/20 shadow-sm' 
                      : 'border-border-subtle hover:border-border-strong bg-canvas/50'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">{p.platform}</span>
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full uppercase ${
                        isViol ? 'bg-red-100 text-red-700' : isRev ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                      }`}>
                        {isViol ? 'Violation' : isRev ? 'Review' : 'Compliant'}
                      </span>
                    </div>
                    <div className="text-xs font-bold text-text-primary line-clamp-1">{p.title}</div>
                  </div>
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-border-subtle/60 text-[11px] text-text-secondary">
                    <span>MRP: ₹{p.mrp}</span>
                    <span className="font-semibold text-text-primary">Sell: ₹{p.selling_price}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Live URL Search Bar */}
        <form onSubmit={handleManualSubmit} className="pt-2">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-text-muted">
                <Globe className="w-4 h-4" />
              </div>
              <input
                type="url"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="Paste Amazon, Blinkit, Zepto, or Flipkart product URL..."
                className="w-full pl-10 pr-4 py-3 bg-canvas border border-border-subtle rounded-2xl text-sm text-text-primary focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all font-mono text-xs"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 bg-primary hover:bg-primary-dark text-white rounded-2xl font-bold text-sm flex items-center justify-center gap-2 shadow-sm transition-all cursor-pointer disabled:opacity-50 shrink-0"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Scraping Marketplace...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Audit Listing</span>
                </>
              )}
            </button>
          </div>
        </form>

      </div>

      {/* 3. Audit Results View */}
      {auditResult && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-in fade-in duration-300">
          
          {/* Left Column: Scraped Listing Metadata (5 Cols) */}
          <div className="lg:col-span-5 space-y-6">
            
            <div className="bg-card rounded-3xl p-6 border border-border-subtle shadow-sm space-y-5">
              
              {/* Product Header & Media */}
              <div className="flex gap-4 items-start">
                <div className="w-24 h-24 bg-canvas rounded-2xl border border-border-subtle p-2 shrink-0 flex items-center justify-center overflow-hidden">
                  <img
                    src={auditResult.images[0] || '/products/aashirvaad_atta.jpg'}
                    alt={auditResult.product_name}
                    className="max-h-full max-w-full object-contain mix-blend-multiply"
                    onError={(e) => { e.target.src = '/products/aashirvaad_atta.jpg'; }}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-canvas border border-border-subtle text-text-muted">
                      {auditResult.platform}
                    </span>
                    <span className="text-xs text-text-muted font-mono">{auditResult.id}</span>
                  </div>
                  <h3 className="font-bold text-base text-text-primary leading-tight line-clamp-2">
                    {auditResult.product_name}
                  </h3>
                  <div className="text-xs text-text-secondary mt-1 flex items-center gap-2">
                    <span>Brand: <strong className="text-text-primary">{auditResult.brand}</strong></span>
                    <span>•</span>
                    <a 
                      href={auditResult.url} 
                      target="_blank" 
                      rel="noreferrer" 
                      className="text-primary hover:underline flex items-center gap-0.5 text-[11px] font-semibold"
                    >
                      <span>View Live Page</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              </div>

              {/* Price & Weight Comparison Block */}
              <div className="grid grid-cols-2 gap-3 p-4 bg-canvas rounded-2xl border border-border-subtle">
                <div>
                  <div className="text-[10px] uppercase font-bold text-text-muted tracking-wider">Selling Price</div>
                  <div className={`text-xl font-black mt-0.5 ${
                    auditResult.selling_price > auditResult.mrp ? 'text-status-err-text' : 'text-text-primary'
                  }`}>
                    ₹{auditResult.selling_price.toFixed(2)}
                  </div>
                  {auditResult.selling_price > auditResult.mrp && (
                    <span className="inline-block mt-1 text-[9px] font-bold text-red-700 bg-red-100 px-1.5 py-0.5 rounded">
                      +₹{(auditResult.selling_price - auditResult.mrp).toFixed(2)} Above MRP!
                    </span>
                  )}
                </div>

                <div>
                  <div className="text-[10px] uppercase font-bold text-text-muted tracking-wider">Declared MRP</div>
                  <div className="text-xl font-black text-text-primary mt-0.5">
                    ₹{auditResult.mrp.toFixed(2)}
                  </div>
                  <div className="text-[10px] text-text-muted mt-1">
                    Incl. of all taxes
                  </div>
                </div>
              </div>

              {/* Declarations Extraction Table */}
              <div className="space-y-3 pt-2">
                <h4 className="text-xs font-bold text-text-muted uppercase tracking-wider">
                  Mandatory Digital Declarations
                </h4>

                <div className="divide-y divide-border-subtle/70 text-xs">
                  <div className="py-2 flex justify-between gap-3">
                    <span className="text-text-secondary font-medium shrink-0">Country of Origin:</span>
                    <span className="text-text-primary font-bold text-right">
                      {auditResult.country_of_origin || (
                        <span className="text-status-err-text font-bold uppercase tracking-wider flex items-center gap-1 justify-end">
                          <XCircle className="w-3 h-3" /> NOT DECLARED
                        </span>
                      )}
                    </span>
                  </div>

                  <div className="py-2 flex justify-between gap-3">
                    <span className="text-text-secondary font-medium shrink-0">Declared Net Qty:</span>
                    <span className="text-text-primary font-bold text-right font-mono">
                      {auditResult.net_quantity}
                    </span>
                  </div>

                  <div className="py-2 flex justify-between gap-3">
                    <span className="text-text-secondary font-medium shrink-0">Merchant / Seller:</span>
                    <span className="text-text-primary font-bold text-right">
                      {auditResult.seller_name}
                    </span>
                  </div>

                  <div className="py-2 flex justify-between gap-3">
                    <span className="text-text-secondary font-medium shrink-0">Manufacturer:</span>
                    <span className="text-text-primary font-medium text-right line-clamp-2 max-w-[240px]">
                      {auditResult.manufacturer_details || 'Not Disclosed'}
                    </span>
                  </div>

                  <div className="py-2 flex justify-between gap-3">
                    <span className="text-text-secondary font-medium shrink-0">Consumer Helpline:</span>
                    <span className="text-text-primary font-medium text-right">
                      {auditResult.consumer_care || 'None Listed'}
                    </span>
                  </div>
                </div>
              </div>

            </div>

          </div>

          {/* Right Column: Statutory Legal Metrology Compliance Findings (7 Cols) */}
          <div className="lg:col-span-7 space-y-6">
            
            {/* Overall Verdict Banner */}
            <div className={`p-6 rounded-3xl border shadow-sm ${
              isViolation 
                ? 'bg-red-50/70 border-red-200 text-red-950' 
                : isReview 
                ? 'bg-amber-50/70 border-amber-200 text-amber-950' 
                : 'bg-emerald-50/70 border-emerald-200 text-emerald-950'
            }`}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-2xl ${
                    isViolation ? 'bg-red-600 text-white' : isReview ? 'bg-amber-500 text-white' : 'bg-emerald-600 text-white'
                  }`}>
                    {isViolation ? <XCircle className="w-6 h-6" /> : isReview ? <AlertTriangle className="w-6 h-6" /> : <ShieldCheck className="w-6 h-6" />}
                  </div>
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider opacity-75">Statutory Audit Result</div>
                    <div className="text-xl font-black tracking-tight">
                      {isViolation ? 'LIKELY STATUTORY VIOLATION' : isReview ? 'NEEDS OFFICER REVIEW' : 'LIKELY COMPLIANT'}
                    </div>
                  </div>
                </div>

                <span className={`text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider ${
                  isViolation ? 'bg-red-200 text-red-900' : isReview ? 'bg-amber-200 text-amber-900' : 'bg-emerald-200 text-emerald-900'
                }`}>
                  {auditResult.overall_tier}
                </span>
              </div>

              <p className="text-xs mt-3 leading-relaxed opacity-90 font-medium">
                {auditResult.violation_summary}
              </p>
            </div>

            {/* Checklist of Metrology Rules */}
            <div className="bg-card rounded-3xl p-6 border border-border-subtle shadow-sm space-y-4">
              <h4 className="text-xs font-bold text-text-muted uppercase tracking-wider flex items-center justify-between">
                <span>Statutory Rule Verifications</span>
                <span className="text-[11px] text-text-secondary font-normal">Legal Metrology (Packaged Commodities) Rules, 2011</span>
              </h4>

              <div className="space-y-3">
                {auditResult.findings.map((finding) => {
                  const pass = finding.status === 'PASS';
                  return (
                    <div 
                      key={finding.rule_id}
                      className={`p-4 rounded-2xl border transition-all ${
                        pass 
                          ? 'border-border-subtle bg-canvas/40' 
                          : 'border-red-200 bg-red-50/40'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <div className="flex items-center gap-2">
                          <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs shrink-0 ${
                            pass ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {pass ? '✓' : '✗'}
                          </span>
                          <span className="font-bold text-sm text-text-primary">{finding.rule_name}</span>
                        </div>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-card border border-border-subtle text-text-secondary">
                          {finding.citation}
                        </span>
                      </div>

                      <div className="text-xs text-text-secondary mt-1 pl-7">
                        {finding.description}
                      </div>

                      <div className="mt-2.5 pl-7 flex items-center justify-between text-[11px] pt-2 border-t border-border-subtle/50">
                        <span className="text-text-muted">Observed Value:</span>
                        <span className={`font-mono font-bold ${pass ? 'text-text-primary' : 'text-red-700'}`}>
                          {finding.observed_value}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Legal Notice Action Bar */}
            {isViolation && (
              <div className="bg-card rounded-3xl p-6 border border-border-subtle shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <h4 className="text-sm font-bold text-text-primary">Issue Digital Marketplace Notice</h4>
                  <p className="text-xs text-text-secondary mt-0.5">
                    Generate an official Show Cause Notice under Section 18 & 36(1) for the e-commerce nodal officer.
                  </p>
                </div>
                <div className="flex items-center gap-2.5 shrink-0 w-full sm:w-auto">
                  <button
                    onClick={() => setShowNoticeModal(true)}
                    className="flex-1 sm:flex-initial px-4 py-2.5 bg-sidebar hover:bg-primary text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition-colors cursor-pointer"
                  >
                    <FileText className="w-4 h-4" />
                    <span>Preview Notice</span>
                  </button>
                </div>
              </div>
            )}

          </div>

        </div>
      )}

      {/* 4. Show Cause Notice Modal */}
      {showNoticeModal && auditResult?.notice_draft && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="bg-card w-full max-w-2xl rounded-3xl border border-border-subtle shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            
            <div className="p-6 border-b border-border-subtle flex items-center justify-between bg-canvas">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" />
                <h3 className="font-bold text-base text-text-primary">
                  Official Show Cause Notice Preview
                </h3>
              </div>
              <button 
                onClick={() => setShowNoticeModal(false)}
                className="text-text-muted hover:text-text-primary text-sm font-bold p-1"
              >
                ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto flex-1 font-mono text-xs text-text-primary leading-relaxed whitespace-pre-wrap bg-canvas/30">
              {auditResult.notice_draft}
            </div>

            <div className="p-4 border-t border-border-subtle bg-canvas flex items-center justify-between">
              <div className="text-[11px] text-text-muted">
                Statutory Notice under Section 18 / 36(1) LM Act 2009
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopyNotice}
                  className="px-4 py-2 bg-card border border-border-subtle hover:border-primary text-text-primary rounded-xl text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  {copiedNotice ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                  <span>{copiedNotice ? 'Copied' : 'Copy Text'}</span>
                </button>
                <button
                  onClick={() => setShowNoticeModal(false)}
                  className="px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-xl text-xs font-bold transition-colors cursor-pointer"
                >
                  Close
                </button>
              </div>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
