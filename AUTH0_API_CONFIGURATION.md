# Auth0 API Configuration Guide

This guide explains how to properly configure your Auth0 API and what NOT to do when setting up users.

## Common Confusion ❌

**WRONG**: Trying to assign API permissions to individual users
**RIGHT**: Assign roles to users; the API is configured once globally

## Part 1: One-Time API Setup (Do This Once)

### Step 1: Create an API in Auth0

1. Go to your [Auth0 Dashboard](https://manage.auth0.com/)
2. Click **Applications** → **APIs** in the left sidebar
3. Click **+ Create API**
4. Fill in the form:
   - **Name**: `Staffing Agent API`
   - **Identifier**: `https://api.staffingagent.com`
     - ⚠️ **Important**: This MUST match your `AUTH0_AUDIENCE` in `.env`
     - This doesn't need to be a real URL - it's just an identifier
   - **Signing Algorithm**: `RS256` (default)
5. Click **Create**

### Step 2: Configure API Settings

After creating the API:

1. Click on the **Settings** tab
2. Scroll down to **Access Settings**
3. Make sure these are set:
   - **Allow Skipping User Consent**: ✅ Enabled (for testing)
   - **Allow Offline Access**: ❌ Disabled (unless you need refresh tokens)
4. Click **Save**

### Step 3: Enable RBAC (Role-Based Access Control)

1. Still in the API settings, scroll to **RBAC Settings**
2. Enable these options:
   - **Enable RBAC**: ✅ ON
   - **Add Permissions in the Access Token**: ❌ OFF
     - We're using roles, not permissions, so we don't need this
3. Click **Save**

**Why we don't use permissions**:
- Permissions are fine-grained (e.g., "read:candidates", "write:candidates")
- Roles are broader (e.g., "superuser", "project_manager", "staff")
- For this application, roles are simpler and sufficient

## Part 2: Application Configuration

### Step 4: Create or Configure Your Application

1. Go to **Applications** → **Applications**
2. If you haven't created one yet, click **+ Create Application**:
   - **Name**: `Staffing Agent Web App`
   - **Type**: `Single Page Application` (for React frontend)
   - Click **Create**

3. Go to the **Settings** tab and configure:

   **Application URIs**:
   - **Allowed Callback URLs**:
     ```
     http://localhost:5173/callback,
     http://localhost:3000/callback,
     https://yourdomain.com/callback
     ```
   - **Allowed Logout URLs**:
     ```
     http://localhost:5173,
     http://localhost:3000,
     https://yourdomain.com
     ```
   - **Allowed Web Origins**:
     ```
     http://localhost:5173,
     http://localhost:3000,
     https://yourdomain.com
     ```

4. Scroll down to **Advanced Settings** → **Grant Types**
   - Make sure these are checked:
     - ✅ Authorization Code
     - ✅ Refresh Token (if you want refresh tokens)
   - Uncheck:
     - ❌ Implicit
     - ❌ Client Credentials (unless you need M2M)

5. Click **Save Changes**

### Step 5: Connect API to Application

1. Still in your Application settings, scroll to **APIs** tab
2. You should see your `Staffing Agent API` listed
3. **You don't need to do anything here** - the API is automatically available
4. The connection happens via the `audience` parameter when logging in

## Part 3: User Configuration (Per User)

### What Users Need

Each user needs:
1. ✅ An email and password (created in User Management → Users)
2. ✅ **One or more roles assigned** (superuser, project_manager, or staff)
3. ❌ **NO API permissions** - this is automatic via roles!

### Step 6: Assign Roles to Users (NOT API Permissions!)

For each user you created:

1. Go to **User Management** → **Users**
2. Click on a user (e.g., `superuser@test.com`)
3. Click the **Roles** tab (NOT the Permissions tab!)
4. Click **Assign Roles**
5. Select the appropriate role:
   - For `superuser@test.com`: Select `superuser` role
   - For `pm@test.com`: Select `project_manager` role
   - For `staff@test.com`: Select `staff` role
6. Click **Assign**

### What You Should See

After assigning roles, each user's profile should show:

**superuser@test.com**
- **Roles** tab: `superuser` ✅
- **Permissions** tab: (empty - this is fine!) ✅

**pm@test.com**
- **Roles** tab: `project_manager` ✅
- **Permissions** tab: (empty - this is fine!) ✅

**staff@test.com**
- **Roles** tab: `staff` ✅
- **Permissions** tab: (empty - this is fine!) ✅

## Part 4: Environment Variables

Update your `backend/.env` file with the correct values:

```bash
# Auth0 Configuration
AUTH0_ENABLED=true
AUTH0_DOMAIN=your-tenant.us.auth0.com          # Your Auth0 domain
AUTH0_CLIENT_ID=abc123...                       # From Application settings
AUTH0_CLIENT_SECRET=xyz789...                   # From Application settings (keep secret!)
AUTH0_AUDIENCE=https://api.staffingagent.com    # MUST match the API Identifier you created
AUTH0_CALLBACK_URL=http://localhost:5173/callback

# Other settings...
DATABASE_URL=postgresql://user:password@localhost:5432/staffing
EMBEDDINGS_PROVIDER=sentence_transformers
```

## Part 5: Verify Configuration

### Check 1: API is Created

1. Go to **Applications** → **APIs**
2. You should see `Staffing Agent API`
3. Click on it and verify:
   - Identifier: `https://api.staffingagent.com`
   - RBAC: Enabled

### Check 2: Application is Created

1. Go to **Applications** → **Applications**
2. You should see `Staffing Agent Web App`
3. Click on it and verify:
   - Type: Single Page Application
   - Callback URLs are set
   - Client ID and Secret match your `.env` file

### Check 3: Roles are Created

1. Go to **User Management** → **Roles**
2. You should see three roles:
   - `superuser`
   - `project_manager`
   - `staff`

### Check 4: Users Have Roles

1. Go to **User Management** → **Users**
2. For each test user, click them and check the **Roles** tab
3. Each should have exactly one role assigned

### Check 5: Auth0 Action is Deployed

1. Go to **Actions** → **Flows** → **Login**
2. You should see "Add Roles to Token" in the flow
3. It should be between "Start" and "Complete"
4. The action should say "Deployed" (not "Draft")

## What Each Component Does

Here's how it all fits together:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User logs in via Auth0                                   │
│    → Auth0 checks username/password                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Auth0 runs Login Flow                                    │
│    → Executes "Add Roles to Token" action                   │
│    → Gets user's roles from User Management                 │
│    → Adds roles to JWT token custom claim                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Auth0 generates JWT token                                │
│    {                                                         │
│      "sub": "auth0|123...",                                  │
│      "email": "staff@test.com",                              │
│      "https://staffingagent.com/roles": ["staff"],           │
│      "aud": "https://api.staffingagent.com",  ← API audience│
│      "iss": "https://your-tenant.auth0.com/"                 │
│    }                                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Token sent to your backend API                           │
│    → Backend validates JWT signature                        │
│    → Backend checks audience matches AUTH0_AUDIENCE         │
│    → Backend extracts roles from custom claim               │
│    → Backend enforces permissions based on roles            │
└─────────────────────────────────────────────────────────────┘
```

## Common Issues and Solutions

### Issue: "audience" error when logging in

**Symptom**: Error says "audience is not allowed"

**Solution**:
1. Check that API audience in Auth0 matches `AUTH0_AUDIENCE` in `.env`
2. Make sure you're passing the `audience` parameter when logging in
3. Verify the API is enabled in Auth0

### Issue: Roles not in JWT token

**Symptom**: Token doesn't have `https://staffingagent.com/roles` claim

**Solution**:
1. Verify Auth0 Action "Add Roles to Token" is **Deployed** (not Draft)
2. Check that the action is **added to Login flow** (drag and drop)
3. Make sure you clicked **Apply** on the Login flow
4. Verify user has role assigned in Auth0 dashboard

### Issue: "Invalid audience" error in backend

**Symptom**: Backend returns 401 with "invalid audience"

**Solution**:
1. Check `AUTH0_AUDIENCE` in `.env` matches API Identifier exactly
2. Verify `AUTH0_DOMAIN` is correct (should end with `.auth0.com`)
3. Restart your backend after changing `.env`

### Issue: User sees API permissions screen

**Symptom**: During login, user sees a consent screen asking for API permissions

**Solution**:
1. This is normal for first-time login
2. To skip it in development, enable "Allow Skipping User Consent" in API settings
3. User clicks "Accept" and won't see it again

## Testing Your Configuration

Use this curl command to test the full flow:

```bash
# 1. Get login URL
curl http://localhost:8000/api/v1/auth/auth0/login

# 2. Open the auth_url in browser, log in, copy the code from redirect

# 3. Exchange code for token
curl "http://localhost:8000/api/v1/auth/auth0/callback?code=YOUR_CODE"

# 4. Use the access_token to call protected endpoint
curl -X POST http://localhost:8000/api/v1/search/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "default", "filters": {"required_skills": ["Python"]}, "top_k": 10}'
```

## Summary: What You Actually Need to Configure

### One-Time Setup (Tenant Level):
1. ✅ Create API with identifier `https://api.staffingagent.com`
2. ✅ Enable RBAC on the API
3. ✅ Create Application (SPA) with callback URLs
4. ✅ Create 3 roles: superuser, project_manager, staff
5. ✅ Create Auth0 Action to add roles to tokens
6. ✅ Add action to Login flow and deploy

### Per-User Setup:
1. ✅ Create user with email/password
2. ✅ Assign ONE role to the user
3. ❌ **DO NOT assign API permissions** - not needed!
4. ❌ **DO NOT configure API access per user** - handled by roles!

The key insight: **Auth0's API and Permission system is optional**. We're using the simpler **Role-Based Access Control (RBAC)** approach where:
- Roles are assigned to users
- Roles are added to JWT tokens via Actions
- Backend checks roles from the token
- No need for per-user API configuration!
