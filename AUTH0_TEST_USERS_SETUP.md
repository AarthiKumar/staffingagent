# Creating Test Users with Different Roles in Auth0

This guide walks you through creating test users with the three different roles: `superuser`, `project_manager`, and `staff`.

## Step 1: Create the Roles

First, you need to create the three roles in Auth0.

### 1.1 Navigate to Roles

1. Go to your [Auth0 Dashboard](https://manage.auth0.com/)
2. Click on **User Management** in the left sidebar
3. Click on **Roles**

### 1.2 Create Superuser Role

1. Click **+ Create Role** button
2. Enter the following:
   - **Name**: `superuser`
   - **Description**: `Full system access - can manage users, view all data, and perform all actions`
3. Click **Create**

### 1.3 Create Project Manager Role

1. Click **+ Create Role** button again
2. Enter the following:
   - **Name**: `project_manager`
   - **Description**: `Can search for staff, view all candidates, and manage availability`
3. Click **Create**

### 1.4 Create Staff Role

1. Click **+ Create Role** button again
2. Enter the following:
   - **Name**: `staff`
   - **Description**: `Can upload and update their own CV only`
3. Click **Create**

## Step 2: Create Test Users

Now create test users for each role.

### 2.1 Navigate to Users

1. In the Auth0 Dashboard, click on **User Management** → **Users**
2. Click the **+ Create User** button

### 2.2 Create Superuser Test Account

1. Click **+ Create User**
2. Fill in the form:
   - **Email**: `superuser@test.com` (or your own email + alias like `youremail+superuser@gmail.com`)
   - **Password**: Create a strong password (e.g., `TestPass123!`)
   - **Connection**: `Username-Password-Authentication` (the default database)
3. Click **Create**
4. **Important**: If you're using a real email, check your inbox for the verification email and verify the account

### 2.3 Create Project Manager Test Account

1. Click **+ Create User** again
2. Fill in the form:
   - **Email**: `pm@test.com` (or `youremail+pm@gmail.com`)
   - **Password**: `TestPass123!`
   - **Connection**: `Username-Password-Authentication`
3. Click **Create**
4. Verify the email if required

### 2.4 Create Staff Test Account

1. Click **+ Create User** again
2. Fill in the form:
   - **Email**: `staff@test.com` (or `youremail+staff@gmail.com`)
   - **Password**: `TestPass123!`
   - **Connection**: `Username-Password-Authentication`
3. Click **Create**
4. Verify the email if required

**Pro Tip**: Gmail users can use the `+` trick to create multiple test accounts:
- `yourname+superuser@gmail.com`
- `yourname+pm@gmail.com`
- `yourname+staff@gmail.com`

All emails will arrive in your main inbox, but Auth0 will treat them as separate accounts.

## Step 3: Assign Roles to Users

Now assign the appropriate roles to each test user.

### 3.1 Assign Superuser Role

1. Go to **User Management** → **Users**
2. Click on the user with email `superuser@test.com`
3. Click the **Roles** tab
4. Click **Assign Roles** button
5. Select the `superuser` role from the list
6. Click **Assign**

### 3.2 Assign Project Manager Role

1. Go back to **Users** list
2. Click on the user with email `pm@test.com`
3. Click the **Roles** tab
4. Click **Assign Roles** button
5. Select the `project_manager` role
6. Click **Assign**

### 3.3 Assign Staff Role

1. Go back to **Users** list
2. Click on the user with email `staff@test.com`
3. Click the **Roles** tab
4. Click **Assign Roles** button
5. Select the `staff` role
6. Click **Assign**

## Step 4: Verify Role Assignment

Let's verify that roles are correctly assigned:

### 4.1 Check Each User

For each test user:
1. Go to **User Management** → **Users**
2. Click on the user
3. Go to the **Roles** tab
4. You should see their assigned role listed

### 4.2 Quick Verification Checklist

- [ ] `superuser@test.com` has the `superuser` role
- [ ] `pm@test.com` has the `project_manager` role
- [ ] `staff@test.com` has the `staff` role

## Step 5: Create Auth0 Action to Add Roles to Tokens

This is **CRITICAL** - without this, roles won't be included in JWT tokens!

### 5.1 Navigate to Actions

1. In Auth0 Dashboard, click on **Actions** in the left sidebar
2. Click on **Flows**
3. Click on **Login**

### 5.2 Create Custom Action

1. Click the **+** (plus) button on the right side
2. Select **Build Custom**
3. Fill in the form:
   - **Name**: `Add Roles to Token`
   - **Trigger**: `Login / Post Login`
   - **Runtime**: `Node 18` (recommended)
4. Click **Create**

### 5.3 Add the Action Code

Replace the default code with:

```javascript
/**
 * Handler that will be called during the execution of a PostLogin flow.
 *
 * @param {Event} event - Details about the user and the context in which they are logging in.
 * @param {PostLoginAPI} api - Interface whose methods can be used to change the behavior of the login.
 */
exports.onExecutePostLogin = async (event, api) => {
  const namespace = 'https://staffingagent.com';

  if (event.authorization) {
    // Add roles to access token (for API authorization)
    api.accessToken.setCustomClaim(`${namespace}/roles`, event.authorization.roles);

    // Add roles to ID token (for frontend user info)
    api.idToken.setCustomClaim(`${namespace}/roles`, event.authorization.roles);

    // Optional: Add email to make it easier to debug
    api.accessToken.setCustomClaim(`${namespace}/email`, event.user.email);
  }
};
```

5. Click **Deploy** (top right)

### 5.4 Add Action to Login Flow

1. Go back to **Actions** → **Flows** → **Login**
2. You should see your custom action in the right sidebar under **Custom**
3. **Drag and drop** the "Add Roles to Token" action into the flow (between "Start" and "Complete")
4. Click **Apply** (top right)

## Step 6: Test Your Setup

Now let's test that everything works!

### 6.1 Test Login with Superuser

1. Open your backend API documentation: `http://localhost:8000/docs`
2. Find the `/api/v1/auth/auth0/login` endpoint
3. Click **Try it out**
4. Click **Execute**
5. Copy the `auth_url` from the response
6. Open it in a browser
7. Log in with `superuser@test.com` / `TestPass123!`
8. You'll be redirected to the callback URL with a `code` parameter
9. Copy that code

### 6.2 Exchange Code for Token

1. Go back to `/docs`
2. Find `/api/v1/auth/auth0/callback`
3. Click **Try it out**
4. Paste the code from the URL
5. Click **Execute**
6. You should receive:
   ```json
   {
     "access_token": "eyJhbGc...",
     "id_token": "eyJhbGc...",
     "token_type": "Bearer",
     "expires_in": 86400
   }
   ```
7. Copy the `access_token`

### 6.3 Verify Token Contains Roles

You can decode the JWT token to verify it contains roles:

1. Go to [jwt.io](https://jwt.io)
2. Paste your `access_token` in the "Encoded" section
3. Look at the decoded payload - you should see:
   ```json
   {
     "https://staffingagent.com/roles": ["superuser"],
     "https://staffingagent.com/email": "superuser@test.com",
     ...
   }
   ```

### 6.4 Test API Endpoints

Now test the actual API with the token:

#### Test 1: Search (requires project_manager or superuser)

```bash
curl -X POST "http://localhost:8000/api/v1/search/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "default",
    "filters": {
      "required_skills": ["Python"]
    },
    "top_k": 10
  }'
```

**Expected**: ✅ Success (200 OK) - Superuser can search

#### Test 2: Repeat with Staff Token

1. Log in as `staff@test.com`
2. Get the access token
3. Try the same search endpoint

**Expected**: ❌ 403 Forbidden - Staff cannot search

## Step 7: Quick Test Script

Here's a Python script to test all three users:

```python
#!/usr/bin/env python3
"""
Test Auth0 integration with all three user roles.

Requirements:
    pip install requests pyjwt
"""

import requests
import jwt
import json
from typing import Dict

BASE_URL = "http://localhost:8000/api/v1"

def get_auth_url() -> str:
    """Step 1: Get Auth0 login URL"""
    response = requests.get(f"{BASE_URL}/auth/auth0/login")
    return response.json()["auth_url"]

def exchange_code_for_token(code: str) -> Dict:
    """Step 2: Exchange authorization code for tokens"""
    response = requests.get(f"{BASE_URL}/auth/auth0/callback?code={code}")
    return response.json()

def decode_token(token: str) -> Dict:
    """Decode JWT token (without verification for debugging)"""
    return jwt.decode(token, options={"verify_signature": False})

def test_search(access_token: str, user_role: str):
    """Test search endpoint"""
    print(f"\n🔍 Testing search as {user_role}...")

    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "agent_id": "default",
        "filters": {"required_skills": ["Python"]},
        "top_k": 10
    }

    response = requests.post(f"{BASE_URL}/search/", json=payload, headers=headers)

    if response.status_code == 200:
        print(f"✅ SUCCESS: {user_role} can search")
        print(f"   Found {len(response.json()['results'])} candidates")
    elif response.status_code == 403:
        print(f"❌ DENIED: {user_role} cannot search (expected for staff)")
    else:
        print(f"⚠️  ERROR: {response.status_code} - {response.text}")

def test_list_candidates(access_token: str, user_role: str):
    """Test list candidates endpoint"""
    print(f"\n📋 Testing list candidates as {user_role}...")

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/candidates/", headers=headers)

    if response.status_code == 200:
        print(f"✅ SUCCESS: {user_role} can list candidates")
        print(f"   Total: {response.json()['total']} candidates")
    elif response.status_code == 403:
        print(f"❌ DENIED: {user_role} cannot list candidates (expected for staff)")
    else:
        print(f"⚠️  ERROR: {response.status_code} - {response.text}")

def main():
    print("=" * 60)
    print("Auth0 Role-Based Access Control Test")
    print("=" * 60)

    # Instructions for manual testing
    print("\n📝 MANUAL STEPS REQUIRED:")
    print("1. Run this script")
    print("2. For each user, you'll get a login URL")
    print("3. Open the URL in a browser and log in")
    print("4. Copy the 'code' parameter from the redirect URL")
    print("5. Paste it back into this script")
    print()

    test_users = [
        {"email": "superuser@test.com", "role": "superuser"},
        {"email": "pm@test.com", "role": "project_manager"},
        {"email": "staff@test.com", "role": "staff"},
    ]

    for user in test_users:
        print(f"\n{'=' * 60}")
        print(f"Testing: {user['email']} ({user['role']})")
        print(f"{'=' * 60}")

        # Get login URL
        auth_url = get_auth_url()
        print(f"\n🔗 Open this URL in your browser:")
        print(f"   {auth_url}")
        print(f"\n   Log in as: {user['email']}")

        # Wait for user to complete login and get code
        code = input("\n📋 Paste the 'code' parameter from redirect URL: ").strip()

        # Exchange code for token
        try:
            tokens = exchange_code_for_token(code)
            access_token = tokens["access_token"]

            # Decode and display token info
            payload = decode_token(access_token)
            roles = payload.get("https://staffingagent.com/roles", [])
            email = payload.get("https://staffingagent.com/email", "unknown")

            print(f"\n✅ Token obtained!")
            print(f"   Email: {email}")
            print(f"   Roles: {roles}")

            # Run tests
            test_search(access_token, user["role"])
            test_list_candidates(access_token, user["role"])

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            continue

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

Save this as `test_auth0_roles.py` and run:

```bash
python test_auth0_roles.py
```

## Troubleshooting

### Issue: Roles not in token

**Solution**: Make sure the Auth0 Action is:
1. Created with the correct code
2. Deployed (not just saved as draft)
3. Added to the Login flow
4. The flow is "Applied" (not just modified)

### Issue: "Invalid token" error

**Solutions**:
- Check that `AUTH0_DOMAIN` in `.env` matches your Auth0 tenant
- Verify `AUTH0_AUDIENCE` matches what you set in Auth0 API settings
- Ensure the token hasn't expired (default is 24 hours)

### Issue: User can't log in

**Solutions**:
- Verify email is verified in Auth0 Users dashboard
- Check that the password meets complexity requirements
- Try resetting the password from Auth0 dashboard

### Issue: 403 Forbidden for superuser

**Solutions**:
- Check that the role is assigned in Auth0 dashboard
- Verify the Auth0 Action is deployed and in the Login flow
- Decode the JWT at jwt.io to see if roles are present
- Check backend logs for authentication errors

## Summary of Test Users

| Email | Password | Role | Can Search | Can View All | Can Upload CV | Can Update Own Profile |
|-------|----------|------|------------|--------------|---------------|------------------------|
| `superuser@test.com` | `TestPass123!` | superuser | ✅ | ✅ | ✅ | ✅ |
| `pm@test.com` | `TestPass123!` | project_manager | ✅ | ✅ | ✅ | ✅ |
| `staff@test.com` | `TestPass123!` | staff | ❌ | ❌ | ✅ | ✅ (own only) |

## Next Steps

Once your test users are working:

1. **Create real users**: Follow the same process for production users
2. **Frontend integration**: Use the Auth0 React SDK to add login UI
3. **Automate testing**: Use the provided Python script or create automated tests
4. **Production setup**: Create a separate Auth0 tenant for production

## Security Best Practices

1. **Never commit passwords**: Use environment variables
2. **Use strong passwords**: For production, require 2FA
3. **Limit superuser access**: Only assign to trusted administrators
4. **Regular audits**: Review user permissions quarterly
5. **Token expiration**: Keep default short expiration (24 hours)
6. **HTTPS only**: Never send tokens over HTTP in production
