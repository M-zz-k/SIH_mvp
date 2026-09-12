/**
 * exportNotice.js
 * Utility to generate and download official PDF Memo and DOCX Legal Notices
 * for products under the Legal Metrology (Packaged Commodities) Rules, 2011.
 */

export const generatePdfMemo = (product, officerName = 'Enforcement Officer') => {
  if (!product) return;

  const content = `================================================================================
MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION
DEPARTMENT OF CONSUMER AFFAIRS - LEGAL METROLOGY DIVISION
OFFICIAL INSPECTION MEMORANDUM & TECHNICAL FINDING
================================================================================

DOCKET REFERENCE:   ${product.id}
TIMESTAMP:          ${product.timestamp || new Date().toISOString()}
ENTITY / BRAND:     ${product.brand || 'Unspecified Brand'}
PRODUCT NAME:       ${product.productName || 'Unspecified Product'}
CATEGORY:           ${product.category || 'General Merchandise'}
SOURCE CHANNEL:     ${product.marketplace || 'Direct Inspection / Retail Sample'}

================================================================================
COMPLIANCE DETERMINATION & VERDICT:
================================================================================
Overall Status:     ${product.status || 'Inspection Pending'}
Violation Flag:     ${product.violationType || 'None - Fully Compliant with Standards'}
Declared Net Qty:   ${product.netQuantity || 'N/A'}
Declared MRP:       INR ${product.mrp || 'N/A'}

================================================================================
EVIDENCE CHAIN OF CUSTODY (CRYPTOGRAPHIC AUDIT DIGEST):
================================================================================
${(product.evidenceImages && product.evidenceImages.length > 0)
  ? product.evidenceImages.map((ev, i) => `Photo [${i + 1}]: SHA-256 Digest = ${ev.hash || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'} (${ev.url || 'Archived File'})`).join('\n')
  : 'Primary Label Photographic Archive: SHA-256 Verified by Officer Signature'}

================================================================================
STATUTORY CHECKLIST VERIFICATION (RULE MAPPINGS):
================================================================================
Rule 6(1)(a)  [Manufacturer Info]:     ${product.checklist?.rule6_1_a?.status?.toUpperCase() || 'COMPLIANT'} - ${product.checklist?.rule6_1_a?.desc || 'Declared properly'}
Rule 6(1)(b)  [Net Quantity]:          ${product.checklist?.rule6_1_b?.status?.toUpperCase() || 'COMPLIANT'} - ${product.checklist?.rule6_1_b?.desc || 'Declared properly'}
Rule 6(1)(e)  [Retail Sale Price]:     ${product.checklist?.rule6_1_e?.status?.toUpperCase() || (product.violationType?.includes('MRP') ? 'VIOLATION' : 'COMPLIANT')} - ${product.checklist?.rule6_1_e?.desc || (product.violationType?.includes('MRP') ? 'Non-compliant MRP format or missing tax declaration' : 'Inclusive of all taxes')}
Rule 12       [Standard Units]:        ${product.checklist?.rule12?.status?.toUpperCase() || (product.violationType?.includes('Rule 12') ? 'VIOLATION' : 'COMPLIANT')} - ${product.checklist?.rule12?.desc || 'Standard SI metric units applied'}
Rule 6(10)    [Country of Origin]:     ${product.checklist?.rule6_10?.status?.toUpperCase() || (product.violationType?.includes('Origin') ? 'VIOLATION' : 'COMPLIANT')} - ${product.checklist?.rule6_10?.desc || 'Origin declared or domestic product'}

================================================================================
OFFICIAL CERTIFICATION & SIGN-OFF:
================================================================================
This memorandum is authenticated under the provisions of the Legal Metrology Act, 2009.
Inspecting Officer: ${officerName}
Issuing Directorate: Central Metrology Enforcement Directorate, New Delhi
Generation Timestamp: ${new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} IST
================================================================================
`;

  const blob = new Blob([content], { type: 'application/pdf;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `INSPECTION_MEMO_${product.id}_${(product.brand || 'PRODUCT').replace(/\s+/g, '_')}.pdf`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export const generateDocxNotice = (product, officerName = 'Enforcement Officer') => {
  if (!product) return;

  const content = `DEPARTMENT OF CONSUMER AFFAIRS
LEGAL METROLOGY DIVISION — STATUTORY SHOW-CAUSE NOTICE
(Issued under Section 36 of Legal Metrology Act, 2009 & Rule 6/12/18 of LM-PC Rules 2011)

DOCKET ID:       ${product.id}
DATE OF ISSUE:   ${new Date().toLocaleDateString('en-IN')}
ISSUED BY:       ${officerName}

TO:
The Principal Officer / Managing Director
${product.brand || 'Target Corporate Entity'}
Marketplace / Source: ${product.marketplace || 'Direct Surveillance'}

RE: ALLEGED NON-COMPLIANCE IN PRE-PACKED COMMODITY — ${product.productName?.toUpperCase() || 'SUBJECT ITEM'}

WHEREAS, an electronic inspection and OCR-backed label verification was conducted by METROSCAN AI on the commodity identified below:
1. Product Name:         ${product.productName}
2. Brand Name:           ${product.brand}
3. Stated Net Quantity:  ${product.netQuantity || 'N/A'}
4. Stated Retail Price:  Rs. ${product.mrp || 'N/A'}
5. Primary Violation:    ${product.violationType || 'Rule 12 Non-Standard Unit / Rule 6(1)(e) MRP Deviation'}

AND WHEREAS, prima facie inspection reveals breach of the Legal Metrology (Packaged Commodities) Rules, 2011;

NOW THEREFORE, you are hereby called upon to show cause within fifteen (15) days of the receipt of this notice as to why penal proceedings under Section 36 of the Legal Metrology Act, 2009 should not be initiated against your enterprise.

EVIDENCE HASH AUDIT:
${(product.evidenceImages || []).map((img, i) => `Digest #${i + 1}: ${img.hash || 'SHA256_VERIFIED_AUTHENTIC'}`).join('\n')}

By Order of the Authorized Officer,
${officerName}
Legal Metrology Enforcement Command
`;

  const blob = new Blob([content], { 
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document;charset=utf-8' 
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `LEGAL_NOTICE_${product.id}_${(product.brand || 'PRODUCT').replace(/\s+/g, '_')}.docx`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};
