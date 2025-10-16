import React from 'react';
import { useApp } from '../context/AppContext';
import SummaryPanel from '../components/summary/SummaryPanel';
import Alert from '../components/common/Alert';

/**
 * Summaries Page
 * Customer order summaries with export functionality
 */
const Summaries = () => {
  const { state, actions } = useApp();
  const { orders, loading, error } = state;

  const handleGenerateSummary = (summaryData) => {
    console.log('Summary generated:', summaryData);
    // Additional handling if needed
  };

  if (error) {
    return (
      <div className="p-6">
        <Alert
          type="error"
          title="Error Loading Data"
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
            Customer Summaries
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Generate and export detailed customer order summaries
          </p>
        </div>
      </div>

      {/* Summary Panel */}
      <SummaryPanel 
        orders={orders}
        onGenerateSummary={handleGenerateSummary}
        loading={loading}
      />

      {/* Help Section */}
      <div className="bg-blue-50 dark:bg-blue-900 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 dark:text-blue-100 mb-2">
          How to use Customer Summaries
        </h3>
        <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
          <li>• Click "Generate Summary" to create a consolidated view of all customer orders</li>
          <li>• Each customer's orders are grouped together with total quantities</li>
          <li>• Export summaries in Excel, CSV, or PDF format for sharing</li>
          <li>• Use this for order fulfillment and customer communication</li>
        </ul>
      </div>
    </div>
  );
};

export default Summaries;
