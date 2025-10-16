import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:3001/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const ordersAPI = {
  // Get all orders
  getOrders: () => api.get('/orders'),
  
  // Get orders with filters
  getOrdersWithFilters: (filters) => 
    api.get('/orders', { params: filters }),
  
  // Get single order
  getOrder: (id) => api.get(`/orders/${id}`),
  
  // Create new order
  createOrder: (orderData) => api.post('/orders', orderData),
  
  // Update order
  updateOrder: (id, orderData) => api.put(`/orders/${id}`, orderData),
  
  // Delete order
  deleteOrder: (id) => api.delete(`/orders/${id}`)
};

export const summariesAPI = {
  // Generate summary
  generateSummary: () => api.get('/summaries'),
  
  // Get summary with filters
  getSummaryWithFilters: (filters) => 
    api.get('/summaries', { params: filters })
};

export const exportAPI = {
  // Export orders to Excel
  exportToExcel: (filters = {}) => 
    api.get('/export', { 
      params: { type: 'excel', ...filters },
      responseType: 'blob'
    }),
  
  // Export orders to CSV
  exportToCSV: (filters = {}) => 
    api.get('/export', { 
      params: { type: 'csv', ...filters },
      responseType: 'blob'
    }),
  
  // Export orders to PDF
  exportToPDF: (filters = {}) => 
    api.get('/export', { 
      params: { type: 'pdf', ...filters },
      responseType: 'blob'
    })
};

// Utility function to handle file download
export const downloadFile = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export default api;
