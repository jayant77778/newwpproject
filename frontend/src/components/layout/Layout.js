import React, { useState } from 'react';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

/**
 * Layout Component
 * Main layout wrapper with navbar and sidebar
 */
const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onToggle={toggleSidebar} />
      
      {/* Main content area */}
      <div className="lg:ml-64">
        {/* Navbar */}
        <Navbar onSidebarToggle={toggleSidebar} />
        
        {/* Page content */}
        <main className="p-4 lg:p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
