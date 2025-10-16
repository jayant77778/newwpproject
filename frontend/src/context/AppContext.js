import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { mockOrders } from '../data/mockData';

// Initial state
const initialState = {
  orders: [],
  loading: false,
  error: null,
  darkMode: false,
  filters: {
    search: '',
    dateRange: { start: '', end: '' },
    itemType: ''
  }
};

// Action types
export const actionTypes = {
  SET_LOADING: 'SET_LOADING',
  SET_ORDERS: 'SET_ORDERS',
  SET_ERROR: 'SET_ERROR',
  TOGGLE_DARK_MODE: 'TOGGLE_DARK_MODE',
  SET_FILTERS: 'SET_FILTERS',
  CLEAR_FILTERS: 'CLEAR_FILTERS'
};

// Reducer
const appReducer = (state, action) => {
  switch (action.type) {
    case actionTypes.SET_LOADING:
      return { ...state, loading: action.payload };
    case actionTypes.SET_ORDERS:
      return { ...state, orders: action.payload, loading: false, error: null };
    case actionTypes.SET_ERROR:
      return { ...state, error: action.payload, loading: false };
    case actionTypes.TOGGLE_DARK_MODE:
      return { ...state, darkMode: !state.darkMode };
    case actionTypes.SET_FILTERS:
      return { 
        ...state, 
        filters: { ...state.filters, ...action.payload } 
      };
    case actionTypes.CLEAR_FILTERS:
      return { 
        ...state, 
        filters: initialState.filters 
      };
    default:
      return state;
  }
};

// Create context
const AppContext = createContext();

// Provider component
export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Initialize with mock data
  useEffect(() => {
    dispatch({ type: actionTypes.SET_LOADING, payload: true });
    // Simulate API call delay
    setTimeout(() => {
      dispatch({ type: actionTypes.SET_ORDERS, payload: mockOrders });
    }, 1000);
  }, []);

  // Dark mode effect
  useEffect(() => {
    if (state.darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [state.darkMode]);

  // Actions
  const actions = {
    setLoading: (loading) => 
      dispatch({ type: actionTypes.SET_LOADING, payload: loading }),
    
    setOrders: (orders) => 
      dispatch({ type: actionTypes.SET_ORDERS, payload: orders }),
    
    setError: (error) => 
      dispatch({ type: actionTypes.SET_ERROR, payload: error }),
    
    toggleDarkMode: () => 
      dispatch({ type: actionTypes.TOGGLE_DARK_MODE }),
    
    setFilters: (filters) => 
      dispatch({ type: actionTypes.SET_FILTERS, payload: filters }),
    
    clearFilters: () => 
      dispatch({ type: actionTypes.CLEAR_FILTERS }),
    
    // Simulate API call for fetching orders
    fetchOrders: async () => {
      try {
        dispatch({ type: actionTypes.SET_LOADING, payload: true });
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        dispatch({ type: actionTypes.SET_ORDERS, payload: mockOrders });
      } catch (error) {
        dispatch({ type: actionTypes.SET_ERROR, payload: error.message });
      }
    },
    
    // Simulate API call for generating summary
    generateSummary: async () => {
      try {
        dispatch({ type: actionTypes.SET_LOADING, payload: true });
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1500));
        return state.orders; // Return orders for summary processing
      } catch (error) {
        dispatch({ type: actionTypes.SET_ERROR, payload: error.message });
        throw error;
      } finally {
        dispatch({ type: actionTypes.SET_LOADING, payload: false });
      }
    }
  };

  return (
    <AppContext.Provider value={{ state, actions }}>
      {children}
    </AppContext.Provider>
  );
};

// Custom hook to use the context
export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
