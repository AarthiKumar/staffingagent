# Auth0 Setup Guide

Complete guide for setting up Auth0 authentication with role-based access control for the Staffing Agent application.

## Table of Contents

1. [Create Auth0 Account](#1-create-auth0-account)
2. [Configure Auth0 Application](#2-configure-auth0-application)
3. [Set Up User Roles](#3-set-up-user-roles)
4. [Configure Backend](#4-configure-backend)
5. [Test Authentication](#5-test-authentication)
6. [Manage Users](#6-manage-users)

---

## 1. Create Auth0 Account

1. Go to [auth0.com](https://auth0.com)
2. Click "Sign Up" and create a free account
3. Create a new tenant (e.g., `staffingagent-dev`)

---

## 2. Configure Auth0 Application

### Create Application

1. In Auth0 Dashboard, go to **Applications** → **Applications**
2. Click **Create Application**
3. Name: `Staffing Agent`
4. Type: **Single Page Web Application**
5. Click **Create**

### Configure Application Settings

1. Go to your application's **Settings** tab
2. Note down these values (you'll need them later):
   - **Domain**: `your-tenant.auth0.com`
   - **Client ID**: `abc123...`
   - **Client Secret**: `xyz789...` (from "Advanced Settings" → "Credentials")

3. Set **Allowed Callback URLs**:
   ```
   http://localhost:5173/callback,
   http://localhost:8000/api/v1/auth/auth0/callback
   ```

4. Set **Allowed Logout URLs**:
   ```
   http://localhost:5173,
   http://localhost:5173/login
   ```

5. Set **Allowed Web Origins**:
   ```
   http://localhost:5173,
   http://localhost:8000
   ```

6. Click **Save Changes**

### Create API

1. Go to **Applications** → **APIs**
2. Click **Create API**
3. Name: `Staffing Agent API`
4. Identifier: `https://api.staffingagent.com` (this is your audience)
5. Signing Algorithm: **RS256**
6. Click **Create**

---

## 3. Set Up User Roles

### Create Roles

1. Go to **User Management** → **Roles**
2. Click **Create Role**

Create these three roles:

**Role 1: Super User**
- Name: `superuser`
- Description: `Full system access, can manage users`

**Role 2: Project Manager**
- Name: `project_manager`
- Description: `Can search for staff and update availability`

**Role 3: Staff**
- Name: `staff`
- Description: `Can upload and update their own CVs`

### Add Roles to Tokens

We need to add roles to the JWT token via an Auth0 Action.

1. Go to **Actions** → **Library**
2. Click **Build Custom**
3. Name: `Add Roles to Token`
4. Trigger: **Login / Post Login**
5. Add this code:

```javascript
exports.onExecutePostLogin = async (event, api) => {
  // Get user roles
  const namespace = 'https://staffingagent.com';

  if (event.authorization) {
    // Add roles to access token
    api.accessToken.setCustomClaim(`${namespace}/roles`, event.authorization.roles);

    // Add roles to ID token
    api.idToken.setCustomClaim(`${namespace}/roles`, event.authorization.roles);
  }
};
```

6. Click **Deploy**
7. Go to **Actions** → **Flows** → **Login**
8. Drag your "Add Roles to Token" action into the flow
9. Click **Apply**

---

## 4. Configure Backend

### Environment Variables

Create or update `backend/.env`:

```env
# Database
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/staffing

# Auth0 Configuration
AUTH0_ENABLED=true
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your_client_id_here
AUTH0_CLIENT_SECRET=your_client_secret_here
AUTH0_AUDIENCE=https://api.staffingagent.com
AUTH0_CALLBACK_URL=http://localhost:5173/callback

# Other settings...
EMBEDDINGS_MODEL=BAAI/bge-small-en
EMBEDDINGS_PROVIDER=local
LLM_PROVIDER=disabled
```

### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs PyJWT and other auth dependencies.

### Restart Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 5. Test Authentication

### Test Auth0 Login Flow

1. **Get Login URL**:
   ```bash
   curl http://localhost:8000/api/v1/auth/auth0/login
   ```

   Response:
   ```json
   {
     "auth_url": "https://your-tenant.auth0.com/authorize?..."
   }
   ```

2. **Open the auth_url in your browser**
   - You'll be redirected to Auth0 login page
   - Log in with a test user
   - After login, you'll be redirected to the callback URL with a code

3. **Exchange Code for Token** (backend handles this automatically)

### Test Protected Endpoint

1. **Get Access Token** from Auth0

2. **Call Protected Endpoint**:
   ```bash
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        http://localhost:8000/api/v1/candidates/
   ```

---

## 6. Manage Users

### Create Users

1. Go to **User Management** → **Users**
2. Click **Create User**
3. Enter email and password
4. Click **Create**

### Assign Roles to Users

1. Click on a user
2. Go to **Roles** tab
3. Click **Assign Roles**
4. Select role(s) (superuser, project_manager, or staff)
5. Click **Assign**

### Example User Setup

**Super User**
- Email: `admin@example.com`
- Role: `superuser`
- Can: Manage all users, full system access

**Project Manager**
- Email: `pm@example.com`
- Role: `project_manager`
- Can: Search for staff, update availability

**Staff Member**
- Email: `john.doe@example.com`
- Role: `staff`
- Can: Upload and update their own CV

---

## Role Permissions

### Superuser
- ✅ Create/delete users
- ✅ Search for candidates
- ✅ Upload any CV
- ✅ Update any availability
- ✅ Edit any sections
- ✅ Full system access

### Project Manager
- ❌ Cannot manage users
- ✅ Search for candidates
- ✅ Upload CVs
- ✅ Update availability
- ✅ View all candidates
- ❌ Cannot delete users

### Staff
- ❌ Cannot manage users
- ❌ Cannot search (unless viewing their own profile)
- ✅ Upload their own CV
- ✅ Update their own CV sections
- ✅ View their own profile
- ❌ Cannot see other staff profiles

---

## Protecting Endpoints

### Backend Example

```python
from fastapi import APIRouter, Depends
from app.core.auth0 import get_current_user, User, UserRole, require_superuser

router = APIRouter()

# Public endpoint (no auth required)
@router.get("/public")
async def public_endpoint():
    return {"message": "Public data"}

# Requires any authenticated user
@router.get("/profile")
async def get_profile(user: User = Depends(get_current_user)):
    return {"email": user.email, "roles": user.roles}

# Requires superuser role
@router.get("/admin")
async def admin_only(user: User = Depends(require_superuser)):
    return {"message": "Admin data"}

# Requires project_manager or superuser
@router.get("/search")
async def search_staff(user: User = Depends(get_current_user)):
    # Check role manually
    if not (user.is_project_manager or user.is_superuser):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return {"results": [...]}
```

---

## Troubleshooting

### "Authentication is not enabled"

Make sure `AUTH0_ENABLED=true` in your `.env` file.

### "Invalid token"

1. Check that `AUTH0_DOMAIN` matches your Auth0 tenant
2. Verify `AUTH0_AUDIENCE` matches your API identifier
3. Ensure the token hasn't expired (default: 1 hour)

### "Insufficient permissions"

1. Check that the user has the required role assigned in Auth0
2. Verify the "Add Roles to Token" Action is deployed and added to the Login flow
3. Inspect the JWT token at [jwt.io](https://jwt.io) to confirm roles are present

### Roles not appearing in token

1. Make sure the Action is deployed
2. Verify the Action is added to the Login flow
3. Log out and log back in to get a fresh token
4. Check that the namespace in the Action matches: `https://staffingagent.com/roles`

---

## Security Best Practices

1. **Use HTTPS in production** - Update callback URLs to use `https://`
2. **Rotate secrets regularly** - Generate new client secrets periodically
3. **Enable MFA** - Require multi-factor authentication for superusers
4. **Monitor login attempts** - Use Auth0 anomaly detection
5. **Limit token lifetime** - Keep access tokens short-lived (default: 1 hour)
6. **Use refresh tokens** - For long-lived sessions
7. **Validate roles server-side** - Never trust client-side role checks alone

---

## Next Steps

1. ✅ Configure Auth0 application and API
2. ✅ Set up user roles
3. ✅ Configure backend environment variables
4. ✅ Create test users with different roles
5. ⬜ Implement frontend Auth0 SDK
6. ⬜ Add login/logout UI
7. ⬜ Test all role permissions
8. ⬜ Deploy to production with HTTPS

---

## Support

- Auth0 Documentation: [auth0.com/docs](https://auth0.com/docs)
- Community Forum: [community.auth0.com](https://community.auth0.com)
- Contact Support: For paid plans

---

## Example .env File

```env
# Database
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/staffing

# Auth0
AUTH0_ENABLED=true
AUTH0_DOMAIN=staffingagent-dev.us.auth0.com
AUTH0_CLIENT_ID=abc123youridhere
AUTH0_CLIENT_SECRET=xyz789yoursecrethere
AUTH0_AUDIENCE=https://api.staffingagent.com
AUTH0_CALLBACK_URL=http://localhost:5173/callback

# MinIO Storage
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=originals
STORAGE_LOCAL_PATH=./data/originals

# Embeddings
EMBEDDINGS_MODEL=BAAI/bge-small-en
EMBEDDINGS_PROVIDER=local

# LLM (optional)
LLM_PROVIDER=disabled
ENABLE_LLM_RERANK=false
ENABLE_NL_ASSIST=false

# Metrics
PROMETHEUS_PORT=9001
```
