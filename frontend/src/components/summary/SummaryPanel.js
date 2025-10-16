import React, { useState } from 'react';
import { FileText, Download, Users, Package, RefreshCw } from 'lucide-react';
import { getOrdersSummary } from '../../data/mockData';

/**
 * SummaryPanel Component
 * Displays customer order summaries with export functionality
 */
const SummaryPanel = ({ orders = [], onGenerateSummary, loading = false }) => {
  const [summaryData, setSummaryData] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateSummary = async () => {
    setIsGenerating(true);
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      const summary = getOrdersSummary(orders);
      setSummaryData(summary);
      if (onGenerateSummary) {
        onGenerateSummary(summary);
      }
    } catch (error) {
      console.error('Error generating summary:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExport = (format) => {
    if (!summaryData) return;
    
    // Simulate export functionality
    console.log(`Exporting summary as ${format}...`);
    
    // In real implementation, this would call the API
    const blob = new Blob([JSON.stringify(summaryData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `summary-${new Date().toISOString().split('T')[0]}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getTotalStats = () => {
    if (!summaryData) return { customers: 0, items: 0, quantity: 0 };
    
    return {
      customers: summaryData.length,
      items: summaryData.reduce((sum, customer) => sum + customer.items.length, 0),
      quantity: summaryData.reduce((sum, customer) => sum + customer.totalQuantity, 0)
    };
  };

  const stats = getTotalStats();

  return (
    <div className="space-y-6">
      {/* Summary Generation Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Customer Order Summary
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Generate and export detailed customer order summaries
            </p>
          </div>
          <button
            onClick={handleGenerateSummary}
            disabled={isGenerating || loading}
            className="btn-primary flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${isGenerating ? 'animate-spin' : ''}`} />
            <span>{isGenerating ? 'Generating...' : 'Generate Summary'}</span>
          </button>
        </div>

        {/* Stats Cards */}
        {summaryData && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 dark:bg-blue-900 rounded-lg p-4">
              <div className="flex items-center">
                <Users className="w-8 h-8 text-blue-600 dark:text-blue-400 mr-3" />
                <div>
                  <p className="text-sm font-medium text-blue-600 dark:text-blue-400">
                    Total Customers
                  </p>
                  <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                    {stats.customers}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-green-50 dark:bg-green-900 rounded-lg p-4">
              <div className="flex items-center">
                <Package className="w-8 h-8 text-green-600 dark:text-green-400 mr-3" />
                <div>
                  <p className="text-sm font-medium text-green-600 dark:text-green-400">
                    Unique Items
                  </p>
                  <p className="text-2xl font-bold text-green-900 dark:text-green-100">
                    {stats.items}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-orange-50 dark:bg-orange-900 rounded-lg p-4">
              <div className="flex items-center">
                <FileText className="w-8 h-8 text-orange-600 dark:text-orange-400 mr-3" />
                <div>
                  <p className="text-sm font-medium text-orange-600 dark:text-orange-400">
                    Total Quantity
                  </p>
                  <p className="text-2xl font-bold text-orange-900 dark:text-orange-100">
                    {stats.quantity}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Export Buttons */}
        {summaryData && (
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => handleExport('excel')}
              className="btn-secondary flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Export Excel</span>
            </button>
            <button
              onClick={() => handleExport('csv')}
              className="btn-secondary flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Export CSV</span>
            </button>
            <button
              onClick={() => handleExport('pdf')}
              className="btn-secondary flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Export PDF</span>
            </button>
          </div>
        )}
      </div>

      {/* Summary Results */}
      {summaryData && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Customer Summary Results
            </h3>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Customer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Phone
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Items Ordered
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Total Quantity
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {summaryData.map((customer, index) => (
                  <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      {customer.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {customer.phone}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                      <div className="space-y-1">
                        {customer.items.map((item, itemIndex) => (
                          <div key={itemIndex} className="flex justify-between">
                            <span>{item.item}</span>
                            <span className="text-gray-500 dark:text-gray-400">
                              ×{item.qty}
                            </span>
                          </div>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200">
                        {customer.totalQuantity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* No Data State */}
      {!summaryData && !isGenerating && (
        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700 p-12 text-center">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No Summary Generated
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Click "Generate Summary" to create a detailed customer order summary.
          </p>
        </div>
      )}

      {/* Loading State */}
      {isGenerating && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
          <div className="spinner mx-auto mb-4"></div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Generating Summary...
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Please wait while we process your order data.
          </p>
        </div>
      )}
    </div>
  );
};

export default SummaryPanel;
