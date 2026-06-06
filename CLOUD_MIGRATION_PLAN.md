# Sticker Tracker: Cloud Migration & Multi-User Deployment Plan

## Executive Summary

Your sticker tracker is currently a single-user local application with JSON file storage. This plan outlines how to transform it into a multi-user, cloud-hosted application using Google Cloud Platform (GCP) for **~$1/month**.

**Recommendation: GCP is ideal** because:
- Cloud Run scales to zero (pay only when in use)
- Firestore handles concurrent writes across multiple users
- Firebase Hosting serves your frontend for free
- Free tier covers typical hobbyist usage (50K reads/day, 1GB storage)

---

## Part 1: Architecture Changes Required

### Current Issues with Multi-User
1. **Single inventory per country** - All users modify the same JSON file
2. **Race conditions** - Concurrent updates corrupt data
3. **No authentication** - No user isolation
4. **Ephemeral file system** - Cloud environments don't persist files between restarts

### Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Users (Multiple)                             │
└──────────┬──────────────────────────────────────────────┬────────┘
           │                                              │
           └─────────────────┬──────────────────────────┬─┘
                             │                          │
                    ┌────────▼─────────┐      ┌────────▼─────────┐
                    │ Firebase Hosting │      │   Cloud Run      │
                    │ (Static Assets)  │      │ (FastAPI Backend)│
                    │ HTML, JS, CSS    │      │                  │
                    └──────────────────┘      └────────┬─────────┘
                                                       │
                                    ┌──────────────────▼──────────────┐
                                    │     Firestore Database          │
                                    │ (Multi-user data + auth state)  │
                                    └─────────────────────────────────┘
```

### Required Code Changes

#### 1. **Abstract Storage Layer** (NEW)
Create a storage provider interface to support both local JSON and Firestore:

```
storage/
├── base.py          # Abstract StorageProvider class
├── local_storage.py # JSON-based (for development)
└── firestore_storage.py # Firestore (for production)
```

#### 2. **Authentication Layer** (NEW)
Add user authentication to isolate per-user data:
- Use Firebase Authentication for SSO/signup
- Validate tokens in FastAPI middleware
- Store user collections as: `users/{user_id}/countries/{country_code}/inventory`

#### 3. **Multi-Tenant Data Model** (MODIFIED)
Current structure:
```
country_inventory/
├── ARG.json
├── USA.json
└── global_inventory.json
```

Cloud structure (Firestore):
```
users/
├── {user_id_1}/
│   ├── countries/
│   │   ├── ARG → {inventory}
│   │   └── USA → {inventory}
│   └── settings → {preferences}
├── {user_id_2}/
│   └── countries/
│       └── ...
```

#### 4. **Dependency Updates**
Add to `requirements.txt`:
```
firebase-admin          # Firestore + Auth integration
python-dotenv          # Environment configuration
google-cloud-firestore # Firestore client
```

---

## Part 2: Implementation Roadmap (8-12 weeks)

### Phase 1: Abstraction Layer (Week 1-2)
**Goal**: Enable switching between local JSON and Firestore without rewriting endpoints

**Tasks**:
- [x] Create `storage/base.py` with `StorageProvider` abstract class
- [x] Implement `storage/local_storage.py` (refactor existing JSON logic)
- [x] Update `api.py` to inject storage provider
- [x] Add environment variable: `STORAGE_PROVIDER=local|firestore`
- [ ] Run all existing tests with both providers

**Deliverable**: Same app works with local JSON OR Firestore via config

> Note: Local JSON access remains available by default, and Firestore is only activated when `STORAGE_PROVIDER=firestore`.

---

### Phase 2: Authentication (Week 2-3)
**Goal**: Add Firebase Auth for multi-user isolation

**Tasks**:
- [x] Set up Firebase project in GCP Console
- [x] Create `auth/firebase_auth.py` middleware
- [ ] Add login/signup routes to `api.py`
- [ ] Modify frontend to use Firebase Auth SDK
- [x] Add `user_id` validation to all inventory endpoints
- [x] Update data paths to include `user_id` namespace in backend storage calls

**Deliverable**: Users can sign up, log in, and their data is isolated

> Backend support is ready for Firebase authentication tokens; frontend auth integration is still pending.

---

### Phase 3: Firestore Migration (Week 3-4)
**Goal**: Replace JSON file storage with Firestore

**Tasks**:
- [x] Create `storage/firestore_storage.py`
- [x] Write migration script: `scripts/migrate_json_to_firestore.py`
- [ ] Test data integrity (counts, stickers match before/after)
- [x] Update `api.py` to use Firestore provider when enabled
- [ ] Add cloud-based backup strategy

**Deliverable**: All data persists in Firestore, no local files needed

> Note: Local storage is still fully available; Firestore is optional and activated with `STORAGE_PROVIDER=firestore`.

---

### Phase 4: Containerization (Week 4-5)
**Goal**: Package FastAPI app for Cloud Run

**Tasks**:
- [x] Create `Dockerfile`
- [x] Create `.dockerignore`
- [ ] Add `entrypoint.sh` script
- [ ] Test container locally: `docker build && docker run`
- [ ] Push to Google Artifact Registry

**Deliverable**: FastAPI app runs in a Docker container

---

### Phase 5: Cloud Deployment (Week 5-6)
**Goal**: Deploy to GCP Cloud Run and Firebase Hosting

**Tasks**:
- [ ] Deploy Cloud Run service from container image
- [ ] Configure Cloud Run environment variables (Firestore credentials, API keys)
- [ ] Set up Firebase Hosting with rewrite rules to Cloud Run backend
- [ ] Configure custom domain + SSL
- [ ] Test end-to-end from cloud

**Deliverable**: App is live at `yourdomain.com`

---

### Phase 6: Polish & Optimization (Week 6-8)
**Goal**: Handle edge cases and optimize for production

**Tasks**:
- [ ] Add error tracking (Cloud Logging)
- [ ] Implement rate limiting (API Gateway or middleware)
- [ ] Add data backup automation (Firestore scheduled exports)
- [ ] Load testing (simulate multiple concurrent users)
- [ ] Security audit (firestore rules, CORS, auth token validation)

**Deliverable**: Production-ready, monitored application

---

## Part 3: Detailed Implementation Steps

### Step 1: Set Up GCP Project

```bash
# Install gcloud CLI (https://cloud.google.com/sdk/docs/install)

# Create new GCP project
gcloud projects create sticker-tracker-prod --name="Sticker Tracker" --set-as-default

# Enable required APIs
gcloud services enable \
  firestore.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  firebase.googleapis.com

# Create Firestore database
gcloud firestore databases create --region=us-central1
```

---

### Step 2: Create Firebase Auth Project

1. Go to the dedicated **[Firebase Console](https://console.firebase.google.com/)** (not the GCP console).
2. Click **"Add project"** and select your existing `sticker-tracker-prod` from the dropdown.
3. In the left sidebar, locate the **Product categories** section:
   - Click **Security > Authentication** → Click **"Get Started"** → Enable **Email/Password** in the "Sign-in method" tab.
   - Click **Databases & Storage > Firestore Database**. You should see the `(default)` database you created via the CLI.
5. Download service account key → save as `firebase-key.json`
6. Add to `.gitignore`

---

### Step 3: Abstract Storage Layer

**File: `stickers/storage/base.py`**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class StorageProvider(ABC):
    @abstractmethod
    def load_country_inventory(self, user_id: str, country_code: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save_country_inventory(self, user_id: str, country_code: str, inventory: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def load_global_inventory(self, user_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save_global_inventory(self, user_id: str, inventory: Dict[str, Any]) -> None:
        pass
```

**File: `stickers/storage/local_storage.py`**
```python
from pathlib import Path
from typing import Dict, Any
from .base import StorageProvider
from inventory import load_json, save_json

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def load_country_inventory(self, user_id: str, country_code: str) -> Dict[str, Any]:
        # For local: ignore user_id, load from shared country_inventory/
        path = self.base_dir / "country_inventory" / f"{country_code.upper()}.json"
        return load_json(path)

    def save_country_inventory(self, user_id: str, country_code: str, inventory: Dict[str, Any]) -> None:
        path = self.base_dir / "country_inventory" / f"{country_code.upper()}.json"
        save_json(path, inventory)
    
    # Similar for global inventory methods...
```

**File: `stickers/storage/firestore_storage.py`**
```python
from typing import Dict, Any
from .base import StorageProvider
import firebase_admin
from firebase_admin import firestore

class FirestoreStorageProvider(StorageProvider):
    def __init__(self):
        self.db = firestore.client()

    def load_country_inventory(self, user_id: str, country_code: str) -> Dict[str, Any]:
        doc = self.db.collection("users").document(user_id) \
            .collection("countries").document(country_code.upper()).get()
        return doc.to_dict() or {}

    def save_country_inventory(self, user_id: str, country_code: str, inventory: Dict[str, Any]) -> None:
        self.db.collection("users").document(user_id) \
            .collection("countries").document(country_code.upper()).set(inventory)
    
    # Similar for global inventory methods...
```

---

### Step 4: Update API Endpoints with User Context

**File: `stickers/api.py` (Modified)**

```python
from fastapi import Depends, HTTPException, Header
from typing import Optional
from storage.base import StorageProvider
from storage.firestore_storage import FirestoreStorageProvider
import os

# Determine storage provider from environment
STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "local")

def get_storage() -> StorageProvider:
    if STORAGE_PROVIDER == "firestore":
        return FirestoreStorageProvider()
    else:
        from storage.local_storage import LocalStorageProvider
        return LocalStorageProvider(BASE_DIR)

async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Extract and validate user ID from Firebase token"""
    if STORAGE_PROVIDER == "local":
        return "local_user"  # Development mode
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # Verify Firebase token here
    # This is pseudocode—use firebase_admin.auth
    user_id = verify_firebase_token(authorization)
    return user_id

@app.get("/inventory/{country_code}")
async def get_inventory(
    country_code: str,
    storage: StorageProvider = Depends(get_storage),
    user_id: str = Depends(get_current_user)
):
    inventory = storage.load_country_inventory(user_id, country_code)
    missing = summarize_missing(inventory)
    return {"missing": missing}

# Similar updates for POST/PATCH endpoints...
```

---

### Step 5: Create Dockerfile

**File: `Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY stickers/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY stickers/ .

# Expose port (Cloud Run expects 8080 by default)
EXPOSE 8080

# Start FastAPI with uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

### Step 6: Firestore Security Rules

**File: `firestore.rules`** (Deploy via Firebase CLI)
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Only users can access their own data
    match /users/{userId}/{document=**} {
      allow read, write: if request.auth.uid == userId;
    }
  }
}
```

---

### Step 7: Deploy to Cloud Run

```bash
# Build and push to Artifact Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/sticker-tracker

# Deploy to Cloud Run
gcloud run deploy sticker-tracker \
  --image gcr.io/PROJECT_ID/sticker-tracker \
  --platform managed \
  --region us-central1 \
  --set-env-vars STORAGE_PROVIDER=firestore \
  --set-env-vars GOOGLE_APPLICATION_CREDENTIALS=/secrets/firebase-key.json
```

---

### Step 8: Deploy Frontend to Firebase Hosting

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Initialize in project root
firebase init hosting

# Configure public directory as stickers/static/

# Deploy
firebase deploy
```

---

## Part 4: Cost Breakdown

| Service | Tier | Monthly Cost | Annual Cost |
|---------|------|--------------|------------|
| **Cloud Run** | 2M requests/month free, then $0.0000025/req | $0 | $0 |
| **Firestore** | 1M reads/month free, 50K/day for reads | $0 | $0 |
| **Firebase Hosting** | 10GB/month free | $0 | $0 |
| **Custom Domain** | .com domain registrar | - | ~$12 |
| **Cloud Storage** (backups) | 5GB free, then $0.020/GB | $0 | $0 |
| **TOTAL** | | ~$1/month | ~$12/year |

*Costs stay at $0 for compute, storage, and hosting if you stay within free tier limits.*

---

## Part 5: Security Checklist

- [ ] Firestore rules enforced (users can only access own data)
- [ ] Firebase Auth tokens validated on every request
- [ ] CORS configured for your domain only
- [ ] Rate limiting enabled (prevent abuse)
- [ ] HTTPS enforced (Firebase Hosting/Cloud Run provide this)
- [ ] No API keys in source code (use environment variables)
- [ ] service account key stored securely (not in git)
- [ ] Automated backups configured (Firestore exports)

---

## Part 6: Testing & Validation

### Local Development
```bash
# Test with local JSON storage
STORAGE_PROVIDER=local python -m uvicorn stickers/api:app --reload

# Test with Firestore emulator
firebase emulators:start
STORAGE_PROVIDER=firestore python -m uvicorn stickers/api:app --reload
```

### Production Validation
- [ ] Create 3+ test user accounts
- [ ] Each user adds stickers independently
- [ ] Verify data is isolated per user
- [ ] Load test with 10+ concurrent users
- [ ] Check Cloud Logging for errors
- [ ] Verify backups are created

---

## Part 7: Timeline & Effort

| Phase | Duration | Complexity | Deliverable |
|-------|----------|-----------|------------|
| Planning & Setup | 1 week | Low | GCP project, Firebase Auth configured |
| Storage Abstraction | 1 week | Medium | Pluggable storage provider |
| Authentication | 1 week | Medium | Multi-user login/signup |
| Firestore Migration | 1 week | Medium | Production database live |
| Containerization | 1 week | Low | Docker image in registry |
| Cloud Deployment | 1 week | Medium | App live on GCP |
| Polish & Testing | 2 weeks | Medium | Production-ready monitoring |
| **Total** | **8 weeks** | **Medium** | **Live, scalable app** |

---

## Part 8: Next Steps

1. **Choose hosting plan**: Confirm GCP + Firestore is acceptable
2. **Set up GCP project**: Create project, enable APIs, download credentials
3. **Start Phase 1**: Build storage abstraction layer
4. **Set up CI/CD**: Automate Docker builds on git push
5. **Security review**: Before going live, audit Firestore rules and auth

---

## FAQ

**Q: Can I keep using local JSON for now?**
A: Yes! The storage abstraction layer lets you develop locally with JSON, test in the cloud with Firestore, and switch via environment variable.

**Q: Will existing data be lost?**
A: No. The migration script reads your JSON files and uploads them to Firestore, preserving all data.

**Q: How do users authenticate?**
A: Firebase Auth provides email/password + Google Sign-In. Users can sign up in seconds.

**Q: What if I exceed free tier?**
A: Unlikely for a personal project. At $0.000025 per request, you'd need 40,000 requests daily to spend $1.

**Q: How do I back up my data?**
A: Firestore exports can be scheduled automatically to Google Cloud Storage (free tier covers it).
