import React, { useState } from 'react';
import { Scale, FileText, Download, Search, CheckCircle, Clock, AlertTriangle, Building, Gavel } from 'lucide-react';
import { GridContainer, Card, CardHeader, CardBody } from '../components/Primitives';

const PRECEDENTS = [
  {
    id: 'DEC-2026-089',
    caseTitle: 'Union of India & State Metrology Dept vs. SwiftRetail Logistics Pvt Ltd',
    court: 'National Consumer Disputes Redressal Commission (NCDRC)',
    citation: '2026 NCDRC 142',
    date: '14 Jan 2026',
    subject: 'E-Commerce Marketplace Liability for Absence of Mandatory Declarations',
    verdict: 'Violation Upheld',
    summary: 'Held that quick-commerce platforms operating dark stores cannot claim safe harbor under Section 79 of the IT Act when packaging, storing, and labeling pre-packed commodities without MRP and standard net quantity declarations.',
    fine: '₹15,00,000 across 12 regional hub warehouses',
    rulesCited: ['Rule 6(1)(e)', 'Rule 6(10)', 'Rule 18(1)']
  },
  {
    id: 'DEC-2025-412',
    caseTitle: 'Metrology Inspectorate vs. Apex Confectionery & Beverage Corp',
    court: 'High Court of Bombay',
    citation: '2025 Bom HC 891',
    date: '28 Nov 2025',
    subject: 'Non-Standard Metric Expressions (Use of "gms" and "mltr")',
    verdict: 'Violation Upheld',
    summary: 'The Court rejected the petitioner’s contention that "gms" is colloquial English and synonymous with "g". Clarified that Rule 12 read with the Seventh Schedule requires strict compliance with metric standards to prevent consumer confusion.',
    fine: '₹5,00,000 compound penalty + inventory recall',
    rulesCited: ['Rule 12', 'Section 36(1) LM Act']
  },
  {
    id: 'DEC-2025-231',
    caseTitle: 'Department of Consumer Affairs vs. Eastern Imports & Trading Ltd',
    court: 'State Consumer Disputes Redressal Commission (SCDRC), Delhi',
    citation: '2025 DL SCDRC 304',
    date: '19 Aug 2025',
    subject: 'Dual MRP and Missing Country of Origin on Imported Electronics',
    verdict: 'Violation Upheld',
    summary: 'Affirmed that pasting stickers to inflate MRP or obscure overseas manufacturer declarations violates Rule 6(1)(a) and Rule 6(1)(e). Stamped dates must remain clearly visible.',
    fine: '₹8,50,000 + notice of cancellation of warehouse registration',
    rulesCited: ['Rule 6(1)(a)', 'Rule 6(1)(e)', 'Rule 6(10)']
  },
  {
    id: 'DEC-2025-104',
    caseTitle: 'Sun Agri-Foods Co-op vs. Controller of Legal Metrology, Maharashtra',
    court: 'Supreme Court of India (Appellate Jurisdiction)',
    citation: '2025 INSC 512',
    date: '12 Apr 2025',
    subject: 'Permissible Tolerances and Maximum Allowable Error (MAE) in Food Packaging',
    verdict: 'Clarified / Remanded',
    summary: 'Apex Court established that deviations beyond the Maximum Allowable Error under First Schedule must result in automated compounded notices, but clerical typographical omissions without fraudulent intent allow 15 days rectification window.',
    fine: 'Rectification order with ₹1,00,000 compliance bond',
    rulesCited: ['Rule 11', 'First Schedule (MAE Limits)']
  }
];

export default function LegalDecisionsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCase, setSelectedCase] = useState(PRECEDENTS[0]);

  const filteredCases = PRECEDENTS.filter(c => 
    c.caseTitle.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.citation.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.rulesCited.some(r => r.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleDownloadDossier = (item) => {
    const text = `================================================================================
MINISTRY OF CONSUMER AFFAIRS - LEGAL METROLOGY VAULT
JUDICIAL PRECEDENT & STATUTORY ENFORCEMENT CITATION
================================================================================
Case Title:  ${item.caseTitle}
Citation:    ${item.citation}
Court:       ${item.court}
Date:        ${item.date}
Subject:     ${item.subject}
Verdict:     ${item.verdict}
Penalty:     ${item.fine}
Rules Cited: ${item.rulesCited.join(', ')}

SUMMARY & LEGAL RATIONALE:
${item.summary}
================================================================================
`;
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${item.id}_LEGAL_PRECEDENT.txt`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col gap-6">
      
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Legal Decisions Vault</h1>
          <p className="text-[11px] text-text-muted mt-1 uppercase tracking-widest font-bold">
            Judicial Precedents, Landmark Case Law & Enforcement Orders
          </p>
        </div>
        <button 
          onClick={() => handleDownloadDossier(selectedCase)}
          className="px-4 py-2 bg-secondary text-white text-xs font-bold rounded-xl hover:bg-secondary-dark transition-colors shadow-sm flex items-center gap-2 cursor-pointer w-fit"
        >
          <Download className="w-4 h-4" /> Download Full Judgment
        </button>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          type="text"
          placeholder="Search case title, citation, or rules (e.g. Rule 12, E-Commerce, NCDRC)..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full bg-card border border-border-subtle rounded-xl pl-10 pr-4 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary shadow-sm"
        />
      </div>

      <GridContainer>
        
        {/* Precedent Cards */}
        <div className="col-span-1 md:col-span-2 lg:col-span-5 flex flex-col gap-3">
          {filteredCases.map(item => (
            <div
              key={item.id}
              onClick={() => setSelectedCase(item)}
              className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                selectedCase.id === item.id
                  ? 'bg-card border-primary ring-2 ring-primary/20 shadow-md'
                  : 'bg-card border-border-subtle hover:border-border-strong shadow-sm'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-xs font-bold text-secondary bg-secondary/10 px-2 py-0.5 rounded-md">
                  {item.citation}
                </span>
                <span className="text-[10px] font-bold text-text-muted">{item.date}</span>
              </div>
              <h3 className="text-sm font-bold text-text-primary mb-1 line-clamp-2">{item.caseTitle}</h3>
              <div className="text-xs text-text-secondary font-medium mb-2">{item.subject}</div>
              <div className="flex flex-wrap gap-1">
                {item.rulesCited.map(r => (
                  <span key={r} className="text-[10px] font-bold bg-canvas border border-border-subtle px-1.5 py-0.5 rounded text-text-muted">
                    {r}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Selected Precedent Detail */}
        <div className="col-span-1 md:col-span-2 lg:col-span-7">
          <Card className="sticky top-6">
            <CardHeader actions={
              <span className="px-2.5 py-1 bg-status-err-bg text-status-err-text border border-status-err-border rounded-lg text-xs font-bold uppercase tracking-wider">
                {selectedCase.verdict}
              </span>
            }>
              <div className="flex items-center gap-2">
                <Gavel className="w-5 h-5 text-primary" />
                <span>{selectedCase.citation}</span>
              </div>
            </CardHeader>
            <CardBody className="space-y-6">
              
              <div>
                <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest block mb-1">
                  Court & Forum
                </span>
                <div className="text-sm font-bold text-text-primary">{selectedCase.court}</div>
                <div className="text-xs text-text-secondary mt-0.5 font-medium">{selectedCase.caseTitle}</div>
              </div>

              <div>
                <h4 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-2">Subject Matter</h4>
                <div className="bg-canvas border border-border-subtle p-3 rounded-xl text-xs font-bold text-text-primary">
                  {selectedCase.subject}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-2">Judicial Holding & Operative Order</h4>
                <div className="bg-canvas border border-border-subtle p-4 rounded-xl text-sm font-medium text-text-primary leading-relaxed">
                  {selectedCase.summary}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-card border border-border-subtle p-4 rounded-xl shadow-xs">
                  <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest mb-1">Enforcement Remedy / Fine</div>
                  <div className="text-xs font-bold text-status-err-text">{selectedCase.fine}</div>
                </div>
                <div className="bg-card border border-border-subtle p-4 rounded-xl shadow-xs">
                  <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest mb-1">Governing Rules Invoked</div>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedCase.rulesCited.map(r => (
                      <span key={r} className="text-[10px] font-bold bg-primary/10 text-primary px-2 py-0.5 rounded">
                        {r}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-border-subtle flex justify-between items-center text-xs text-text-muted font-medium">
                <span>Official Repository Reference: {selectedCase.id}</span>
                <button 
                  onClick={() => handleDownloadDossier(selectedCase)}
                  className="text-primary font-bold hover:underline flex items-center gap-1 cursor-pointer"
                >
                  Export Citation <Download className="w-3.5 h-3.5" />
                </button>
              </div>

            </CardBody>
          </Card>
        </div>

      </GridContainer>

    </div>
  );
}
