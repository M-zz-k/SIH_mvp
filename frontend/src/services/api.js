import mockInspections from '../mock/inspections.json';

const USE_MOCK = true;

// Simulate network delay
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export const fetchInspections = async () => {
  if (USE_MOCK) {
    await delay(800);
    return [...mockInspections];
  }
  
  // Real API implementation goes here
  const response = await fetch('/api/inspections');
  return response.json();
};

export const fetchInspectionById = async (id) => {
  if (USE_MOCK) {
    await delay(500);
    return mockInspections.find((i) => i.id === id);
  }
  
  // Real API implementation goes here
  const response = await fetch(`/api/inspections/${id}`);
  return response.json();
};
