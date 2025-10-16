import React from 'react';
import { TrendingUp, TrendingDown, Users, ShoppingCart, Package, Activity } from 'lucide-react';

/**
 * DashboardCards Component
 * Displays summary statistics cards
 */
const DashboardCards = ({ stats, loading = false }) => {
  const cards = [
    {
      title: 'Total Orders',
      value: stats?.totalOrders || 0,
      icon: ShoppingCart,
      color: 'blue',
      change: '+12%',
      changeType: 'increase'
    },
    {
      title: 'Total Customers',
      value: stats?.uniqueCustomers || 0,
      icon: Users,
      color: 'green',
      change: '+8%',
      changeType: 'increase'
    },
    {
      title: 'Most Ordered Item',
      value: stats?.mostOrderedItem || 'N/A',
      icon: Package,
      color: 'purple',
      change: 'Cotton Shirt',
      changeType: 'neutral'
    },
    {
      title: 'Total Quantity',
      value: stats?.totalQuantity || 0,
      icon: Activity,
      color: 'orange',
      change: '+15%',
      changeType: 'increase'
    }
  ];

  const colorClasses = {
    blue: {
      bg: 'bg-blue-50 dark:bg-blue-900',
      icon: 'bg-blue-100 dark:bg-blue-800 text-blue-600 dark:text-blue-400',
      text: 'text-blue-600 dark:text-blue-400'
    },
    green: {
      bg: 'bg-green-50 dark:bg-green-900',
      icon: 'bg-green-100 dark:bg-green-800 text-green-600 dark:text-green-400',
      text: 'text-green-600 dark:text-green-400'
    },
    purple: {
      bg: 'bg-purple-50 dark:bg-purple-900',
      icon: 'bg-purple-100 dark:bg-purple-800 text-purple-600 dark:text-purple-400',
      text: 'text-purple-600 dark:text-purple-400'
    },
    orange: {
      bg: 'bg-orange-50 dark:bg-orange-900',
      icon: 'bg-orange-100 dark:bg-orange-800 text-orange-600 dark:text-orange-400',
      text: 'text-orange-600 dark:text-orange-400'
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[...Array(4)].map((_, index) => (
          <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
            <div className="flex items-center justify-between">
              <div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 mb-2"></div>
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-16 mb-2"></div>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-12"></div>
              </div>
              <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {cards.map((card, index) => {
        const Icon = card.icon;
        const colors = colorClasses[card.color];
        
        return (
          <div
            key={index}
            className={`
              bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700
              p-6 hover:shadow-md transition-all duration-200 card-shadow
              ${colors.bg}
            `}
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                  {card.title}
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  {typeof card.value === 'number' && card.value > 999 
                    ? `${(card.value / 1000).toFixed(1)}k` 
                    : card.value
                  }
                </p>
                <div className="flex items-center text-sm">
                  {card.changeType === 'increase' && (
                    <TrendingUp className="w-3 h-3 text-green-500 mr-1" />
                  )}
                  {card.changeType === 'decrease' && (
                    <TrendingDown className="w-3 h-3 text-red-500 mr-1" />
                  )}
                  <span className={`
                    ${card.changeType === 'increase' ? 'text-green-600 dark:text-green-400' : ''}
                    ${card.changeType === 'decrease' ? 'text-red-600 dark:text-red-400' : ''}
                    ${card.changeType === 'neutral' ? 'text-gray-500 dark:text-gray-400' : ''}
                  `}>
                    {card.change}
                  </span>
                </div>
              </div>
              <div className={`
                w-12 h-12 rounded-lg flex items-center justify-center
                ${colors.icon}
              `}>
                <Icon className="w-6 h-6" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default DashboardCards;
