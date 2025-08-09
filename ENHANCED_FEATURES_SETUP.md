# Returns Management SaaS - Enhanced Features Setup Guide

## Overview

The Returns Management SaaS has been enhanced with powerful new features:

1. **Local-First / Offline Mode**: Full functionality without external dependencies
2. **Real Shopify Integration**: OAuth with live data sync + offline fallback 
3. **Email Notifications**: Automated customer and merchant notifications
4. **AI-Powered Suggestions**: Intelligent return reason recommendations
5. **Advanced Export**: PDF, CSV, and Excel report generation

## 🚀 Quick Start

### Current Status
- ✅ **Online Mode**: Full functionality with MongoDB backend
- ✅ **Offline Fallback**: Mock data when services unavailable  
- ✅ **Shopify OAuth**: Real integration with provided credentials
- ✅ **Enhanced Features**: Email, AI, and Export ready

### Accessing the Application
- **Merchant Dashboard**: https://your-domain.com
- **Customer Portal**: https://your-domain.com/customer
- **Settings & Integration**: Navigate to "Settings" tab in merchant dashboard

## 🛠️ Feature Configuration

### 1. Shopify Integration

#### OAuth Credentials (Pre-configured)
```env
SHOPIFY_CLIENT_ID=81e556a66ac6d28a54e1ed972a3c43ad
SHOPIFY_CLIENT_SECRET=d23f49ea8d18e93a8a26c2c04dba826c
```

#### Setup Instructions:
1. Go to **Settings → Shopify Integration**
2. Enter your shop domain (e.g., "demo-store")  
3. Click "Connect to Shopify"
4. Complete OAuth flow in new window
5. Data will sync automatically

#### Offline Mode:
- Set `OFFLINE_MODE=true` in backend/.env
- Uses mock data from `/app/mock_data/`
- All features work identically offline

### 2. Email Notifications

#### Required Environment Variables:
```env
# Gmail Example
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
FROM_EMAIL=noreply@yourstore.com
FROM_NAME=Your Store Name
```

#### Testing:
1. Go to **Settings → Enhanced Features → Email**
2. Enter test email address
3. Click "Send Test"
4. Check inbox for test message

#### Supported Email Providers:
- **Gmail**: smtp.gmail.com (use App Password)
- **Outlook**: smtp-mail.outlook.com  
- **Yahoo**: smtp.mail.yahoo.com
- **Custom SMTP**: Any compliant server

### 3. AI-Powered Features

#### OpenAI Integration (Optional):
```env
OPENAI_API_KEY=sk-your-openai-key-here
```

#### Local Fallback:
- Works without OpenAI key
- Uses rule-based AI algorithms
- Same functionality, different intelligence source

#### Features:
- **Return Reason Suggestions**: Analyze products for likely return reasons
- **Upsell Message Generation**: Create compelling alternative offers
- **Pattern Analysis**: Insights into return trends and recommendations

### 4. Export & Reporting

#### Available Formats:
- **CSV**: Raw data for spreadsheet analysis
- **PDF**: Professional formatted reports with charts
- **Excel**: Multi-sheet analytics workbooks

#### Usage:
1. Go to **Settings → Enhanced Features → Export**
2. Choose format and time period
3. Click export to download file

## 📁 Project Structure

### New Backend Services
```
/app/backend/src/
├── services/
│   ├── shopify_service.py      # Shopify API + offline fallback
│   ├── email_service.py        # SMTP email notifications  
│   ├── ai_service.py          # OpenAI + local AI features
│   └── export_service.py      # PDF/CSV/Excel generation
├── controllers/
│   ├── shopify_controller.py          # OAuth & webhooks
│   └── enhanced_features_controller.py # Email, AI, Export APIs
└── config/
    └── shopify.py             # OAuth configuration
```

### Mock Data (Offline Mode)
```
/app/mock_data/
├── orders_demo-store.json     # Sample Shopify orders
├── products_demo-store.json   # Sample Shopify products
└── [shop-name].json          # Auto-generated for each shop
```

### Enhanced Frontend
```
/app/frontend/src/components/
├── ShopifyIntegration.js      # OAuth flow & connection status
├── EnhancedFeatures.js        # Email, AI, Export interfaces
└── CustomerPortal.js          # Self-service return portal
```

## 🔧 API Endpoints

### Shopify Integration
```
GET  /api/shopify/install              # Initiate OAuth
GET  /api/shopify/callback             # OAuth callback  
POST /api/shopify/sync                 # Manual data sync
GET  /api/shopify/connection-status    # Check connection
```

### Enhanced Features
```
# Email
POST /api/enhanced/email/test          # Send test email
GET  /api/enhanced/email/settings      # Get SMTP status

# AI
POST /api/enhanced/ai/suggest-reasons  # Get return suggestions
POST /api/enhanced/ai/generate-upsell  # Generate upsell text
GET  /api/enhanced/ai/analyze-patterns # Return analytics

# Export  
GET  /api/enhanced/export/returns/csv  # Export CSV
GET  /api/enhanced/export/returns/pdf  # Export PDF report
GET  /api/enhanced/export/analytics/excel # Export Excel analytics
```

## 🔒 Security & Privacy

### API Key Storage
- Shopify tokens encrypted in MongoDB
- OpenAI API key in environment variables only  
- SMTP credentials never logged

### Multi-Tenant Isolation
- All data scoped by tenant_id
- Shopify connections isolated per merchant
- Export data filtered by tenant

### Offline Mode Security
- Mock data contains no real customer information
- Webhook signatures verified (real mode only)
- Local algorithms for AI suggestions

## 🧪 Testing

### Manual Testing Checklist

#### Shopify Integration:
- [ ] OAuth flow completes successfully
- [ ] Connection status shows "Connected" 
- [ ] Data sync imports orders and products
- [ ] Offline mode uses mock data when connection fails

#### Email Notifications:
- [ ] Test email sends successfully
- [ ] Return status changes trigger notifications  
- [ ] Email templates render correctly
- [ ] SMTP errors handled gracefully

#### AI Features:
- [ ] Return reason suggestions work with and without OpenAI
- [ ] Upsell messages generate appropriately
- [ ] Pattern analysis provides insights
- [ ] Local fallback works when OpenAI unavailable

#### Export Features:
- [ ] CSV exports download correctly
- [ ] PDF reports format properly
- [ ] Excel files open with multiple sheets
- [ ] Date filtering works accurately

### Automated Testing:
```bash
# Backend API tests
cd /app && python -m pytest tests/

# Frontend tests (if implemented)
cd /app/frontend && npm test
```

## 🚨 Troubleshooting

### Common Issues:

#### Shopify Connection Fails:
- Verify shop domain format (no .myshopify.com)
- Check OAuth credentials in .env file
- Ensure shop exists and is accessible
- Try offline mode if Shopify is down

#### Email Tests Fail:
- Verify SMTP settings in .env
- For Gmail, use App Password not regular password
- Check firewall/proxy settings
- Test SMTP connection manually

#### AI Suggestions Not Working:
- Verify OpenAI API key if using OpenAI
- Check API quota and billing
- Local fallback should work without OpenAI
- Ensure product data is provided

#### Export Downloads Fail:
- Check browser popup blockers
- Verify tenant permissions
- Try different export formats
- Check backend logs for errors

### Debug Commands:
```bash
# Check backend logs
tail -f /var/log/supervisor/backend.err.log

# Restart services
sudo supervisorctl restart all

# Test API endpoints
curl -X GET "http://localhost:8001/api/enhanced/status"

# Check MongoDB connection
mongo --eval "db.stats()"
```

## 🔄 Deployment Notes

### Environment Variables Checklist:
```env
# Database (Required)
MONGO_URL=mongodb://localhost:27017
DB_NAME=returns_management

# Shopify (Required for real integration)  
SHOPIFY_CLIENT_ID=81e556a66ac6d28a54e1ed972a3c43ad
SHOPIFY_CLIENT_SECRET=d23f49ea8d18e93a8a26c2c04dba826c

# Email (Optional - disables notifications if missing)
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourstore.com

# AI (Optional - uses local fallback if missing)
OPENAI_API_KEY=sk-your-key-here

# Mode Configuration
OFFLINE_MODE=false
DEBUG=true
```

### Production Considerations:
- Use encrypted environment variable storage
- Implement proper SSL certificates
- Set up monitoring for Shopify webhooks
- Configure email sending limits
- Monitor OpenAI API usage and costs
- Regular database backups including Shopify tokens

## 📞 Support

### Documentation:
- `/app/docs/DATABASE_SCHEMA.md` - Complete database documentation
- `/app/tests/README.md` - Testing instructions
- `/app/PROJECT_COMPLETE.md` - Full project overview

### Getting Help:
1. Check this setup guide first
2. Review backend logs for errors  
3. Test individual components in isolation
4. Verify all environment variables are set
5. Try offline mode to isolate issues

The enhanced Returns Management SaaS provides a complete, production-ready solution with both online and offline capabilities. All features are designed to work seamlessly together while maintaining the flexibility to operate independently when needed.