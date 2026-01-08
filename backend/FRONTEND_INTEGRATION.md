# 🔗 RISKOFF Backend - Frontend Integration Guide

> **For:** Frontend Development Team  
> **Backend URL:** `http://localhost:8000`

---

## 🔑 Authentication Header

All protected endpoints require this header:

```
Authorization: Bearer <access_token>
```

> ⚠️ **Important:** Include the word `Bearer ` (with a space) before the token!

---

## 📡 Key Endpoints

### 1. Login

| Property         | Value              |
| ---------------- | ------------------ |
| **URL**          | `POST /auth/login` |
| **Auth**         | ❌ Not required    |
| **Content-Type** | `application/json` |

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**

```json
{
  "message": "Login successful",
  "user_id": "uuid-here",
  "email": "user@example.com",
  "full_name": "John Doe",
  "access_token": "eyJhbGc...",
  "refresh_token": "refresh-token-here",
  "token_type": "bearer"
}
```

---

### 2. Signup

| Property         | Value               |
| ---------------- | ------------------- |
| **URL**          | `POST /auth/signup` |
| **Auth**         | ❌ Not required     |
| **Content-Type** | `application/json`  |

**Request Body:**

```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "1234567890",
  "password": "password123"
}
```

---

### 3. Apply for Loan

| Property         | Value               |
| ---------------- | ------------------- |
| **URL**          | `POST /loans/apply` |
| **Auth**         | ✅ Required         |
| **Content-Type** | `application/json`  |

**Request Body:**

```json
{
  "amount": 100000,
  "tenure_months": 24,
  "monthly_income": 75000,
  "monthly_expenses": 30000,
  "purpose": "Business expansion"
}
```

**Response:**

```json
{
  "id": 1,
  "status": "APPROVED",
  "risk_score": 25.0,
  "max_approved_amount": 100000,
  "emi": 4707.35,
  "ai_explanation": "Congratulations! Your loan has been approved..."
}
```

---

### 4. Upload Receipt (Image)

| Property         | Value                  |
| ---------------- | ---------------------- |
| **URL**          | `POST /upload/receipt` |
| **Auth**         | ⚪ Optional            |
| **Content-Type** | `multipart/form-data`  |

> ⚠️ **Use FormData, NOT JSON!**

**JavaScript Example:**

```javascript
const formData = new FormData();
formData.append("file", fileInput.files[0]);

fetch("http://localhost:8000/upload/receipt", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`, // Optional
  },
  body: formData,
});
```

---

### 5. Upload Bank Statement (CSV)

| Property         | Value                         |
| ---------------- | ----------------------------- |
| **URL**          | `POST /upload/bank-statement` |
| **Auth**         | ✅ Required                   |
| **Content-Type** | `multipart/form-data`         |

> ⚠️ **Use FormData, NOT JSON!**

```javascript
const formData = new FormData();
formData.append("file", csvFile);

fetch("http://localhost:8000/upload/bank-statement", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
  },
  body: formData,
});
```

---

### 6. AI Chat Agent

| Property         | Value              |
| ---------------- | ------------------ |
| **URL**          | `POST /agent/chat` |
| **Auth**         | ✅ Required        |
| **Content-Type** | `application/json` |

**Request Body:**

```json
{
  "query": "What is my loan status?"
}
```

**Response:**

```json
{
  "response": "Hello John! Your loan of ₹100,000 is approved...",
  "suggested_action": "Complete loan documentation"
}
```

---

### 7. Get My Loans

| Property | Value                 |
| -------- | --------------------- |
| **URL**  | `GET /loans/my-loans` |
| **Auth** | ✅ Required           |

---

### 8. Get Current User

| Property | Value          |
| -------- | -------------- |
| **URL**  | `GET /auth/me` |
| **Auth** | ✅ Required    |

---

## ⚠️ Common Pitfalls

1. **NO trailing slashes!**

   - ✅ Correct: `/auth/login`
   - ❌ Wrong: `/auth/login/`

2. **Bearer prefix required!**

   - ✅ Correct: `Authorization: Bearer eyJhbG...`
   - ❌ Wrong: `Authorization: eyJhbG...`

3. **File uploads use FormData, not JSON!**

4. **Error Response Format:**
   ```json
   {
     "status": "error",
     "message": "Invalid email or password",
     "code": 401
   }
   ```

---

## 🧪 Quick Test (cURL)

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"password123"}'

# Protected endpoint
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 📚 Full API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
