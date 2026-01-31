# Frontend Auth0 Setup Guide

This guide explains how to set up and use Auth0 authentication in the Staffing Agent frontend application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Development](#development)
5. [How It Works](#how-it-works)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before setting up the frontend, make sure you have:

1. ✅ **Auth0 account** set up (see `AUTH0_SETUP.md`)
2. ✅ **Auth0 Application** created as a Single Page Application
3. ✅ **Auth0 API** configured with audience `https://api.staffingagent.com`
4. ✅ **Test users** created with different roles (see `AUTH0_TEST_USERS_SETUP.md`)
5. ✅ **Backend API** running with Auth0 protection enabled

## Installation

### Step 1: Install Dependencies

```bash
cd frontend
npm install
```

This will install all dependencies including `@auth0/auth0-react`.

## Configuration

### Step 2: Create Environment File

Copy the example environment file:

```bash
cp .env.example .env.local
```

### Step 3: Configure Auth0 Settings

Edit `.env.local` with your Auth0 credentials:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000/api/v1

# Auth0 Configuration
VITE_AUTH0_ENABLED=true
VITE_AUTH0_DOMAIN=your-tenant.us.auth0.com
VITE_AUTH0_CLIENT_ID=abc123xyz789...
VITE_AUTH0_AUDIENCE=https://api.staffingagent.com
VITE_AUTH0_REDIRECT_URI=http://localhost:5173/callback
```

**Where to find these values:**

| Variable | Where to Find It |
|----------|------------------|
| `VITE_AUTH0_DOMAIN` | Auth0 Dashboard → Applications → Your App → Domain |
| `VITE_AUTH0_CLIENT_ID` | Auth0 Dashboard → Applications → Your App → Client ID |
| `VITE_AUTH0_AUDIENCE` | Auth0 Dashboard → Applications → APIs → Identifier |
| `VITE_AUTH0_REDIRECT_URI` | Your frontend URL + `/callback` |

**IMPORTANT**:
- Never commit `.env.local` to version control
- The `.env.example` file is for reference only
- In production, set these as environment variables in your hosting platform

## Development

### Step 4: Start the Development Server

```bash
npm run dev
```

The application will start at `http://localhost:5173`.

### Step 5: Test Authentication

1. **Open** `http://localhost:5173` in your browser
2. You should see a "Log In" button in the top right
3. **Click "Log In"**
4. You'll be redirected to Auth0's login page
5. **Log in** with one of your test users (e.g., `superuser@test.com`)
6. You'll be redirected back to `/callback`, then to the home page
7. You should now see your **user menu** with your name and role badge

### Step 6: Test Role-Based Access

**As Superuser (`superuser@test.com`):**
- ✅ Can access all pages
- ✅ Can search for candidates
- ✅ Can view and edit all candidate profiles
- ✅ Can manage availability
- ✅ Can upload CVs

**As Project Manager (`pm@test.com`):**
- ✅ Can access all pages
- ✅ Can search for candidates
- ✅ Can view and edit all candidate profiles
- ✅ Can manage availability
- ✅ Can upload CVs

**As Staff (`staff@test.com`):**
- ❌ Cannot search (will get 403 error)
- ❌ Cannot list all candidates
- ✅ Can upload their own CV
- ✅ Can view/edit their own profile only

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend Application                                        │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ App.tsx                                                │ │
│  │  └─ Auth0ProviderWithConfig (wraps entire app)        │ │
│  │      └─ BrowserRouter                                  │ │
│  │          └─ AppContent                                 │ │
│  │              ├─ Navigation (with UserMenu)             │ │
│  │              └─ Routes (wrapped with RequireAuth)      │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Auth Components                                        │ │
│  │  ├─ useAuth() hook - access auth state                │ │
│  │  ├─ RequireAuth - protect routes                      │ │
│  │  ├─ UserMenu - login/logout UI                        │ │
│  │  └─ Callback - handle Auth0 redirect                  │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ API Client                                             │ │
│  │  └─ Automatically includes Bearer token in requests   │ │
│  └───────────────────────────────────────────────────────┘ │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               │ HTTP Requests with
                               │ Authorization: Bearer <token>
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Backend API                                                 │
│  └─ Validates JWT tokens                                    │
│  └─ Enforces role-based permissions                         │
└─────────────────────────────────────────────────────────────┘
```

### Authentication Flow

1. **User clicks "Log In"**
   - `UserMenu` component calls `login()` from `useAuth()` hook
   - User is redirected to Auth0 login page

2. **User enters credentials**
   - Auth0 validates credentials
   - Auth0 Action adds roles to JWT token

3. **Auth0 redirects back**
   - User redirected to `/callback` with authorization code
   - `Callback` component handles the redirect

4. **Token exchange**
   - Auth0 SDK exchanges code for access token and ID token
   - Tokens are cached in localStorage

5. **App updates**
   - `useAuth()` hook provides user info and auth state
   - `UserMenu` displays user's name and role
   - All API calls include `Authorization: Bearer <token>` header

6. **Automatic token refresh**
   - Auth0 SDK automatically refreshes tokens before expiry
   - No user interaction required

### Key Components

#### `lib/auth.tsx`

**`Auth0ProviderWithConfig`**: Wraps the entire app and provides Auth0 context.

```tsx
<Auth0ProviderWithConfig>
  <App />
</Auth0ProviderWithConfig>
```

**`useAuth()` hook**: Access authentication state anywhere in the app.

```tsx
const { isAuthenticated, user, login, logout, hasRole } = useAuth();
```

**`RequireAuth` component**: Protect routes that require authentication.

```tsx
<Route path="/" element={
  <RequireAuth>
    <Search />
  </RequireAuth>
} />
```

**`withRequiredRole()` HOC**: Protect components that require specific roles.

```tsx
export default withRequiredRole(SearchPage, UserRole.PROJECT_MANAGER);
```

#### `lib/api.ts`

The API client automatically includes the Auth0 access token in all requests:

```typescript
private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options?.headers,
  };

  if (this.getAccessToken) {
    const token = await this.getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  // ... make request
}
```

#### `components/UserMenu.tsx`

Displays login button when logged out, user menu when logged in:

- Shows user's name and email
- Displays role badge (Superuser, PM, Staff)
- Provides logout functionality
- Dropdown menu with user info

### Files Added/Modified

**New Files:**
- `frontend/src/lib/auth.tsx` - Auth0 provider and hooks
- `frontend/src/components/UserMenu.tsx` - User menu UI
- `frontend/src/routes/Callback.tsx` - Auth0 callback handler
- `frontend/.env.example` - Environment template

**Modified Files:**
- `frontend/src/App.tsx` - Wrapped with Auth0Provider, added UserMenu
- `frontend/src/lib/config.ts` - Added Auth0 configuration
- `frontend/src/lib/types.ts` - Added Auth0 types
- `frontend/src/lib/api.ts` - Added token injection
- `frontend/package.json` - Added @auth0/auth0-react dependency

## Production Deployment

### Environment Variables

Set these environment variables in your production hosting platform:

```bash
VITE_API_URL=https://api.yourdomain.com/api/v1
VITE_AUTH0_ENABLED=true
VITE_AUTH0_DOMAIN=your-tenant.us.auth0.com
VITE_AUTH0_CLIENT_ID=production_client_id
VITE_AUTH0_AUDIENCE=https://api.staffingagent.com
VITE_AUTH0_REDIRECT_URI=https://yourdomain.com/callback
```

### Build for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

### Update Auth0 Settings

In Auth0 Dashboard → Applications → Your App → Settings:

1. **Add production URLs** to Allowed Callback URLs:
   ```
   https://yourdomain.com/callback
   ```

2. **Add production URLs** to Allowed Logout URLs:
   ```
   https://yourdomain.com
   ```

3. **Add production URLs** to Allowed Web Origins:
   ```
   https://yourdomain.com
   ```

4. **Save Changes**

### Deploy

Deploy the `dist/` directory to your hosting platform:

**Vercel:**
```bash
npm install -g vercel
vercel --prod
```

**Netlify:**
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

**AWS S3 + CloudFront:**
```bash
aws s3 sync dist/ s3://your-bucket/
aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/*"
```

### HTTPS Requirement

⚠️ **IMPORTANT**: Auth0 requires HTTPS in production. Make sure your frontend is served over HTTPS.

Most hosting platforms (Vercel, Netlify, AWS CloudFront) provide HTTPS automatically.

## Troubleshooting

### Issue: "Auth0 not configured" warning

**Symptom**: Console shows "Auth0 not configured. Running without authentication."

**Solution**:
- Check that `.env.local` exists and has the correct values
- Make sure `VITE_AUTH0_DOMAIN` and `VITE_AUTH0_CLIENT_ID` are set
- Restart the dev server after changing `.env.local`

### Issue: Redirect loop after login

**Symptom**: After logging in, you're stuck in an infinite redirect loop.

**Solution**:
- Check that `VITE_AUTH0_REDIRECT_URI` matches your callback URL
- Verify `/callback` route exists in your app
- Check browser console for errors

### Issue: 401 Unauthorized from API

**Symptom**: API requests return 401 even when logged in.

**Solution**:
- Check that `VITE_AUTH0_AUDIENCE` matches the backend's `AUTH0_AUDIENCE`
- Verify the access token is being sent (check Network tab → Request Headers)
- Decode the token at jwt.io to verify it has the `audience` claim

### Issue: 403 Forbidden for certain actions

**Symptom**: Logged in but getting 403 errors.

**Solution**:
- Check that user has the correct role assigned in Auth0
- Verify Auth0 Action is deployed and adding roles to token
- Decode token at jwt.io to verify `https://staffingagent.com/roles` claim exists

### Issue: Token expired error

**Symptom**: After some time, requests start failing with "Token has expired".

**Solution**:
- Auth0 SDK should automatically refresh tokens
- Check that `cacheLocation="localstorage"` is set in Auth0Provider
- Try logging out and logging back in
- Check Auth0 dashboard → Applications → Settings → Token Expiration

### Issue: Cross-Origin errors

**Symptom**: CORS errors in browser console.

**Solution**:
- Verify backend has CORS enabled for your frontend domain
- Check backend's `CORS_ORIGINS` setting
- Make sure `VITE_API_URL` in frontend matches backend URL exactly

## Testing Checklist

Before deploying to production, test these scenarios:

### Authentication Flow
- [ ] Can log in with superuser account
- [ ] Can log in with project manager account
- [ ] Can log in with staff account
- [ ] User menu shows correct name and role
- [ ] Can log out successfully
- [ ] After logout, redirected to login screen

### Authorization (Superuser)
- [ ] Can access search page
- [ ] Can view all candidates
- [ ] Can edit any candidate profile
- [ ] Can upload CVs
- [ ] Can manage availability

### Authorization (Project Manager)
- [ ] Can access search page
- [ ] Can view all candidates
- [ ] Can edit any candidate profile
- [ ] Can upload CVs
- [ ] Can manage availability

### Authorization (Staff)
- [ ] Search page shows permission error
- [ ] Candidates list shows permission error
- [ ] Can upload own CV
- [ ] Can view own profile
- [ ] Can edit own profile
- [ ] Cannot edit other profiles

### Error Handling
- [ ] Invalid login shows error message
- [ ] Expired token auto-refreshes
- [ ] Network errors show user-friendly message
- [ ] 403 errors show "Access Denied" message

## Security Best Practices

1. **Never commit secrets**:
   - Add `.env.local` to `.gitignore` ✅ (already done)
   - Never commit Auth0 Client Secret to frontend

2. **Use environment variables**:
   - All Auth0 config comes from environment variables
   - Different values for dev/staging/production

3. **HTTPS only in production**:
   - Auth0 requires HTTPS for production
   - Use hosting platforms that provide automatic HTTPS

4. **Rotate credentials regularly**:
   - Generate new Client Secrets periodically
   - Revoke old credentials in Auth0 dashboard

5. **Monitor for security issues**:
   - Check Auth0 dashboard for failed login attempts
   - Review Auth0 logs for suspicious activity

## Next Steps

Now that Auth0 is set up on the frontend:

1. **Test thoroughly** with all three user roles
2. **Deploy to staging** environment
3. **Perform end-to-end testing** in staging
4. **Deploy to production** with production Auth0 settings
5. **Monitor** for any authentication issues

For backend setup, see `AUTH0_SETUP.md`.

For creating test users, see `AUTH0_TEST_USERS_SETUP.md`.

For API configuration, see `AUTH0_API_CONFIGURATION.md`.
