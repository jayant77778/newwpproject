import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Download, FileText, Table, FileSpreadsheet } from 'lucide-react';
import Alert from '../components/common/Alert';

/**
 * Export Page
 * Data export functionality with various format options
 */
const Export = () => {
  const { state } = useApp();
  const { orders, loading } = state;
  
  const [exportLoading, setExportLoading] = useState({});
  const [exportComplete, setExportComplete] = useState(null);

  const exportOptions = [
    {
      id: 'orders-excel',
      title: 'Orders - Excel Format',
      description: 'Complete order data in spreadsheet format',
      icon: FileSpreadsheet,
      format: 'excel',
      type: 'orders',
      color: 'green'
    },
    {
      id: 'orders-csv',
      title: 'Orders - CSV Format',
      description: 'Comma-separated values for data import',
      icon: Table,
      format: 'csv',
      type: 'orders',
      color: 'blue'
    },
    {
      id: 'orders-pdf',
      title: 'Orders - PDF Report',
      description: 'Formatted report for printing or sharing',
      icon: FileText,
      format: 'pdf',
      type: 'orders',
      color: 'red'
    },
    {
      id: 'summary-excel',
      title: 'Customer Summary - Excel',
      description: 'Customer-wise order summaries in spreadsheet',
      icon: FileSpreadsheet,
      format: 'excel',
      type: 'summary',
      color: 'purple'
    },
    {
      id: 'summary-csv',
      title: 'Customer Summary - CSV',
      description: 'Customer summaries in CSV format',
      icon: Table,
      format: 'csv',
      type: 'summary',
      color: 'orange'
    },
    {
      id: 'summary-pdf',
      title: 'Customer Summary - PDF',
      description: 'Professional summary report',
      icon: FileText,
      format: 'pdf',
      type: 'summary',
      color: 'indigo'
    }
  ];

  const handleExport = async (option) => {
    setExportLoading(prev => ({ ...prev, [option.id]: true }));
    
    try {
      // Simulate export process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Generate mock data for export
      let data;
      if (option.type === 'orders') {
        data = orders.flatMap(order => 
          order.orders.map(item => ({
            customerName: order.name,
            phone: order.phone,
            item: item.item,
            quantity: item.qty,
            time: order.time,
            date: order.date
          }))
        );
      } else {
        // Summary data
        const summaryMap = {};
        orders.forEach(order => {
          const key = order.phone;
          if (!summaryMap[key]) {
            summaryMap[key] = {
              name: order.name,
              phone: order.phone,
              items: {},
              totalQuantity: 0
            };
          }
          order.orders.forEach(item => {
            summaryMap[key].items[item.item] = (summaryMap[key].items[item.item] || 0) + item.qty;
            summaryMap[key].totalQuantity += item.qty;
          });
        });
        
        data = Object.values(summaryMap).map(customer => ({
          name: customer.name,
          phone: customer.phone,
          items: Object.entries(customer.items).map(([item, qty]) => `${item} (${qty})`).join(', '),
          totalQuantity: customer.totalQuantity
        }));
      }
      
      // Create and download file
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${option.type}-${option.format}-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      setExportComplete(option.title);
      setTimeout(() => setExportComplete(null), 3000);
      
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setExportLoading(prev => ({ ...prev, [option.id]: false }));
    }
  };

  const getColorClasses = (color) => {
    const colors = {
      green: 'bg-green-50 dark:bg-green-900 border-green-200 dark:border-green-700 text-green-800 dark:text-green-200',
      blue: 'bg-blue-50 dark:bg-blue-900 border-blue-200 dark:border-blue-700 text-blue-800 dark:text-blue-200',
      red: 'bg-red-50 dark:bg-red-900 border-red-200 dark:border-red-700 text-red-800 dark:text-red-200',
      purple: 'bg-purple-50 dark:bg-purple-900 border-purple-200 dark:border-purple-700 text-purple-800 dark:text-purple-200',
      orange: 'bg-orange-50 dark:bg-orange-900 border-orange-200 dark:border-orange-700 text-orange-800 dark:text-orange-200',
      indigo: 'bg-indigo-50 dark:bg-indigo-900 border-indigo-200 dark:border-indigo-700 text-indigo-800 dark:text-indigo-200'
    };
    return colors[color] || colors.blue;
  };

  const getIconColorClass = (color) => {
    const colors = {
      green: 'text-green-600 dark:text-green-400',
      blue: 'text-blue-600 dark:text-blue-400',
      red: 'text-red-600 dark:text-red-400',
      purple: 'text-purple-600 dark:text-purple-400',
      orange: 'text-orange-600 dark:text-orange-400',
      indigo: 'text-indigo-600 dark:text-indigo-400'
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Export Data
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Download your order data in various formats
        </p>
      </div>

      {/* Export Success Alert */}
      {exportComplete && (
        <Alert
          type="success"
          title="Export Completed"
          message={`${exportComplete} has been downloaded successfully.`}
          onClose={() => setExportComplete(null)}
        />
      )}

      {/* Export Statistics */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Available Data
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-primary-600 dark:text-primary-400">
              {orders.length}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Total Orders
            </div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {new Set(orders.map(order => order.phone)).size}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Unique Customers
            </div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
              {orders.reduce((sum, order) => sum + order.orders.reduce((orderSum, item) => orderSum + item.qty, 0), 0)}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Total Items
            </div>
          </div>
        </div>
      </div>

      {/* Export Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {exportOptions.map((option) => {
          const Icon = option.icon;
          const isLoading = exportLoading[option.id];
          
          return (
            <div
              key={option.id}
              className={`
                border rounded-lg p-6 hover:shadow-md transition-all duration-200 cursor-pointer
                ${getColorClasses(option.color)}
              `}
              onClick={() => !isLoading && !loading && handleExport(option)}
            >
              <div className="flex items-start space-x-4">
                <div className={`
                  w-12 h-12 rounded-lg flex items-center justify-center
                  ${isLoading ? 'animate-pulse' : ''}
                `}>
                  {isLoading ? (
                    <div className="spinner"></div>
                  ) : (
                    <Icon className={`w-6 h-6 ${getIconColorClass(option.color)}`} />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-medium mb-1">
                    {option.title}
                  </h3>
                  <p className="text-sm opacity-75 mb-3">
                    {option.description}
                  </p>
                  <button
                    disabled={isLoading || loading}
                    className={`
                      flex items-center space-x-2 text-sm font-medium
                      ${isLoading || loading 
                        ? 'opacity-50 cursor-not-allowed' 
                        : 'hover:underline'
                      }
                    `}
                  >
                    <Download className="w-4 h-4" />
                    <span>
                      {isLoading ? 'Exporting...' : `Download ${option.format.toUpperCase()}`}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Export Help */}
      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
          Export Formats Guide
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white mb-2">Excel (.xlsx)</h4>
            <p className="text-gray-600 dark:text-gray-400">
              Best for data analysis, calculations, and sharing with teams who use Microsoft Office.
            </p>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white mb-2">CSV (.csv)</h4>
            <p className="text-gray-600 dark:text-gray-400">
              Universal format compatible with all spreadsheet applications and databases.
            </p>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 dark:text-white mb-2">PDF (.pdf)</h4>
            <p className="text-gray-600 dark:text-gray-400">
              Professional reports perfect for printing, sharing, or archiving.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Export;
