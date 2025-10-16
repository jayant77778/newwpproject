import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Orders from './pages/Orders';
import Summaries from './pages/Summaries';
import Export from './pages/Export';

/**
 * Main App Component
 * Root component with routing and global state management
 */
function App() {
  return (
    <AppProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/summaries" element={<Summaries />} />
            <Route path="/export" element={<Export />} />
          </Routes>
        </Layout>
      </Router>
    </AppProvider>
  );
}

export default App;
