# 📮 Postman Setup Guide

Guide untuk menggunakan Postman dengan API Adaptive PDF Data Extraction System.

---

## 🚀 Quick Setup

### Method 1: Import OpenAPI Spec (Recommended)

1. **Open Postman**
2. **Click "Import"** (top left)
3. **Select "Link"** tab
4. **Paste URL**: `http://localhost:8000/apispec.json`
5. **Click "Continue"** → **"Import"**

✅ **Done!** All endpoints akan ter-import otomatis dengan dokumentasi lengkap.

---

### Method 2: Manual Collection

Download dan import file collection (jika tersedia):
- File: `Adaptive_PDF_Extraction_API.postman_collection.json`
- Import via: Postman → Import → File

---

## 🔐 Setup Authentication

### 1. Create Environment

**Postman → Environments → Create Environment**

**Variables:**
```
base_url: http://localhost:8000
token: (will be set automatically)
template_id: 1
document_id: (will be set after extraction)
```

### 2. Get JWT Token

**Request:**
```
POST {{base_url}}/api/v1/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Save Token Script** (Tests tab):
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("token", jsonData.data.token);
    console.log("Token saved:", jsonData.data.token);
}
```

### 3. Use Token in Requests

**Authorization Tab:**
- Type: `Bearer Token`
- Token: `{{token}}`

Or **Headers:**
```
Authorization: Bearer {{token}}
```

---

## 📋 Common Request Examples

### 1. Health Check
```
GET {{base_url}}/api/health
```

### 2. List Templates
```
GET {{base_url}}/api/v1/templates
Authorization: Bearer {{token}}
```

### 3. Extract Document
```
POST {{base_url}}/api/v1/extraction/extract
Authorization: Bearer {{token}}
Content-Type: multipart/form-data

Body (form-data):
- file: [Select PDF file]
- template_id: {{template_id}}
```

**Save Document ID Script** (Tests tab):
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("document_id", jsonData.data.document_id);
    console.log("Document ID saved:", jsonData.data.document_id);
}
```

### 4. Submit Feedback
```
POST {{base_url}}/api/v1/extraction/feedback
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "document_id": {{document_id}},
  "corrections": {
    "recipient_name": "Corrected Name",
    "issue_date": "2024-01-20"
  }
}
```

### 5. Train Model
```
POST {{base_url}}/api/v1/learning/train
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "template_id": {{template_id}},
  "use_all_feedback": true,
  "is_incremental": false,
  "force_validation": false
}
```

### 6. Get Strategy Performance
```
GET {{base_url}}/api/v1/templates/{{template_id}}/strategy-performance/stats
Authorization: Bearer {{token}}
```

---

## 🔄 Complete Workflow Collection

### Collection Structure
```
📁 Adaptive PDF Extraction API
├─ 📁 Auth
│  ├─ Register User
│  └─ Login (saves token)
├─ 📁 Templates
│  ├─ List Templates
│  ├─ Get Template
│  ├─ Create Template
│  ├─ Update Template
│  └─ Delete Template
├─ 📁 Extraction
│  ├─ Extract Document (saves document_id)
│  ├─ Get Document
│  ├─ List Documents
│  └─ Submit Feedback
├─ 📁 Learning
│  ├─ Train Model
│  ├─ Get Model Info
│  └─ Training History
├─ 📁 Strategy Performance
│  ├─ Get All Performance
│  ├─ Get Statistics
│  ├─ Get Field Comparison
│  ├─ Get All Fields Comparison
│  ├─ Get Best Strategies
│  └─ Get Strategy Details
├─ 📁 Data Quality
│  ├─ Get Latest Metrics
│  └─ Get Metrics History
└─ 📁 Utilities
   ├─ Health Check
   └─ Generate Preview
```

---

## 🧪 Pre-request Scripts

### Global Setup (Collection level)
```javascript
// Set base URL if not in environment
if (!pm.environment.get("base_url")) {
    pm.environment.set("base_url", "http://localhost:8000");
}

// Add timestamp to requests
pm.request.headers.add({
    key: "X-Request-Time",
    value: new Date().toISOString()
});
```

### Auto-refresh Token
```javascript
// Check if token is expired (if you have expiry logic)
const token = pm.environment.get("token");
if (!token || isTokenExpired(token)) {
    // Trigger login request
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/api/v1/auth/login",
        method: "POST",
        header: {
            "Content-Type": "application/json"
        },
        body: {
            mode: "raw",
            raw: JSON.stringify({
                username: pm.environment.get("username"),
                password: pm.environment.get("password")
            })
        }
    }, function(err, res) {
        if (!err && res.code === 200) {
            const jsonData = res.json();
            pm.environment.set("token", jsonData.data.token);
        }
    });
}
```

---

## 📊 Test Scripts

### Generic Success Test
```javascript
pm.test("Status code is 200", function() {
    pm.response.to.have.status(200);
});

pm.test("Response has success field", function() {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property("success");
    pm.expect(jsonData.success).to.be.true;
});

pm.test("Response time is less than 2000ms", function() {
    pm.expect(pm.response.responseTime).to.be.below(2000);
});
```

### Extraction Test
```javascript
pm.test("Extraction successful", function() {
    var jsonData = pm.response.json();
    pm.expect(jsonData.success).to.be.true;
    pm.expect(jsonData.data).to.have.property("document_id");
    pm.expect(jsonData.data).to.have.property("extracted_data");
    
    // Save document ID for next requests
    pm.environment.set("document_id", jsonData.data.document_id);
});

pm.test("All fields extracted", function() {
    var jsonData = pm.response.json();
    var extractedData = jsonData.data.extracted_data;
    pm.expect(Object.keys(extractedData).length).to.be.above(0);
});
```

### Strategy Performance Test
```javascript
pm.test("Strategy stats available", function() {
    var jsonData = pm.response.json();
    pm.expect(jsonData.data).to.be.an("array");
    pm.expect(jsonData.data.length).to.be.above(0);
    
    // Check CRF strategy exists
    var crfStrategy = jsonData.data.find(s => s.strategy_type === "crf");
    pm.expect(crfStrategy).to.exist;
    pm.expect(crfStrategy.avg_accuracy).to.be.a("number");
});
```

---

## 🎯 Environment Variables Reference

### Development Environment
```json
{
  "name": "Development",
  "values": [
    {
      "key": "base_url",
      "value": "http://localhost:8000",
      "enabled": true
    },
    {
      "key": "token",
      "value": "",
      "enabled": true
    },
    {
      "key": "template_id",
      "value": "1",
      "enabled": true
    },
    {
      "key": "document_id",
      "value": "",
      "enabled": true
    },
    {
      "key": "username",
      "value": "test_user",
      "enabled": true
    },
    {
      "key": "password",
      "value": "test_password",
      "enabled": true
    }
  ]
}
```

### Production Environment
```json
{
  "name": "Production",
  "values": [
    {
      "key": "base_url",
      "value": "https://api.yourdomain.com",
      "enabled": true
    },
    {
      "key": "token",
      "value": "",
      "enabled": true
    }
  ]
}
```

---

## 🔧 Tips & Tricks

### 1. Chain Requests
Use **Collection Runner** untuk menjalankan workflow lengkap:
1. Login → Extract → Submit Feedback → Train Model

### 2. Mock Servers
Buat mock server dari OpenAPI spec untuk testing frontend tanpa backend.

### 3. Monitors
Setup Postman Monitor untuk health check otomatis.

### 4. Documentation
Generate documentation dari collection: **Collection → View Documentation**

### 5. Code Generation
Generate code snippets: **Code** button (kanan atas request)

---

## 📝 Common Issues

### Issue 1: CORS Error
**Solution:** Pastikan CORS enabled di backend untuk Postman origin.

### Issue 2: Token Expired
**Solution:** Re-run login request atau gunakan auto-refresh script.

### Issue 3: File Upload Failed
**Solution:** 
- Check file size (max 16MB)
- Use `form-data` body type
- Select file dengan "Select Files" button

### Issue 4: 404 Not Found
**Solution:**
- Check base_url environment variable
- Verify endpoint path
- Ensure server is running

---

## 🚀 Advanced Features

### Newman (CLI Runner)
```bash
# Install Newman
npm install -g newman

# Run collection
newman run collection.json -e environment.json

# With reporters
newman run collection.json -e environment.json \
  --reporters cli,html \
  --reporter-html-export report.html
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Run API Tests
  run: |
    newman run postman_collection.json \
      -e postman_environment.json \
      --bail
```

---

## 📚 Resources

- **Postman Learning Center**: https://learning.postman.com
- **API Documentation**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Swagger UI**: http://localhost:8000/api/docs

---

**Last Updated:** 2024-11-08  
**Version:** 1.0.0
