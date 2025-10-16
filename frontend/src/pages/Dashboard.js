import React, { useEffect, useMemo } from 'react';
import { useApp } from '../context/AppContext';
import DashboardCards from '../components/dashboard/DashboardCards';
import ChartsSection from '../components/dashboard/ChartsSection';
import OrdersTable from '../components/orders/OrdersTable';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Alert from '../components/common/Alert';
import { 
  getDashboardStats, 
  getTopItems, 
  getOrdersOverTime 
} from '../data/mockData';

/**
 * Dashboard Page
 * Main dashboard with overview cards, charts, and recent orders
 */
const Dashboard = () => {
  const { state, actions } = useApp();
  const { orders, loading, error } = state;

  // Calculate dashboard statistics
  const dashboardStats = useMemo(() => {
    return getDashboardStats(orders);
  }, [orders]);

  // Get chart data
  const topItems = useMemo(() => {
    return getTopItems(orders, 10);
  }, [orders]);

  const ordersOverTime = useMemo(() => {
    return getOrdersOverTime(orders);
  }, [orders]);

  // Get recent orders for table (last 10)
  const recentOrders = useMemo(() => {
    return orders.slice(-10).reverse();
  }, [orders]);

  useEffect(() => {
    // Fetch orders on component mount if not already loaded
    if (orders.length === 0 && !loading) {
      actions.fetchOrders();
    }
  }, [orders.length, loading, actions]);

  if (error) {
    return (
      <div className="p-6">
        <Alert
          type="error"
          title="Error Loading Dashboard"
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
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Overview of your WhatsApp group orders
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex space-x-3">
          <button
            onClick={() => actions.fetchOrders()}
            disabled={loading}
            className="btn-secondary flex items-center space-x-2"
          >
            <span>Refresh Data</span>
          </button>
        </div>
      </div>

      {/* Dashboard Cards */}
      <DashboardCards stats={dashboardStats} loading={loading} />

      {/* Charts Section */}
      <ChartsSection 
        topItems={topItems}
        ordersOverTime={ordersOverTime}
        loading={loading}
      />

      {/* Recent Orders Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Recent Orders
            </h2>
            <a
              href="/orders"
              className="text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              View All →
            </a>
          </div>
        </div>
        
        {loading ? (
          <LoadingSpinner text="Loading recent orders..." />
        ) : (
          <div className="p-6">
            <OrdersTable 
              orders={recentOrders}
              showFilters={false}
              showPagination={false}
              pageSize={5}
            />
          </div>
        )}
      </div>

      {/* Quick Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
          <h3 className="text-lg font-semibold mb-2">Today's Orders</h3>
          <p className="text-3xl font-bold">{dashboardStats.totalOrders}</p>
          <p className="text-blue-100 text-sm">
            {dashboardStats.totalOrders > 0 ? '+12% from yesterday' : 'No orders yet today'}
          </p>
        </div>

        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
          <h3 className="text-lg font-semibold mb-2">Active Customers</h3>
          <p className="text-3xl font-bold">{dashboardStats.uniqueCustomers}</p>
          <p className="text-green-100 text-sm">
            {dashboardStats.uniqueCustomers > 0 ? 'Engaged customers' : 'No customers yet'}
          </p>
        </div>

        <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg p-6 text-white">
          <h3 className="text-lg font-semibold mb-2">Top Item</h3>
          <p className="text-xl font-bold">{dashboardStats.mostOrderedItem}</p>
          <p className="text-purple-100 text-sm">
            Most popular item today
          </p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
