# Testing Guide - Authentication System

## 🧪 Test Using Swagger UI (Easiest)

FastAPI provides an interactive API documentation at:

```
http://localhost:8000/docs
```

### Step-by-Step in Swagger:

1. **Go to** `http://localhost:8000/docs`

2. **Register User:**
   - Find `POST /register`
   - Click "Try it out"
   - Fill in:
     ```json
     {
       "email": "alice@example.com",
       "password": "password123",
       "full_name": "Alice Smith"
     }
     ```
   - Click "Execute"

3. **Login:**
   - Find `POST /login`
   - Click "Try it out"
   - Fill in same credentials
   - Click "Execute"
   - **COPY THE TOKEN** from response

4. **Authorize:**
   - Click the 🔒 **"Authorize"** button at top right
   - Paste your token
   - Click "Authorize"
   - Now all protected endpoints will work!

5. **Upload Document:**
   - Find `POST /upload-document/`
   - Click "Try it out"
   - Fill statement_id and upload a PDF
   - Click "Execute"

---

## 🔧 Test Using curl Commands

### 1️⃣ Register Users

```bash
# Register Alice
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "password123",
    "full_name": "Alice Smith"
  }'

# Register Bob
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@example.com",
    "password": "password456",
    "full_name": "Bob Jones"
  }'
```

### 2️⃣ Login and Get Tokens

```bash
# Alice Login
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "password123"
  }'

# Save Alice's token in variable
ALICE_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Bob Login
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@example.com",
    "password": "password456"
  }'

# Save Bob's token
BOB_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3️⃣ Upload Documents

```bash
# Alice uploads a document
curl -X POST "http://localhost:8000/upload-document/" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -F "statement_id=ALICE_STMT_001" \
  -F "pdf_file=@/path/to/alice_statement.pdf"

# Bob uploads a document
curl -X POST "http://localhost:8000/upload-document/" \
  -H "Authorization: Bearer $BOB_TOKEN" \
  -F "statement_id=BOB_STMT_001" \
  -F "pdf_file=@/path/to/bob_statement.pdf"
```

### 4️⃣ Test Security (Important!)

```bash
# Alice can see her documents
curl -X GET "http://localhost:8000/documents/" \
  -H "Authorization: Bearer $ALICE_TOKEN"

# Bob can see his documents
curl -X GET "http://localhost:8000/documents/" \
  -H "Authorization: Bearer $BOB_TOKEN"

# ❌ Alice CANNOT access Bob's documents
# This should return 404 or empty
curl -X GET "http://localhost:8000/documents/2" \
  -H "Authorization: Bearer $ALICE_TOKEN"

# ❌ Without token - should fail with 401
curl -X GET "http://localhost:8000/documents/"
```

### 5️⃣ Test Transactions

```bash
# Get transactions for Alice's statement
curl -X GET "http://localhost:8000/statements/ALICE_STMT_001/transactions" \
  -H "Authorization: Bearer $ALICE_TOKEN"

# Get transaction summary
curl -X GET "http://localhost:8000/statements/ALICE_STMT_001/transactions/summary" \
  -H "Authorization: Bearer $ALICE_TOKEN"

# ❌ Bob CANNOT access Alice's transactions
curl -X GET "http://localhost:8000/statements/ALICE_STMT_001/transactions" \
  -H "Authorization: Bearer $BOB_TOKEN"
# Should return 404 - "Statement not found or access denied"
```

---

## 🐍 Test Using Python

Create a test script `test_auth.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Register
def register_user(email, password, full_name):
    response = requests.post(
        f"{BASE_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name
        }
    )
    print(f"Register {email}:", response.status_code)
    return response.json()

# 2. Login
def login_user(email, password):
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": email,
            "password": password
        }
    )
    print(f"Login {email}:", response.status_code)
    data = response.json()
    return data.get("access_token")

# 3. Upload Document
def upload_document(token, statement_id, file_path):
    headers = {"Authorization": f"Bearer {token}"}
    files = {"pdf_file