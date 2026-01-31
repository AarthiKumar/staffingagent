# Getting Started with Auth0 Authentication

This guide walks you through setting up and testing the complete Auth0 authentication system for the Staffing Agent application.

## Quick Start Checklist

Follow these steps in order:

### ✅ Phase 1: Auth0 Account Setup (15-20 minutes)

1. [ ] Create Auth0 account at https://auth0.com/signup
2. [ ] Create Auth0 Application (Single Page Application type)
3. [ ] Create Auth0 API with identifier `https://api.staffingagent.com`
4. [ ] Create 3 roles: `superuser`, `project_manager`, `staff`
5. [ ] Create Auth0 Action to add roles to tokens
6. [ ] Create 3 test users with different roles

**📖 Detailed Guide**: See `AUTH0_SETUP.md` and `AUTH0_TEST_USERS_SETUP.md`

### ✅ Phase 2: Backend Configuration (5-10 minutes)

1. [ ] Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. [ ] Create `.env` file with Auth0 credentials:
   ```bash
   cd backend
   cp .env.example .env
   ```

3. [ ] Edit `backend/.env` with your Auth0 values:
   ```bash
   AUTH0_ENABLED=true
   AUTH0_DOMAIN=your-tenant.us.auth0.com
   AUTH0_CLIENT_ID=your_client_id
   AUTH0_CLIENT_SECRET=your_client_secret
   AUTH0_AUDIENCE=https://api.staffingagent.com
   AUTH0_CALLBACK_URL=http://localhost:5173/callback
   ```

4. [ ] Start the backend:
   ```bash
   uvicorn app.main:app --reload
   ```

**📖 Detailed Guide**: See `AUTH0_SETUP.md` section "Backend Configuration"

### ✅ Phase 3: Frontend Configuration (5-10 minutes)

1. [ ] Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. [ ] Create `.env.local` file:
   ```bash
   cd frontend
   cp .env.example .env.local
   ```

3. [ ] Edit `frontend/.env.local` with your Auth0 values:
   ```bash
   VITE_AUTH0_ENABLED=true
   VITE_AUTH0_DOMAIN=your-tenant.us.auth0.com
   VITE_AUTH0_CLIENT_ID=your_client_id
   VITE_AUTH0_AUDIENCE=https://api.staffingagent.com
   VITE_AUTH0_REDIRECT_URI=http://localhost:5173/callback
   ```

4. [ ] Start the frontend:
   ```bash
   npm run dev
   ```

**📖 Detailed Guide**: See `FRONTEND_AUTH0_SETUP.md`

### ✅ Phase 4: Testing (15-20 minutes)

1. [ ] Open `http://localhost:5173` in your browser
2. [ ] Click "Log In" button
3. [ ] Log in with superuser account (`superuser@test.com`)
4. [ ] Verify you can:
   - Search for candidates
   - View all candidates
   - Upload CVs
   - Manage availability
5. [ ] Log out and log in as staff (`staff@test.com`)
6. [ ] Verify you CANNOT:
   - Search for candidates (should show 403 error)
   - View all candidates list
7. [ ] Verify you CAN:
   - Upload your own CV
   - View your own profile

**📖 Detailed Guide**: See testing sections in both setup guides

---

## Complete Documentation Index

### Auth0 Setup Guides

| Document | Purpose | When to Use |
|----------|---------|-------------|
| `AUTH0_SETUP.md` | Complete Auth0 setup from scratch | First-time setup |
| `AUTH0_API_CONFIGURATION.md` | Auth0 API and user config | Configuring Auth0 properly |
| `AUTH0_TEST_USERS_SETUP.md` | Creating test users with roles | Setting up test accounts |
| `FRONTEND_AUTH0_SETUP.md` | Frontend integration guide | Frontend development |

### Example Code

| File | Purpose |
|------|---------|
| `backend/examples/auth_examples.py` | Backend API usage examples |
| `backend/app/tests/test_auth0.py` | Backend unit tests |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│ User Browser                                                      │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ React Frontend (http://localhost:5173)                     │ │
│  │                                                             │ │
│  │  1. User clicks "Log In"                                   │ │
│  │  2. Redirected to Auth0 login page                         │ │
│  │  3. User enters credentials                                │ │
│  │  4. Auth0 validates and runs Action (adds roles)           │ │
│  │  5. Redirected to /callback with code                      │ │
│  │  6. Auth0 SDK exchanges code for tokens                    │ │
│  │  7. Tokens cached in localStorage                          │ │
│  │  8. User menu shows name and role badge                    │ │
│  │                                                             │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │ Every API call includes:                            │  │ │
│  │  │   Authorization: Bearer <access_token>              │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              │ HTTP with Bearer Token
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ FastAPI Backend (http://localhost:8000)                          │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Auth0 Middleware                                           │ │
│  │                                                             │ │
│  │  1. Extract Bearer token from Authorization header        │ │
│  │  2. Validate JWT signature with Auth0 public key          │ │
│  │  3. Check token audience matches AUTH0_AUDIENCE           │ │
│  │  4. Extract user email and roles from token               │ │
│  │  5. Create User object with role-checking methods         │ │
│  │  6. Pass User to endpoint handler                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Protected Endpoints                                        │ │
│  │                                                             │ │
│  │  @router.post("/search/")                                  │ │
│  │  def search(user: User = Depends(require_project_manager))│ │
│  │      if not user.is_project_manager:                       │ │
│  │          raise HTTPException(403, "Access denied")         │ │
│  │      # ... perform search                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Role-Based Permissions Matrix

| Action | Endpoint | Superuser | PM | Staff |
|--------|----------|-----------|----|----|
| **Search** |
| Search candidates | `POST /search/` | ✅ | ✅ | ❌ |
| View search results | `GET /search/candidates/{id}` | ✅ | ✅ | ❌ |
| **Candidates** |
| List all candidates | `GET /candidates/` | ✅ | ✅ | ❌ |
| View any candidate | `GET /candidates/{id}` | ✅ | ✅ | ❌ |
| View own profile | `GET /candidates/{id}` | ✅ | ✅ | ✅* |
| Update any candidate | `PUT /candidates/{id}` | ✅ | ✅ | ❌ |
| Update own profile | `PUT /candidates/{id}` | ✅ | ✅ | ✅* |
| **Availability** |
| List availability | `GET /availability/` | ✅ | ✅ | ❌ |
| Update availability | `PUT /availability/{id}` | ✅ | ✅ | ❌ |
| Upload availability CSV | `POST /availability/upload` | ✅ | ✅ | ❌ |
| **CV Management** |
| Upload CV | `POST /ingest/` | ✅ | ✅ | ✅ |
| Approve CV merge | `POST /ingest/approve-merge` | ✅ | ✅ | ❌ |
| **Sections** |
| Update any section | `PUT /sections/{id}` | ✅ | ✅ | ❌ |
| Update own sections | `PUT /sections/{id}` | ✅ | ✅ | ✅* |
| Delete section | `DELETE /sections/{id}` | ✅ | ✅ | ❌ |

\* Staff can only access their own resources (matched by email)

---

## Common Workflows

### Workflow 1: Superuser manages system

```bash
# 1. Log in as superuser@test.com
# 2. Search for candidates
POST /api/v1/search/
{
  "agent_id": "default",
  "filters": {"required_skills": ["Python"]},
  "top_k": 20
}

# 3. View candidate details
GET /api/v1/candidates/{id}

# 4. Update candidate info
PUT /api/v1/candidates/{id}
{
  "name": "Updated Name",
  "location": "New York, NY"
}

# 5. Manage availability
PUT /api/v1/availability/{id}
{
  "available_from": "2024-03-01",
  "capacity_pct": 50
}
```

### Workflow 2: Project Manager searches for staff

```bash
# 1. Log in as pm@test.com
# 2. Search for candidates with specific skills
POST /api/v1/search/
{
  "agent_id": "default",
  "filters": {
    "required_skills": ["Kubernetes", "Python"],
    "min_years": {"Kubernetes": 2},
    "availability_from": "2024-02-01"
  },
  "text": "DevOps engineer with cloud experience",
  "top_k": 30
}

# 3. View candidate CV
GET /api/v1/candidates/{id}

# 4. Update availability
PUT /api/v1/availability/{id}
{
  "available_from": "2024-03-15",
  "capacity_pct": 100,
  "notes": "Available for new project"
}
```

### Workflow 3: Staff member updates own CV

```bash
# 1. Log in as staff@test.com
# 2. Upload new CV
POST /api/v1/ingest/
{
  "agent_id": "default",
  "document_type": "resume",
  "filename": "john_doe_cv.pdf",
  "content_base64": "...",
  "manual_email": "staff@test.com"  # Must match logged-in email
}

# 3. View own profile
GET /api/v1/candidates/{id}  # Only works if candidate.email == staff@test.com

# 4. Update own skills section
PUT /api/v1/sections/{section_id}
{
  "text": "Python, Kubernetes, Docker, AWS, Terraform, Jenkins, GitLab CI"
}
```

---

## Troubleshooting Guide

### Backend Issues

#### Issue: "Invalid token" error

**Check:**
```bash
# 1. Verify backend .env has correct values
cat backend/.env | grep AUTH0

# 2. Check logs for specific error
tail -f backend/logs/app.log

# 3. Test token manually
curl -X POST http://localhost:8000/api/v1/search/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "default", "filters": {}, "top_k": 10}'
```

#### Issue: "Roles not in token"

**Fix:**
1. Go to Auth0 Dashboard → Actions → Flows → Login
2. Verify "Add Roles to Token" action is deployed (not draft)
3. Verify action is in the flow (drag and drop)
4. Click "Apply" to save the flow
5. Log out and log back in to get new token

### Frontend Issues

#### Issue: Infinite redirect loop

**Check:**
```bash
# 1. Verify callback URL matches
cat frontend/.env.local | grep REDIRECT_URI

# 2. Check browser console for errors
# 3. Check Auth0 Application settings have correct callback URL
```

#### Issue: "Auth0 not configured" warning

**Fix:**
```bash
# 1. Verify .env.local exists
ls -la frontend/.env.local

# 2. Check values are set
cat frontend/.env.local

# 3. Restart dev server
cd frontend
npm run dev
```

### Auth0 Dashboard Issues

#### Issue: Can't find roles

**Location**: Auth0 Dashboard → User Management → Roles

#### Issue: Can't find Actions

**Location**: Auth0 Dashboard → Actions → Flows → Login

#### Issue: Can't find API

**Location**: Auth0 Dashboard → Applications → APIs

---

## Security Checklist

Before going to production:

### Auth0 Configuration
- [ ] Change Auth0 passwords to strong, unique passwords
- [ ] Enable Multi-Factor Authentication (MFA) for admin accounts
- [ ] Set token expiration to reasonable values (24 hours recommended)
- [ ] Add production URLs to Auth0 Application settings
- [ ] Remove development/localhost URLs from production tenant

### Backend
- [ ] Set `AUTH0_ENABLED=true` in production
- [ ] Use environment variables, not `.env` file in production
- [ ] Enable HTTPS only (no HTTP)
- [ ] Set `CORS_ORIGINS` to specific domains, not `*`
- [ ] Rotate `AUTH0_CLIENT_SECRET` regularly

### Frontend
- [ ] Use environment variables in hosting platform
- [ ] Never commit `.env.local` to git
- [ ] Enable HTTPS only
- [ ] Set Content Security Policy (CSP) headers
- [ ] Use `cacheLocation="localstorage"` for token caching

### Monitoring
- [ ] Enable Auth0 logs and monitoring
- [ ] Set up alerts for failed login attempts
- [ ] Monitor API for 401/403 errors
- [ ] Regular security audits

---

## Next Steps

Now that Auth0 is fully integrated:

1. **✅ Test thoroughly** with all three user roles
2. **📝 Train users** on how to log in and use the system
3. **🚀 Deploy to staging** for UAT (User Acceptance Testing)
4. **🔍 Monitor** Auth0 dashboard for issues
5. **🎯 Deploy to production** when ready

## Support Resources

- **Auth0 Documentation**: https://auth0.com/docs
- **Auth0 Community**: https://community.auth0.com/
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **React Auth0 SDK**: https://auth0.com/docs/quickstart/spa/react

## Project Documentation

- `AUTH0_SETUP.md` - Complete Auth0 setup guide
- `AUTH0_TEST_USERS_SETUP.md` - Creating test users
- `AUTH0_API_CONFIGURATION.md` - API configuration guide
- `FRONTEND_AUTH0_SETUP.md` - Frontend integration
- `backend/examples/auth_examples.py` - Code examples
- `backend/app/tests/test_auth0.py` - Unit tests

---

**Happy Authenticating! 🎉**
