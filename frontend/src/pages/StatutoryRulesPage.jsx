import React, { useState } from 'react';
import { Scale, BookOpen, Search, Filter, CheckCircle2, AlertOctagon, FileText, ChevronRight, Download, ShieldCheck } from 'lucide-react';
import { GridContainer, Card, CardHeader, CardBody } from '../components/Primitives';

const STATUTORY_RULES = [
  {
    id: 'rule6_1_a',
    rule: 'Rule 6(1)(a)',
    title: 'Name & Address of Manufacturer / Packer',
    category: 'Identity',
    severity: 'High',
    description: 'Every package shall bear the name and complete address of the manufacturer, or where the manufacturer is not the packer, the name and address of the manufacturer and packer.',
    penalty: 'Compoundable offence under Section 36(1) of Legal Metrology Act, 2009. Fine up to ₹25,000 for first offence.',
    exampleCorrect: 'Manufactured by: Sunrise Foods Pvt. Ltd., Plot 12, MIDC, Pune, Maharashtra - 411019',
    exampleViolation: 'Mfg by: Sunrise Foods, Pune (missing pin code / complete corporate identity)'
  },
  {
    id: 'rule6_1_b',
    rule: 'Rule 6(1)(b)',
    title: 'Net Quantity Declaration in Standard Unit',
    category: 'Quantity & Units',
    severity: 'Critical',
    description: 'The net quantity in terms of standard unit of weight or measure shall be declared on each package.',
    penalty: 'Seizure of package stock; fine up to ₹50,000 for second violation or imprisonment.',
    exampleCorrect: 'Net Qty: 1 kg (or 500 g, 1 L, 750 ml)',
    exampleViolation: 'Net Weight: 1000 gms / 1.0 kilo (non-standard symbol violation)'
  },
  {
    id: 'rule6_1_c',
    rule: 'Rule 6(1)(c)',
    title: 'Month and Year of Manufacture / Pre-packing',
    category: 'Shelf Life',
    severity: 'High',
    description: 'The month and year in which the commodity is manufactured or pre-packed or imported shall be mentioned clearly.',
    penalty: 'Penalty up to ₹25,000; mandatory stock withdrawal if misleading consumers.',
    exampleCorrect: 'Mfg Date: 03/2026 or Mar-2026',
    exampleViolation: 'Date missing or stamped illegibly without month clarification'
  },
  {
    id: 'rule6_1_e',
    rule: 'Rule 6(1)(e)',
    title: 'Maximum Retail Price (MRP) Declaration',
    category: 'Pricing',
    severity: 'Critical',
    description: 'Retail sale price shall clearly state "Maximum Retail Price" or "MRP ₹..." inclusive of all taxes. Overcharging or dual MRP is strictly prohibited.',
    penalty: 'Severe prosecution under Section 36(2); fine up to ₹1,00,000 and possible license suspension.',
    exampleCorrect: 'MRP ₹199.00 (Incl. of all taxes)',
    exampleViolation: 'MRP: 199/- + GST Extra (Forbidden tax exclusion syntax)'
  },
  {
    id: 'rule12',
    rule: 'Rule 12',
    title: 'Manner of Expressing Units & Symbols',
    category: 'Quantity & Units',
    severity: 'Medium',
    description: 'Units must use official metric symbols (kg, g, mg, L, ml, m, cm, mm). Plural suffixes like "kgs", "gms", "mltr", or "mtrs" are non-compliant.',
    penalty: 'Statutory compliance notice; corrective packaging mandate within 30 days.',
    exampleCorrect: '5 kg, 250 g, 500 ml',
    exampleViolation: '5 kgs., 250 gms., 500 mltr'
  },
  {
    id: 'rule6_10',
    rule: 'Rule 6(10)',
    title: 'Country of Origin for Imported Products',
    category: 'Origin',
    severity: 'High',
    description: 'Mandatory declaration of Country of Origin on both digital e-commerce listings and physical retail packaging.',
    penalty: 'Customs and metrology audit notice; e-commerce takedown notice.',
    exampleCorrect: 'Country of Origin: India / Country of Origin: Vietnam',
    exampleViolation: 'Imported product without explicit country declaration'
  }
];

export default function StatutoryRulesPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [activeRule, setActiveRule] = useState(STATUTORY_RULES[0]);

  const categories = ['All', 'Identity', 'Quantity & Units', 'Pricing', 'Shelf Life', 'Origin'];

  const filteredRules = STATUTORY_RULES.filter(r => {
    const matchesSearch = r.rule.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          r.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          r.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCat = selectedCategory === 'All' || r.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  return (
    <div className="flex flex-col gap-6">
      
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Statutory Rules Configurator</h1>
          <p className="text-[11px] text-text-muted mt-1 uppercase tracking-widest font-bold">
            Legal Metrology (Packaged Commodities) Rules, 2011 Reference & Rule Engine Spec
          </p>
        </div>
        <div className="flex items-center gap-2 bg-card border border-border-subtle px-3 py-1.5 rounded-xl shadow-sm text-xs font-bold text-text-secondary">
          <ShieldCheck className="w-4 h-4 text-primary" /> Active Edition: Gazette of India 2011 (Amended 2024)
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            placeholder="Search by rule, clause, or requirement (e.g. MRP, Rule 12)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-card border border-border-subtle rounded-xl pl-10 pr-4 py-2.5 text-sm font-medium text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary shadow-sm"
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1 sm:pb-0">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-colors shadow-sm cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-primary text-white'
                  : 'bg-card text-text-secondary border border-border-subtle hover:bg-canvas'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      <GridContainer>
        
        {/* Left Rules List */}
        <div className="col-span-1 md:col-span-2 lg:col-span-5 flex flex-col gap-3">
          {filteredRules.map(rule => (
            <div
              key={rule.id}
              onClick={() => setActiveRule(rule)}
              className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                activeRule.id === rule.id
                  ? 'bg-card border-primary ring-2 ring-primary/20 shadow-md'
                  : 'bg-card border-border-subtle hover:border-border-strong shadow-sm'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-xs font-bold text-primary bg-primary-light/15 px-2 py-0.5 rounded-md">
                  {rule.rule}
                </span>
                <span className={`text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded ${
                  rule.severity === 'Critical' ? 'bg-status-err-bg text-status-err-text border border-status-err-border' :
                  rule.severity === 'High' ? 'bg-status-review-bg text-status-review-text border border-status-review-border' :
                  'bg-canvas text-text-secondary border border-border-subtle'
                }`}>
                  {rule.severity}
                </span>
              </div>
              <h3 className="text-sm font-bold text-text-primary mb-1">{rule.title}</h3>
              <p className="text-xs text-text-muted line-clamp-2">{rule.description}</p>
            </div>
          ))}
          {filteredRules.length === 0 && (
            <div className="p-8 bg-card rounded-2xl border border-border-subtle text-center text-sm font-bold text-text-muted">
              No matching statutory rules found.
            </div>
          )}
        </div>

        {/* Right Detail Pane */}
        <div className="col-span-1 md:col-span-2 lg:col-span-7">
          <Card className="sticky top-6">
            <CardHeader actions={
              <span className="text-xs font-mono font-bold text-text-muted">{activeRule.category}</span>
            }>
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-primary" />
                <span>{activeRule.rule}: {activeRule.title}</span>
              </div>
            </CardHeader>
            <CardBody className="space-y-6">
              
              <div>
                <h4 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-2">Legal Specification</h4>
                <div className="bg-canvas border border-border-subtle p-4 rounded-xl text-sm font-medium text-text-primary leading-relaxed">
                  {activeRule.description}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-2">Penal & Enforcement Provisions</h4>
                <div className="bg-status-err-bg/50 border border-status-err-border p-4 rounded-xl text-xs font-bold text-status-err-text">
                  {activeRule.penalty}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-status-ok-bg/60 border border-status-ok-border p-4 rounded-xl">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-status-ok-text mb-1.5 uppercase tracking-wide">
                    <CheckCircle2 className="w-4 h-4" /> Compliant Standard
                  </div>
                  <div className="text-xs font-medium text-text-primary bg-card/80 p-2.5 rounded-lg border border-status-ok-border font-mono">
                    {activeRule.exampleCorrect}
                  </div>
                </div>

                <div className="bg-status-err-bg/60 border border-status-err-border p-4 rounded-xl">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-status-err-text mb-1.5 uppercase tracking-wide">
                    <AlertOctagon className="w-4 h-4" /> Violation Pattern
                  </div>
                  <div className="text-xs font-medium text-text-primary bg-card/80 p-2.5 rounded-lg border border-status-err-border font-mono">
                    {activeRule.exampleViolation}
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-border-subtle flex justify-between items-center text-xs text-text-muted font-medium">
                <span>Integrated with automated Python Rule Engine (`rule_engine.py`)</span>
                <span className="font-bold text-primary">Regex & OCR Verification Active</span>
              </div>

            </CardBody>
          </Card>
        </div>

      </GridContainer>

    </div>
  );
}
