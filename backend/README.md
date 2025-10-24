# WhatsApp Group Order Automation - Backend

FastAPI backend for WhatsApp Group Order Management System with real-time WhatsApp integration.

## 🚀 Features

- **WhatsApp Web Integration**: Automated message parsing from WhatsApp groups
- **Real-time Order Processing**: Automatic order detection and processing
- **Customer Management**: Track customers and their order history
- **Data Export**: Excel, CSV, and PDF export capabilities
- **RESTful API**: Complete REST API for frontend integration
- **Database Support**: PostgreSQL/SQLite with SQLAlchemy ORM
- **Authentication**: JWT-based user authentication
- **Background Tasks**: Celery integration for background processing

## 📋 Prerequisites

- Python 3.8+
- Chrome/Chromium browser
- PostgreSQL (optional, SQLite works too)
- Redis (for caching and sessions)

## 🛠️ Installation

### 1. Clone and Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Database Setup

```bash
# Create database tables
python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
```

### 4. Run the Server

```bash
# Development
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📱 WhatsApp Setup

### 1. Initial Connection

1. Start the server
2. Visit `http://localhost:8000/docs`
3. Use `/api/whatsapp/connect` endpoint
4. Scan QR code in your browser
5. Select WhatsApp groups to monitor

### 2. Testing with Your Group

1. Create a test WhatsApp group
2. Add some friends/test numbers
3. Send test order messages like:
   ```
   Hi! I want to order:
   - Cotton Shirt 2 pieces
   - Denim Jeans 1 piece
   ```

4. The system will automatically:
   - Detect the order message
   - Extract customer and item information
   - Store in database
   - Make available via API

## 🔧 API Endpoints

### WhatsApp Integration
- `POST /api/whatsapp/connect` - Connect to WhatsApp Web
- `GET /api/whatsapp/groups` - Get available groups
- `POST /api/whatsapp/groups/{id}/select` - Select group to monitor
- `GET /api/whatsapp/groups/{id}/messages` - Get group messages
- `POST /api/whatsapp/groups/{id}/start-monitoring` - Start real-time monitoring

### Orders Management
- `GET /api/orders` - List orders with filtering
- `POST /api/orders` - Create new order
- `PUT /api/orders/{id}` - Update order
- `DELETE /api/orders/{id}` - Delete order
- `GET /api/orders/statistics/dashboard` - Dashboard stats

### Data Export
- `GET /api/export/excel` - Export to Excel
- `GET /api/export/csv` - Export to CSV
- `GET /api/export/summary-excel` - Customer summary Excel

### Order Summaries
- `GET /api/summaries/generate` - Generate customer summary
- `GET /api/summaries/customer-breakdown` - Detailed breakdown

## 🧪 Testing the System

### 1. Manual Testing

```bash
# Test WhatsApp bot manually
python app/whatsapp/bot.py
```

### 2. API Testing

```bash
# Install httpx for testing
pip install httpx

# Test API endpoints
python test_api.py
```

### 3. Sample Order Messages

Send these messages in your test WhatsApp group:

```
Message 1:
Hi, I want to order cotton shirt 3 pieces

Message 2:
Please book for me:
- Formal shirt 2
- Jeans 1 piece

Message 3:
मुझे चाहिए:
कॉटन शर्ट 5 पीस
जींस 2 पीस
```

## 📊 Message Processing Logic

The system automatically detects orders using:

1. **Keyword Detection**: Words like "order", "want", "need", "चाहिए", etc.
2. **Quantity Patterns**: Numbers followed by "pieces", "pc", "पीस"
3. **Product Patterns**: Product names with quantities
4. **Context Analysis**: Message structure and content

### Example Parsed Data:
```json
{
  "customer_name": "John Doe",
  "items": [
    {"item": "Cotton Shirt", "quantity": 3},
    {"item": "Denim Jeans", "quantity": 1}
  ],
  "raw_message": "Hi, I want cotton shirt 3 pieces and jeans 1"
}
```

## 🔧 Configuration

### Key Environment Variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/whatsapp_orders

# WhatsApp
WHATSAPP_SESSION_PATH=./whatsapp_sessions
WHATSAPP_HEADLESS=true

# Security
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.com
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── models.py          # Database models
│   ├── schemas.py         # Pydantic schemas
│   ├── database.py        # Database configuration
│   ├── routers/           # API route handlers
│   │   ├── whatsapp.py    # WhatsApp endpoints
│   │   ├── orders.py      # Order management
│   │   ├── export.py      # Data export
│   │   ├── summaries.py   # Order summaries
│   │   └── auth.py        # Authentication
│   └── whatsapp/          # WhatsApp integration
│       └── bot.py         # WhatsApp bot logic
├── main.py                # FastAPI application
├── requirements.txt       # Dependencies
└── .env.example          # Environment template
```

## 🚀 Production Deployment

### 1. Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Systemd Service

```ini
[Unit]
Description=WhatsApp Order API
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/backend
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🔍 Troubleshooting

### Common Issues:

1. **Chrome Driver Issues**:
   ```bash
   # Install Chrome
   sudo apt-get update
   sudo apt-get install google-chrome-stable
   ```

2. **WhatsApp Connection Failed**:
   - Check if Chrome is properly installed
   - Ensure WhatsApp Web is accessible
   - Try clearing browser cache
   - Check firewall settings

3. **Database Connection**:
   ```bash
   # Test database connection
   python -c "from app.database import test_connection; print(test_connection())"
   ```

4. **Permission Errors**:
   ```bash
   # Fix session directory permissions
   chmod -R 755 whatsapp_sessions/
   ```

## 📈 Monitoring & Logs

### Enable Logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Health Check:
```bash
curl http://localhost:8000/api/health
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review API documentation at `/docs`

---

**Happy Coding! 🚀**
