import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  ShoppingCart, 
  FileText, 
  Download,
  Menu,
  X
} from 'lucide-react';

/**
 * Sidebar Component
 * Navigation sidebar with collapsible functionality
 */
const Sidebar = ({ isOpen, onToggle }) => {
  const location = useLocation();

  const menuItems = [
    {
      path: '/',
      icon: LayoutDashboard,
      label: 'Dashboard',
      description: 'Overview and analytics'
    },
    {
      path: '/orders',
      icon: ShoppingCart,
      label: 'Orders',
      description: 'Manage all orders'
    },
    {
      path: '/summaries',
      icon: FileText,
      label: 'Summaries',
      description: 'Customer summaries'
    },
    {
      path: '/export',
      icon: Download,
      label: 'Export',
      description: 'Download reports'
    }
  ];

  const isActivePath = (path) => {
    return location.pathname === path;
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed top-0 left-0 h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700
        transform transition-transform duration-300 ease-in-out z-50
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static lg:h-auto
        w-64 flex flex-col
      `}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <ShoppingCart className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                OrderApp
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                WhatsApp Orders
              </p>
            </div>
          </div>
          <button
            onClick={onToggle}
            className="lg:hidden p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = isActivePath(item.path);
            
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => {
                  // Close sidebar on mobile after navigation
                  if (window.innerWidth < 1024) {
                    onToggle();
                  }
                }}
                className={`
                  flex items-center space-x-3 px-3 py-3 rounded-lg transition-all duration-200
                  group hover:bg-gray-100 dark:hover:bg-gray-700
                  ${isActive 
                    ? 'bg-primary-50 dark:bg-primary-900 text-primary-700 dark:text-primary-300 border-r-2 border-primary-600' 
                    : 'text-gray-700 dark:text-gray-300'
                  }
                `}
              >
                <Icon className={`
                  w-5 h-5 transition-colors duration-200
                  ${isActive 
                    ? 'text-primary-600 dark:text-primary-400' 
                    : 'text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-300'
                  }
                `} />
                <div className="flex-1">
                  <div className={`
                    font-medium text-sm
                    ${isActive ? 'text-primary-700 dark:text-primary-300' : ''}
                  `}>
                    {item.label}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {item.description}
                  </div>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
            © 2024 WhatsApp Order System
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
