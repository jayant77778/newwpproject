# WhatsApp Group Order Automation System - Frontend

A modern, responsive React.js dashboard for managing WhatsApp group orders with real-time analytics, customer summaries, and export functionality.

## 🚀 Features

### 📊 Dashboard
- **Real-time Analytics**: Total orders, customers, most ordered items, and quantity metrics
- **Interactive Charts**: Bar charts for top items, pie charts for distribution, line charts for time trends
- **Recent Orders Table**: Quick view of latest orders with sorting and filtering

### 📦 Orders Management
- **Complete Order Tracking**: View all customer orders in a comprehensive table
- **Advanced Filtering**: Search by name, phone, item type, date range
- **Sorting & Pagination**: Sort by any column, paginate through large datasets
- **Export Options**: Download filtered orders in Excel, CSV, or PDF

### 📋 Customer Summaries
- **Automated Grouping**: Consolidate orders by customer automatically
- **Summary Generation**: One-click summary creation with customer totals
- **Multiple Export Formats**: Excel, CSV, PDF export options

### 📁 Export Center
- **Bulk Export**: Export all data or filtered subsets
- **Multiple Formats**: Support for Excel (.xlsx), CSV (.csv), and PDF (.pdf)
- **Professional Reports**: Formatted reports ready for sharing

### 🎨 Modern UI/UX
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Dark Mode**: Toggle between light and dark themes
- **Clean Interface**: Modern design with intuitive navigation
- **Loading States**: Smooth loading animations and states
- **Error Handling**: Graceful error handling with user-friendly messages

## 🛠️ Tech Stack

- **React.js 18** - Modern React with hooks and functional components
- **TailwindCSS** - Utility-first CSS framework for rapid styling
- **React Router DOM** - Client-side routing for single-page application
- **Recharts** - Responsive charts built on React components
- **Lucide React** - Beautiful, customizable icons
- **Axios** - HTTP client for API requests (ready for backend integration)
- **Context API** - Global state management

## 📁 Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── common/           # Reusable UI components
│   │   │   ├── Alert.js
│   │   │   ├── LoadingSpinner.js
│   │   │   └── SearchInput.js
│   │   ├── dashboard/        # Dashboard-specific components
│   │   │   ├── DashboardCards.js
│   │   │   └── ChartsSection.js
│   │   ├── layout/           # Layout components
│   │   │   ├── Layout.js
│   │   │   ├── Navbar.js
│   │   │   └── Sidebar.js
│   │   ├── orders/           # Order management components
│   │   │   └── OrdersTable.js
│   │   └── summary/          # Summary components
│   │       └── SummaryPanel.js
│   ├── context/              # Global state management
│   │   └── AppContext.js
│   ├── data/                 # Mock data and utilities
│   │   └── mockData.js
│   ├── hooks/                # Custom React hooks
│   │   └── index.js
│   ├── pages/                # Main application pages
│   │   ├── Dashboard.js
│   │   ├── Orders.js
│   │   ├── Summaries.js
│   │   └── Export.js
│   ├── services/             # API services
│   │   └── api.js
│   ├── utils/                # Utility functions
│   │   └── index.js
│   ├── App.js                # Main app component
│   ├── index.js              # React DOM entry point
│   └── index.css             # Global styles
├── package.json
├── tailwind.config.js
└── postcss.config.js
```

## 🚀 Getting Started

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn

### Installation

1. **Navigate to the frontend directory:**
   ```powershell
   cd "C:\Users\jai80\OneDrive\Desktop\newproject wp api\frontend"
   ```

2. **Install dependencies:**
   ```powershell
   npm install
   ```

3. **Start the development server:**
   ```powershell
   npm start
   ```

4. **Open your browser:**
   Navigate to `http://localhost:3000`

### Available Scripts

- `npm start` - Runs the app in development mode
- `npm run build` - Builds the app for production
- `npm test` - Launches the test runner
- `npm run eject` - Ejects from Create React App (irreversible)

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:3001/api
REACT_APP_APP_NAME=WhatsApp Order Dashboard
```

### API Integration
The app is ready for backend integration. Update the API base URL in `src/services/api.js`:

```javascript
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:3001/api',
  // ... other config
});
```

## 📊 Mock Data

The app includes comprehensive mock data for development and testing:

- **10 sample customers** with realistic names and phone numbers
- **Various order items** including clothing and accessories
- **Time-based ordering** to demonstrate time-series charts
- **Mixed quantities** to show distribution analytics

## 🎨 Theming

### Dark Mode
- Automatic system preference detection
- Manual toggle in the navbar
- Consistent dark theme across all components

### Color Scheme
- **Primary**: Blue (#3B82F6)
- **Success**: Green (#22C55E)
- **Warning**: Orange (#F59E0B)
- **Error**: Red (#EF4444)
- **Gray Scale**: Tailwind's gray palette

## 📱 Responsive Design

### Breakpoints
- **Mobile**: < 640px (sm)
- **Tablet**: 640px - 1024px (md/lg)
- **Desktop**: > 1024px (xl)

### Mobile Features
- Collapsible sidebar with overlay
- Touch-friendly interfaces
- Responsive tables with horizontal scroll
- Mobile-optimized navigation

## 🔌 API Endpoints (Ready for Backend)

The frontend is prepared for these API endpoints:

### Orders
- `GET /api/orders` - Fetch all orders
- `GET /api/orders?filters` - Fetch filtered orders
- `POST /api/orders` - Create new order
- `PUT /api/orders/:id` - Update order
- `DELETE /api/orders/:id` - Delete order

### Summaries
- `GET /api/summaries` - Generate customer summaries
- `GET /api/summaries?filters` - Generate filtered summaries

### Export
- `GET /api/export?type=excel` - Export to Excel
- `GET /api/export?type=csv` - Export to CSV
- `GET /api/export?type=pdf` - Export to PDF

## 🧪 Testing

The project includes mock data and utilities for testing:

1. **Component Testing**: All components are modular and testable
2. **Mock Data**: Realistic data for development
3. **Error States**: Proper error handling and display
4. **Loading States**: Loading indicators for all async operations

## 🚀 Deployment

### Build for Production
```powershell
npm run build
```

### Deploy Options
- **Netlify**: Drag and drop the `build` folder
- **Vercel**: Connect your GitHub repository
- **AWS S3**: Upload the build folder to S3 bucket
- **Traditional Hosting**: Upload build folder to web server

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **React Team** - For the amazing React framework
- **Tailwind CSS** - For the utility-first CSS framework
- **Recharts** - For beautiful React charts
- **Lucide** - For the icon library

## 📞 Support

For support, email support@example.com or create an issue in the repository.

---

**Built with ❤️ for WhatsApp Group Order Management**
