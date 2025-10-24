# WhatsApp Group Order Automation System

A complete React.js frontend for managing WhatsApp group orders with a modern dashboard interface.

## 🚀 Features

- **Modern Dashboard** - Clean, responsive UI with dark mode support
- **Order Management** - View, filter, and search through orders
- **Customer Summaries** - Generate and export customer-wise summaries
- **Data Export** - Export to Excel, CSV, and PDF formats
- **Real-time Charts** - Visual analytics with Recharts
- **Mobile Responsive** - Works perfectly on all devices

## 🛠️ Tech Stack

- **Frontend**: React.js 18, TailwindCSS, React Router
- **Charts**: Recharts
- **Icons**: Lucide React
- **API**: Axios for HTTP requests
- **State Management**: Context API + useReducer

## 📦 Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/jayant77778/wp_automation.git
cd wp_automation
```

2. Install dependencies:
```bash
cd frontend
npm install
```

3. Start the development server:
```bash
npm start
```

The app will be available at `http://localhost:3000`

### Production Build

```bash
cd frontend
npm run build
```

## 🌐 Deployment

### Vercel Deployment

This project is configured for easy deployment on Vercel:

1. Push your code to GitHub
2. Connect your GitHub repository to Vercel
3. Vercel will automatically detect the configuration and deploy

The project includes:
- `vercel.json` configuration for proper routing
- Optimized build settings for React apps
- Environment variables setup

### Manual Deployment

You can also deploy using Vercel CLI:

```bash
npm install -g vercel
vercel --prod
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:3001/api
REACT_APP_APP_NAME=WhatsApp Order Dashboard
REACT_APP_VERSION=1.0.0
```

### API Integration

The app is designed to work with a backend API. Update the API URL in:
- `.env` files for different environments
- `src/services/api.js` for API endpoints

## 📱 Usage

1. **Dashboard**: Overview of orders, customers, and analytics
2. **Orders**: Detailed view of all orders with filtering and search
3. **Summaries**: Customer-wise order summaries with export options
4. **Export**: Download data in various formats

## 🎨 UI Components

- **Responsive Layout** with collapsible sidebar
- **Dark Mode Support** with theme toggle
- **Interactive Charts** showing order analytics
- **Sortable Tables** with pagination
- **Search & Filter** functionality
- **Loading States** and error handling

## 📊 Mock Data

The app includes comprehensive mock data for development and demonstration:
- 10+ sample customers with realistic orders
- Various clothing items (shirts, jeans, sarees, etc.)
- Time-based order data for analytics

## 🔗 Links

- **Live Demo**: [Deployed on Vercel](https://wp-automation-git-main-jayant77778s-projects.vercel.app)
- **GitHub Repository**: [https://github.com/jayant77778/wp_automation](https://github.com/jayant77778/wp_automation)

## 📄 License

MIT License - feel free to use this project for your own purposes.
# newwpproject
