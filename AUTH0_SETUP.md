# Auth0 Configuration for aal.yookthi.ai

This document provides the exact Auth0 configuration needed for production deployment.

## 1. Create Auth0 API

1. Go to **Auth0 Dashboard** → **Applications** → **APIs**
2. Click **Create API**
3. Configure:
   - **Name:** Staffing Agent API
   - **Identifier:** `https://aal.yookthi.ai`
   - **Signing Algorithm:** RS256
4. Click **Create**

## 2. Create Auth0 Application (SPA)

1. Go to **Auth0 Dashboard** → **Applications** → **Applications**
2. Click **Create Application**
3. Configure:
   - **Name:** Staffing Agent Frontend
   - **Application Type:** Single Page Application
4. Click **Create**

### Application Settings

Go to the **Settings** tab and configure:

- **Allowed Callback URLs:**
  ```
  https://aal.yookthi.ai/callback
  ```

- **Allowed Logout URLs:**
  ```
  https://aal.yookthi.ai
  ```

- **Allowed Web Origins:**
  ```
  https://aal.yookthi.ai
  ```

- **Allowed Origins (CORS):**
  ```
  https://aal.yookthi.ai
  ```

### Save Configuration

- **Domain:** Copy this (e.g., `your-tenant.auth0.com`)
- **Client ID:** Copy this

## 3. Create Auth0 Action (Post-Login Trigger)

1. Go to **Auth0 Dashboard** → **Actions** → **Flows**
2. Select **Login** flow
3. Click **+ Add Action** → **Build Custom**
4. Configure:
   - **Name:** Add Custom Claims
   - **Trigger:** Post Login
   - **Runtime:** Node 18

### Action Code

```javascript
exports.onExecutePostLogin = async (event, api) => {
  const namespace = 'https://aal.yookthi.ai';

  if (event.authorization) {
    api.idToken.setCustomClaim(`${namespace}/roles`, event.authorization.roles);
    api.accessToken.setCustomClaim(`${namespace}/roles`, event.authorization.roles);
  }
};
```

5. Click **Deploy**
6. **Drag the action** into the Login flow
7. Click **Apply**

## 4. Configure Roles and Permissions

### Create Roles

1. Go to **User Management** → **Roles**
2. Create the following roles:

#### Superuser Role
- **Name:** `superuser`
- **Description:** Full system access
- **Permissions:** (Assign all API permissions)

#### Project Manager Role
- **Name:** `project_manager`
- **Description:** Can search and manage candidates
- **Permissions:**
  - `search:candidates`
  - `view:candidates`
  - `manage:availability`

#### Candidate Role
- **Name:** `candidate`
- **Description:** Can manage own CV and availability
- **Permissions:**
  - `upload:cv`
  - `edit:own_cv`
  - `edit:own_availability`

### Assign Roles to Users

1. Go to **User Management** → **Users**
2. Select a user
3. Go to **Roles** tab
4. Click **Assign Roles**
5. Select appropriate role(s)

## 5. Environment Variables

Update your `.env.production` file with the values from Auth0:

```bash
# Backend Auth0 settings
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=<your-client-id-from-step-2>
AUTH0_AUDIENCE=https://aal.yookthi.ai

# Frontend Auth0 settings (for Docker build args)
VITE_AUTH0_DOMAIN=your-tenant.auth0.com
VITE_AUTH0_CLIENT_ID=<your-client-id-from-step-2>
VITE_AUTH0_AUDIENCE=https://aal.yookthi.ai
VITE_API_BASE_URL=https://aal.yookthi.ai/api/v1
```

## 6. Test Authentication

After deployment, test the authentication flow:

1. Go to `https://aal.yookthi.ai`
2. Click **Sign In**
3. You should be redirected to Auth0
4. After successful login, you should be redirected back to the application

### Debugging

If authentication fails:

1. Check browser console for errors
2. Check backend logs:
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f backend
   ```
3. Verify Auth0 configuration matches exactly
4. Check that roles are assigned to your user
5. Verify the namespace in the Auth0 Action matches `https://aal.yookthi.ai`

## Summary Checklist

- [ ] Auth0 API created with identifier `https://aal.yookthi.ai`
- [ ] Auth0 SPA application created with correct callback URLs
- [ ] Auth0 Action created with namespace `https://aal.yookthi.ai`
- [ ] Auth0 Action deployed and added to Login flow
- [ ] Roles created (superuser, project_manager, candidate)
- [ ] At least one user has a role assigned
- [ ] `.env.production` updated with Auth0 credentials
- [ ] Application deployed and tested

## Important Notes

1. **Namespace Consistency:** The namespace `https://aal.yookthi.ai` must be consistent across:
   - Auth0 Action
   - Backend code (`backend/app/core/security.py`)
   - Frontend code (`frontend/src/App.tsx`)

2. **Audience Matching:** The `AUTH0_AUDIENCE` must match your API identifier exactly.

3. **Domain Format:** The `AUTH0_DOMAIN` should NOT include `https://`, just the domain (e.g., `your-tenant.auth0.com`).

4. **Callback URLs:** Must match your deployed domain exactly, including the protocol (`https://`).
