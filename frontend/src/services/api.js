import mockInspections from '../mock/inspections.json';

const USE_MOCK = true;

// Simulate network delay
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Keep an in-memory mutable copy of the data for the prototype
let memoryInspections = [...mockInspections];

export const fetchInspections = async () => {
  if (USE_MOCK) {
    await delay(800);
    return [...memoryInspections];
  }
  
  // Real API implementation goes here
  const response = await fetch('/api/inspections');
  return response.json();
};

export const fetchInspectionById = async (id) => {
  if (USE_MOCK) {
    await delay(500);
    return memoryInspections.find((i) => i.id === id);
  }
  
  // Real API implementation goes here
  const response = await fetch(`/api/inspections/${id}`);
  return response.json();
};

export const addInspection = async (newInspection) => {
  if (USE_MOCK) {
    await delay(1000);
    memoryInspections = [newInspection, ...memoryInspections];
    return newInspection;
  }
  // Real API implementation goes here
  return newInspection;
};
