import React from 'react';
import { 
  Menu, 
  Bell, 
  User, 
  Settings, 
  LogOut, 
  Moon, 
  Sun,
  Search
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

/**
 * Navbar Component
 * Top navigation bar with user menu and settings
 */
const Navbar = ({ onSidebarToggle }) => {
  const { state, actions } = useApp();
  const { darkMode } = state;

  const handleLogout = () => {
    // Implementation for logout functionality
    console.log('Logout clicked');
  };

  return (
    <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
      <div className="flex items-center justify-between">
        {/* Left side */}
        <div className="flex items-center space-x-4">
          {/* Sidebar toggle button */}
          <button
            onClick={onSidebarToggle}
            className="lg:hidden p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <Menu className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>

          {/* Page title */}
          <div className="hidden sm:block">
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              WhatsApp Order Dashboard
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Manage and track your group orders
            </p>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Search bar - hidden on mobile */}
          <div className="hidden md:block relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Quick search..."
              className="form-input pl-10 pr-4 w-64"
            />
          </div>

          {/* Dark mode toggle */}
          <button
            onClick={actions.toggleDarkMode}
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
            title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {darkMode ? (
              <Sun className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            ) : (
              <Moon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            )}
          </button>

          {/* Notifications */}
          <button className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 relative">
            <Bell className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            {/* Notification badge */}
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-error-500 rounded-full"></span>
          </button>

          {/* User menu */}
          <div className="relative group">
            <button className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500">
              <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="hidden sm:block text-left">
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Admin User
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  admin@example.com
                </div>
              </div>
            </button>

            {/* Dropdown menu */}
            <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
              <div className="py-1">
                <a
                  href="#"
                  className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <User className="w-4 h-4" />
                  <span>Profile</span>
                </a>
                <a
                  href="#"
                  className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <Settings className="w-4 h-4" />
                  <span>Settings</span>
                </a>
                <hr className="my-1 border-gray-200 dark:border-gray-700" />
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 w-full px-4 py-2 text-sm text-error-600 hover:bg-error-50 dark:hover:bg-error-900"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
