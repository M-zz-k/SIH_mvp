import mockInspections from '../mock/inspections.json';
import { detectPacketVision, analyzeScannedImage } from '../utils/ocrScanner';

const USE_MOCK = true;

// Simulate network delay
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const PRODUCT_IMAGES = {
  'SKU-101': '/products/aashirvaad_atta.jpg',
  'SKU-102': '/products/pillsbury_atta.jpg',
  'SKU-103': '/products/lindt_chocolate.jpg',
  'SKU-104': '/products/himalayan_water.jpg',
  'SKU-105': '/products/fortune_oil.jpg',
  'SKU-106': '/products/tata_salt.jpg',
  'SKU-107': '/products/apple_iphone15.jpg',
  'SKU-108': '/products/maggi_noodles.jpg',
  'SKU-109': '/products/nestle_kitkat.jpg',
};

const normalizeInspection = (item) => {
  if (!item) return item;
  // CRITICAL: Always prioritize the item's own image so user photos are never replaced!
  const finalImage = item.image || PRODUCT_IMAGES[item.id] || '/products/apple_iphone15.jpg';
  
  return {
    ...item,
    image: finalImage,
    evidenceImages: (item.evidenceImages && item.evidenceImages.length > 0)
      ? item.evidenceImages.map((ev, i) => ({
          ...ev,
          url: ev.url || finalImage,
        }))
      : [{ id: 'ev1', url: finalImage, hash: 'q1w2e3r4t5y6u7i8' }]
  };
};

// Keep an in-memory mutable copy of the data for the prototype, with localStorage backing
const STORAGE_KEY = 'metroscan_custom_inspections';
let memoryInspections = [];

export const purgeExpiredInspections = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return [];
    let items = JSON.parse(saved);
    const now = Date.now();

    // 1. Filter out expired items (TTL check)
    items = items.filter(item => {
      if (!item) return false;
      if (item.expiresAt && item.expiresAt <= now) return false;
      return true;
    });

    // 2. Deduplicate: keep only the single most recent scan per product/brand
    const seen = new Set();
    const deduplicated = [];
    for (const item of items) {
      const key = `${item.brand || ''}_${item.productName || ''}`.toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        deduplicated.push(item);
      }
    }

    if (deduplicated.length !== JSON.parse(saved).length) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(deduplicated));
      memoryInspections = [...deduplicated.map(normalizeInspection), ...mockInspections.map(normalizeInspection)];
    }
    return deduplicated;
  } catch (e) {
    console.warn('Failed during purgeExpiredInspections', e);
    return [];
  }
};

export const clearAllTestScans = async () => {
  try {
    localStorage.removeItem(STORAGE_KEY);
    memoryInspections = mockInspections.map(normalizeInspection);
    return memoryInspections;
  } catch (e) {
    console.warn('Failed to clear test scans', e);
    return [];
  }
};

// Periodic auto-cleaner: runs every 5 seconds to purge expired scans automatically
if (typeof window !== 'undefined') {
  setInterval(purgeExpiredInspections, 5000);
}

const loadPersistedInspections = () => {
  return purgeExpiredInspections();
};

const savePersistedInspection = (item) => {
  try {
    const existing = loadPersistedInspections();
    // Remove previous scan of the same product to prevent duplicates
    const itemKey = `${item.brand || ''}_${item.productName || ''}`.toLowerCase();
    const filtered = existing.filter(i => {
      if (!i) return false;
      if (i.id === item.id) return false;
      const k = `${i.brand || ''}_${i.productName || ''}`.toLowerCase();
      return k !== itemKey;
    });
    const updated = [item, ...filtered];
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (e) {
    console.warn('Failed to persist inspection', e);
  }
};

export const toggleEvidencePermanence = async (id) => {
  const existing = loadPersistedInspections();
  const target = existing.find(i => i && i.id === id);
  if (!target) return null;

  if (target.isPermanent) {
    // Re-enable 5 minute TTL
    target.isPermanent = false;
    target.expiresAt = Date.now() + 5 * 60 * 1000;
  } else {
    // Mark as permanently archived
    target.isPermanent = true;
    delete target.expiresAt;
  }

  savePersistedInspection(target);
  const memIdx = memoryInspections.findIndex(i => i && i.id === id);
  if (memIdx !== -1) memoryInspections[memIdx] = target;
  return target;
};

const initialPersisted = loadPersistedInspections().map(normalizeInspection);
const persistedIds = new Set(initialPersisted.map(i => i.id));
memoryInspections = [
  ...initialPersisted,
  ...mockInspections.filter(i => !persistedIds.has(i.id)).map(normalizeInspection)
];

export const fetchInspections = async () => {
  if (USE_MOCK) {
    await delay(200);
    purgeExpiredInspections();
    const seen = new Set();
    const unique = [];
    for (const item of memoryInspections) {
      if (item && !seen.has(item.id)) {
        seen.add(item.id);
        unique.push(normalizeInspection(item));
      }
    }
    return unique;
  }
  
  // Real API implementation goes here
  const response = await fetch('/api/inspections');
  return response.json();
};

export const fetchInspectionById = async (id) => {
  if (USE_MOCK) {
    await delay(150);
    if (!id) return null;
    let found = memoryInspections.find((i) => i && i.id === id);
    if (!found) {
      const persisted = loadPersistedInspections();
      found = persisted.find((i) => i && i.id === id);
      if (found) {
        memoryInspections = [normalizeInspection(found), ...memoryInspections];
      }
    }

    // Auto-heal / re-evaluate if the inspection was previously saved as unclassified but has a real photo with KitKat packet
    if (found && (found.brand === 'No Commercial Label' || found.productName?.includes('Unclassified')) && found.image) {
      try {
        const vision = await detectPacketVision(found.image);
        if (vision.isRedPacket) {
          const reAnalyzed = await analyzeScannedImage(found.image, 'kitkat');
          found = {
            ...found,
            productName: reAnalyzed.productName,
            brand: reAnalyzed.brand,
            category: reAnalyzed.category,
            status: reAnalyzed.status,
            netQuantity: reAnalyzed.netQuantity,
            mrp: reAnalyzed.mrp,
            violationType: reAnalyzed.violationType,
            boundingBoxes: reAnalyzed.boundingBoxes,
            checklist: reAnalyzed.checklist
          };
          savePersistedInspection(found);
          const memIdx = memoryInspections.findIndex(i => i && i.id === id);
          if (memIdx !== -1) memoryInspections[memIdx] = found;
        }
      } catch (e) {
        console.warn('Auto-heal inspection error:', e);
      }
    }

    // Fallback only if absolutely no matching scan was found
    if (!found) {
      if (id === 'SKU-109' || id.toLowerCase().includes('kitkat')) {
        found = memoryInspections.find((i) => i && i.id === 'SKU-109');
      } else {
        found = memoryInspections.find((i) => i && i.id === 'SKU-107') || memoryInspections[0];
      }
    }
    return found ? normalizeInspection(found) : null;
  }
  
  // Real API implementation goes here
  const response = await fetch(`/api/inspections/${id}`);
  return response.json();
};

export const addInspection = async (newInspection) => {
  if (USE_MOCK) {
    await delay(300);
    const now = Date.now();
    const itemWithTTL = {
      ...newInspection,
      createdAt: newInspection.createdAt || now,
      // 5-Minute Auto-Purge TTL:
      expiresAt: newInspection.isPermanent ? undefined : (newInspection.expiresAt || (now + 5 * 60 * 1000))
    };
    const normalized = normalizeInspection(itemWithTTL);
    savePersistedInspection(normalized);
    memoryInspections = [normalized, ...memoryInspections.filter(i => i && i.id !== normalized.id)];
    return normalized;
  }
  // Real API implementation goes here
  return newInspection;
};

export const updateInspectionStatus = async (id, newStatus, noticeIssued = true) => {
  if (USE_MOCK) {
    await delay(300);
    const index = memoryInspections.findIndex(i => i && i.id === id);
    if (index !== -1) {
      memoryInspections[index] = {
        ...memoryInspections[index],
        status: newStatus,
        noticeIssued: noticeIssued,
        noticeDate: new Date().toISOString().split('T')[0]
      };
      savePersistedInspection(memoryInspections[index]);
      return memoryInspections[index];
    }
    return null;
  }
  return null;
};

export const fetchScrapePresets = async () => {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/scrape/presets');
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn('Backend scrape presets unavailable, using fallback', e);
  }
  return [
    { id: 'amazon_atta', title: 'Aashirvaad Superior MP Whole Wheat Atta, 5kg', platform: 'Amazon India', status: 'likely_compliant', mrp: 275, selling_price: 249 },
    { id: 'amazon_oil_violation', title: 'Fortune Sunlite Refined Sunflower Oil, 1L Pouch', platform: 'Amazon India', status: 'likely_violation', mrp: 140, selling_price: 165 },
    { id: 'blinkit_snack', title: 'Nestle KitKat 4-Finger Crisp Wafer Chocolate Bar, 38.5g', platform: 'Blinkit Quick Commerce', status: 'likely_compliant', mrp: 30, selling_price: 30 },
    { id: 'zepto_drink', title: 'Himalayan Natural Mineral Water, 1L', platform: 'Zepto Quick Commerce', status: 'needs_officer_review', mrp: 65, selling_price: 60 }
  ];
};

export const auditEcommerceListing = async (url, presetId = null) => {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/scrape/listing', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, preset_id: presetId })
    });
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn('Backend scrape listing error, generating resilient audit docket', e);
  }
  
  // Fallback docket if network call fails
  const isViolation = presetId === 'amazon_oil_violation' || (url && url.includes('oil'));
  return {
    id: 'ECOMM-OFFLINE-' + Date.now().toString().slice(-4),
    url: url || 'https://www.amazon.in/dp/B00V4J77A0',
    platform: 'Amazon India',
    product_name: isViolation ? 'Fortune Sunlite Refined Sunflower Oil, 1L Pouch' : 'Aashirvaad Superior MP Whole Wheat Atta, 5kg',
    brand: isViolation ? 'Fortune' : 'Aashirvaad',
    seller_name: 'RetailEZ Private Limited',
    mrp: isViolation ? 140.0 : 275.0,
    selling_price: isViolation ? 165.0 : 249.0,
    net_quantity: isViolation ? '1 Litre (non-standard)' : '5 kg',
    country_of_origin: isViolation ? null : 'India',
    manufacturer_details: 'ITC Limited, Kolkata / Adani Wilmar, Ahmedabad',
    consumer_care: '1800-425-4444',
    images: [isViolation ? '/products/fortune_oil.jpg' : '/products/aashirvaad_atta.jpg'],
    findings: [
      {
        rule_id: 'LMR-2011-R6(10)-ORIGIN',
        rule_name: 'Country of Origin Declaration',
        citation: 'Rule 6(10) Legal Metrology (Packaged Commodities) Rules 2011',
        status: isViolation ? 'FAIL' : 'PASS',
        observed_value: isViolation ? 'NOT DISPLAYED' : 'India',
        statutory_requirement: 'Mandatory display of Country of Origin on digital marketplace prior to consumer purchase.',
        severity: 'HIGH',
        description: isViolation ? 'Listing omits mandatory Country of Origin disclosure on digital catalog.' : 'Country of origin is prominently declared.'
      },
      {
        rule_id: 'LMR-2011-R6(1)(e)-MRP',
        rule_name: isViolation ? 'Predatory Pricing Above Declared MRP' : 'Maximum Retail Price (MRP)',
        citation: 'Rule 6(1)(e) & Section 36(1) LM Act 2009',
        status: isViolation ? 'FAIL' : 'PASS',
        observed_value: isViolation ? '₹165.00 (Declared MRP: ₹140.00)' : '₹249.00 (MRP: ₹275.00)',
        statutory_requirement: 'Selling price must not exceed declared MRP.',
        severity: isViolation ? 'CRITICAL' : 'HIGH',
        description: isViolation ? 'E-Commerce seller is selling commodity at ₹25.00 ABOVE declared MRP.' : 'Selling price is within declared MRP bounds.'
      }
    ],
    overall_tier: isViolation ? 'likely_violation' : 'likely_compliant',
    violation_summary: isViolation ? 'Critical statutory violations detected: Sale above MRP (+₹25.00) and missing Country of Origin.' : 'All statutory e-commerce marketplace declarations under Rule 6(10) are satisfied.',
    notice_draft: isViolation ? 'SHOW CAUSE NOTICE UNDER SECTION 18 & 36(1) OF LEGAL METROLOGY ACT, 2009\nTo: Nodal Officer, Amazon Seller Services Pvt Ltd\nSubject: Overpricing above MRP on Fortune Sunflower Oil 1L' : null,
    audited_at: new Date().toISOString()
  };
};

