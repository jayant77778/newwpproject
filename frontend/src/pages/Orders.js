import React, { useState, useMemo } from 'react';
import { useApp } from '../context/AppContext';
import OrdersTable from '../components/orders/OrdersTable';
import SearchInput from '../components/common/SearchInput';
import Alert from '../components/common/Alert';
import { Filter, Download, RefreshCw, Calendar } from 'lucide-react';

/**
 * Orders Page
 * Complete orders management with filtering and export
 */
const Orders = () => {
  const { state, actions } = useApp();
  const { orders, loading, error } = state;
  
  const [filters, setFilters] = useState({
    search: '',
    itemType: '',
    dateRange: { start: '', end: '' },
    customer: ''
  });
  
  const [showFilters, setShowFilters] = useState(false);

  // Get unique values for filters
  const filterOptions = useMemo(() => {
    const itemTypes = new Set();
    const customers = new Set();
    
    orders.forEach(order => {
      customers.add(order.name);
      order.orders.forEach(item => {
        itemTypes.add(item.item);
      });
    });
    
    return {
      itemTypes: Array.from(itemTypes).sort(),
      customers: Array.from(customers).sort()
    };
  }, [orders]);

  // Filter orders based on current filters
  const filteredOrders = useMemo(() => {
    let filtered = orders;

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(order => 
        order.name.toLowerCase().includes(searchLower) ||
        order.phone.includes(filters.search) ||
        order.orders.some(item => item.item.toLowerCase().includes(searchLower))
      );
    }

    // Customer filter
    if (filters.customer) {
      filtered = filtered.filter(order => order.name === filters.customer);
    }

    // Item type filter
    if (filters.itemType) {
      filtered = filtered.filter(order => 
        order.orders.some(item => item.item === filters.itemType)
      );
    }

    // Date range filter
    if (filters.dateRange.start || filters.dateRange.end) {
      filtered = filtered.filter(order => {
        const orderDate = new Date(order.date);
        const startDate = filters.dateRange.start ? new Date(filters.dateRange.start) : null;
        const endDate = filters.dateRange.end ? new Date(filters.dateRange.end) : null;
        
        if (startDate && orderDate < startDate) return false;
        if (endDate && orderDate > endDate) return false;
        return true;
      });
    }

    return filtered;
  }, [orders, filters]);

  const handleExport = (format) => {
    console.log(`Exporting ${filteredOrders.length} orders as ${format}...`);
    
    // Simulate export
    const data = filteredOrders.map(order => ({
      name: order.name,
      phone: order.phone,
      items: order.orders.map(item => `${item.item} (${item.qty})`).join(', '),
      time: order.time,
      date: order.date
    }));
    
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `orders-${new Date().toISOString().split('T')[0]}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      itemType: '',
      dateRange: { start: '', end: '' },
      customer: ''
    });
  };

  const hasActiveFilters = Object.values(filters).some(filter => {
    if (typeof filter === 'object') {
      return Object.values(filter).some(val => val !== '');
    }
    return filter !== '';
  });

  if (error) {
    return (
      <div className="p-6">
        <Alert
          type="error"
          title="Error Loading Orders"
          message={error}
          onClose={() => actions.setError(null)}
          actions={
            <button
              onClick={() => actions.fetchOrders()}
              className="btn-primary text-sm"
            >
              Retry
            </button>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Orders Management
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            View and manage all customer orders
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex space-x-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn-secondary flex items-center space-x-2 ${showFilters ? 'bg-primary-50 text-primary-700' : ''}`}
          >
            <Filter className="w-4 h-4" />
            <span>Filters</span>
          </button>
          <button
            onClick={() => actions.fetchOrders()}
            disabled={loading}
            className="btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filters Section */}
      {showFilters && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Search
              </label>
              <SearchInput
                value={filters.search}
                onChange={(value) => setFilters(prev => ({ ...prev, search: value }))}
                placeholder="Search orders..."
              />
            </div>

            {/* Customer Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Customer
              </label>
              <select
                value={filters.customer}
                onChange={(e) => setFilters(prev => ({ ...prev, customer: e.target.value }))}
                className="form-input"
              >
                <option value="">All Customers</option>
                {filterOptions.customers.map(customer => (
                  <option key={customer} value={customer}>{customer}</option>
                ))}
              </select>
            </div>

            {/* Item Type Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Item Type
              </label>
              <select
                value={filters.itemType}
                onChange={(e) => setFilters(prev => ({ ...prev, itemType: e.target.value }))}
                className="form-input"
              >
                <option value="">All Items</option>
                {filterOptions.itemTypes.map(item => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </div>

            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Date Range
              </label>
              <div className="space-y-2">
                <input
                  type="date"
                  value={filters.dateRange.start}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    dateRange: { ...prev.dateRange, start: e.target.value }
                  }))}
                  className="form-input"
                  placeholder="Start date"
                />
                <input
                  type="date"
                  value={filters.dateRange.end}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    dateRange: { ...prev.dateRange, end: e.target.value }
                  }))}
                  className="form-input"
                  placeholder="End date"
                />
              </div>
            </div>
          </div>

          {/* Filter Actions */}
          <div className="mt-4 flex items-center justify-between">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {filteredOrders.length} of {orders.length} orders shown
            </div>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>
      )}

      {/* Export Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Export Orders
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Download filtered orders in various formats
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => handleExport('excel')}
              className="btn-secondary flex items-center space-x-2"
              disabled={filteredOrders.length === 0}
            >
              <Download className="w-4 h-4" />
              <span>Excel</span>
            </button>
            <button
              onClick={() => handleExport('csv')}
              className="btn-secondary flex items-center space-x-2"
              disabled={filteredOrders.length === 0}
            >
              <Download className="w-4 h-4" />
              <span>CSV</span>
            </button>
            <button
              onClick={() => handleExport('pdf')}
              className="btn-secondary flex items-center space-x-2"
              disabled={filteredOrders.length === 0}
            >
              <Download className="w-4 h-4" />
              <span>PDF</span>
            </button>
          </div>
        </div>
      </div>

      {/* Orders Table */}
      <OrdersTable 
        orders={filteredOrders}
        loading={loading}
        showFilters={false}
        showPagination={true}
        pageSize={20}
      />

      {/* No Orders State */}
      {!loading && filteredOrders.length === 0 && orders.length > 0 && (
        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700 p-12 text-center">
          <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No orders found
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Try adjusting your filters to see more results.
          </p>
          <button
            onClick={clearFilters}
            className="btn-primary"
          >
            Clear Filters
          </button>
        </div>
      )}
    </div>
  );
};

export default Orders;
