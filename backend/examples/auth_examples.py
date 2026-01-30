"""
Examples of using Auth0 authenticated endpoints with different user roles.

This file demonstrates how the role-based access control works for different
user types: superuser, project_manager, and staff.
"""

import requests

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

# Example tokens (in production, these come from Auth0 login flow)
# These are just placeholders - real tokens come from Auth0
SUPERUSER_TOKEN = "eyJhbGc..."  # Token with superuser role
PROJECT_MANAGER_TOKEN = "eyJhbGc..."  # Token with project_manager role
STAFF_TOKEN = "eyJhbGc..."  # Token with staff role


def get_headers(token: str) -> dict:
    """Get authorization headers with bearer token"""
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# EXAMPLE 1: Search for candidates (Project Manager or Superuser only)
# ============================================================================

def search_candidates_as_project_manager():
    """
    ✅ Allowed: Project managers can search for candidates
    """
    search_payload = {
        "agent_id": "default",
        "filters": {
            "required_skills": ["Python", "Kubernetes"],
            "min_years": {"Python": 3},
            "availability_from": "2024-02-01",
        },
        "text": "DevOps engineer with cloud experience",
        "top_k": 20,
    }

    response = requests.post(
        f"{BASE_URL}/search/",
        json=search_payload,
        headers=get_headers(PROJECT_MANAGER_TOKEN),
    )

    if response.status_code == 200:
        results = response.json()
        print(f"Found {len(results['results'])} candidates")
        for result in results["results"]:
            print(f"- {result['name']} (score: {result['score']})")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def search_candidates_as_staff():
    """
    ❌ Denied: Staff cannot search for candidates
    Expected: 403 Forbidden
    """
    search_payload = {
        "agent_id": "default",
        "filters": {"required_skills": ["Python"]},
        "top_k": 20,
    }

    response = requests.post(
        f"{BASE_URL}/search/",
        json=search_payload,
        headers=get_headers(STAFF_TOKEN),
    )

    # Should return 403 Forbidden
    print(f"Status: {response.status_code}")
    print(f"Message: {response.json()}")


# ============================================================================
# EXAMPLE 2: View candidate profiles
# ============================================================================

def view_own_profile_as_staff():
    """
    ✅ Allowed: Staff can view their own profile (email matches)
    """
    # Assuming the staff member's candidate_id is known
    candidate_id = "123e4567-e89b-12d3-a456-426614174000"

    response = requests.get(
        f"{BASE_URL}/candidates/{candidate_id}",
        headers=get_headers(STAFF_TOKEN),
    )

    if response.status_code == 200:
        profile = response.json()
        print(f"Profile: {profile['name']} - {profile['email']}")
        print(f"Skills: {len(profile['sections'])} sections")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def view_other_profile_as_staff():
    """
    ❌ Denied: Staff cannot view other candidates' profiles
    Expected: 403 Forbidden
    """
    # Trying to view someone else's profile
    other_candidate_id = "999e4567-e89b-12d3-a456-426614174999"

    response = requests.get(
        f"{BASE_URL}/candidates/{other_candidate_id}",
        headers=get_headers(STAFF_TOKEN),
    )

    # Should return 403 Forbidden
    print(f"Status: {response.status_code}")
    print(f"Message: {response.json()}")


def view_any_profile_as_project_manager():
    """
    ✅ Allowed: Project managers can view any candidate profile
    """
    candidate_id = "123e4567-e89b-12d3-a456-426614174000"

    response = requests.get(
        f"{BASE_URL}/candidates/{candidate_id}",
        headers=get_headers(PROJECT_MANAGER_TOKEN),
    )

    if response.status_code == 200:
        profile = response.json()
        print(f"Profile: {profile['name']} - {profile['email']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


# ============================================================================
# EXAMPLE 3: Update candidate information
# ============================================================================

def update_own_profile_as_staff():
    """
    ✅ Allowed: Staff can update their own profile
    """
    candidate_id = "123e4567-e89b-12d3-a456-426614174000"

    update_payload = {
        "name": "John Doe",
        "location": "San Francisco, CA",
    }

    response = requests.put(
        f"{BASE_URL}/candidates/{candidate_id}",
        json=update_payload,
        headers=get_headers(STAFF_TOKEN),
    )

    if response.status_code == 200:
        print(f"Profile updated: {response.json()}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def update_other_profile_as_staff():
    """
    ❌ Denied: Staff cannot update other candidates' profiles
    Expected: 403 Forbidden
    """
    other_candidate_id = "999e4567-e89b-12d3-a456-426614174999"

    update_payload = {"location": "New York, NY"}

    response = requests.put(
        f"{BASE_URL}/candidates/{other_candidate_id}",
        json=update_payload,
        headers=get_headers(STAFF_TOKEN),
    )

    # Should return 403 Forbidden
    print(f"Status: {response.status_code}")
    print(f"Message: {response.json()}")


# ============================================================================
# EXAMPLE 4: Update CV sections
# ============================================================================

def update_own_section_as_staff():
    """
    ✅ Allowed: Staff can update sections of their own CV
    """
    section_id = "abc12345-e89b-12d3-a456-426614174000"

    update_payload = {
        "text": "Python, Kubernetes, Docker, AWS, Terraform, Jenkins, GitLab CI, Linux"
    }

    response = requests.put(
        f"{BASE_URL}/sections/{section_id}",
        json=update_payload,
        headers=get_headers(STAFF_TOKEN),
    )

    if response.status_code == 200:
        result = response.json()
        print(f"Section updated: {result['type']}")
        print(f"Embeddings regenerated: {result['embeddings_regenerated']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def delete_section_as_staff():
    """
    ❌ Denied: Staff cannot delete sections (requires project_manager role)
    Expected: 403 Forbidden
    """
    section_id = "abc12345-e89b-12d3-a456-426614174000"

    response = requests.delete(
        f"{BASE_URL}/sections/{section_id}",
        headers=get_headers(STAFF_TOKEN),
    )

    # Should return 403 Forbidden
    print(f"Status: {response.status_code}")
    print(f"Message: {response.json()}")


def delete_section_as_project_manager():
    """
    ✅ Allowed: Project managers can delete sections
    """
    section_id = "abc12345-e89b-12d3-a456-426614174000"

    response = requests.delete(
        f"{BASE_URL}/sections/{section_id}",
        headers=get_headers(PROJECT_MANAGER_TOKEN),
    )

    if response.status_code == 200:
        print(f"Section deleted: {response.json()}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


# ============================================================================
# EXAMPLE 5: Manage availability
# ============================================================================

def update_availability_as_project_manager():
    """
    ✅ Allowed: Project managers can update candidate availability
    """
    candidate_id = "123e4567-e89b-12d3-a456-426614174000"

    availability_payload = {
        "candidate_id": candidate_id,
        "available_from": "2024-03-01",
        "capacity_pct": 50,
        "notes": "Available for 50% allocation on new projects",
    }

    response = requests.put(
        f"{BASE_URL}/availability/{candidate_id}",
        json=availability_payload,
        headers=get_headers(PROJECT_MANAGER_TOKEN),
    )

    if response.status_code == 200:
        print(f"Availability updated: {response.json()}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def update_availability_as_staff():
    """
    ❌ Denied: Staff cannot update availability (requires project_manager role)
    Expected: 403 Forbidden
    """
    candidate_id = "123e4567-e89b-12d3-a456-426614174000"

    availability_payload = {
        "candidate_id": candidate_id,
        "available_from": "2024-03-01",
        "capacity_pct": 100,
    }

    response = requests.put(
        f"{BASE_URL}/availability/{candidate_id}",
        json=availability_payload,
        headers=get_headers(STAFF_TOKEN),
    )

    # Should return 403 Forbidden
    print(f"Status: {response.status_code}")
    print(f"Message: {response.json()}")


# ============================================================================
# EXAMPLE 6: Upload CVs
# ============================================================================

def upload_cv_as_staff():
    """
    ✅ Allowed: All authenticated users can upload CVs
    Staff should upload their own CV (email in manual_email should match their Auth0 email)
    """
    import base64

    # Read CV file and encode to base64
    with open("resume.pdf", "rb") as f:
        content_base64 = base64.b64encode(f.read()).decode("utf-8")

    ingest_payload = {
        "agent_id": "default",
        "document_type": "resume",
        "filename": "john_doe_resume.pdf",
        "content_base64": content_base64,
        "use_ocr": False,
        # Manual fields should match the staff member's Auth0 email
        "manual_email": "john.doe@example.com",  # Should match STAFF_TOKEN email
    }

    response = requests.post(
        f"{BASE_URL}/ingest/",
        json=ingest_payload,
        headers=get_headers(STAFF_TOKEN),
    )

    if response.status_code == 200:
        result = response.json()
        print(f"CV uploaded: {result['document_id']}")
        print(f"Sections: {result['sections_count']}")
        print(f"Embeddings: {result['embeddings_count']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def approve_merge_as_project_manager():
    """
    ✅ Allowed: Project managers can approve CV merges for duplicate candidates
    """
    merge_payload = {
        "candidate_id": "123e4567-e89b-12d3-a456-426614174000",
        "new_document_id": "abc12345-e89b-12d3-a456-426614174abc",
        "approved_data": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-1234",
            "location": "San Francisco, CA",
        },
    }

    response = requests.post(
        f"{BASE_URL}/ingest/approve-merge",
        json=merge_payload,
        headers=get_headers(PROJECT_MANAGER_TOKEN),
    )

    if response.status_code == 200:
        print(f"Merge approved: {response.json()}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def approve_merge_as_staff():
    """
    ❌ Denied: Staff cannot approve merges (requires project_manager role)
    Expected: 403 Forbidden
    """
    merge_payload = {
        "candidate_id": "123e4567-e89b-12d3-a456-426614174000",
        "new_document_id": "abc12345-e89b-12d3-a456-426614174abc",
        "approved_data": {"name": "John Doe"},
    }

    response = requests.post(
        f"{BASE_URL}/ingest/approve-merge",
        json=merge_payload,
        headers=get_headers(STAFF_TOKEN),
    )

    # Should return 403 Forbidden
    print(f"Status: {response.status_code}")
    print(f"Message: {response.json()}")


# ============================================================================
# EXAMPLE 7: List all candidates
# ============================================================================

def list_candidates_as_project_manager():
    """
    ✅ Allowed: Project managers can list all candidates
    """
    response = requests.get(
        f"{BASE_URL}/candidates/",
        params={"page": 1, "page_size": 50, "search": "engineer"},
        headers=get_headers(PROJECT_MANAGER_TOKEN),
    )

    if response.status_code == 200:
        result = response.json()
        print(f"Total candidates: {result['total']}")
        print(f"Page {result['page']}: {len(result['candidates'])} results")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def list_candidates_as_staff():
    """
    ❌ Denied: Staff cannot list all candidates
    Expected: 403 Forbidden
    """
    response = requests.get(
        f"{BASE_URL}/candidates/",
        headers=get_headers(STAFF_TOKEN),
    )

    # Should return 403 Forbidden
    print(f"Status: {response.status_code}")
    print(f"Message: {response.json()}")


# ============================================================================
# Permission Matrix Summary
# ============================================================================

"""
PERMISSION MATRIX
=================

Endpoint                              | Superuser | Project Manager | Staff
--------------------------------------|-----------|-----------------|-------
POST /search/                         |     ✅    |       ✅        |   ❌
GET  /candidates/                     |     ✅    |       ✅        |   ❌
GET  /candidates/{id}                 |     ✅    |       ✅        |   ✅ (own only)
PUT  /candidates/{id}                 |     ✅    |       ✅        |   ✅ (own only)
GET  /availability/                   |     ✅    |       ✅        |   ❌
PUT  /availability/{id}               |     ✅    |       ✅        |   ❌
POST /availability/upload             |     ✅    |       ✅        |   ❌
POST /ingest/                         |     ✅    |       ✅        |   ✅
POST /ingest/approve-merge            |     ✅    |       ✅        |   ❌
PUT  /sections/{id}                   |     ✅    |       ✅        |   ✅ (own only)
DELETE /sections/{id}                 |     ✅    |       ✅        |   ❌

Notes:
- "Own only" means staff can only access resources where the candidate email
  matches their Auth0 email address
- Superuser has full access to all endpoints
- Project Manager can search, view all candidates, and manage availability
- Staff can only upload and manage their own CV
"""

if __name__ == "__main__":
    print(__doc__)
    print("\nSee function examples above for usage patterns.")
    print("\nTo test these examples, you need to:")
    print("1. Set up Auth0 following AUTH0_SETUP.md")
    print("2. Create test users with different roles")
    print("3. Get access tokens from Auth0 for each user")
    print("4. Replace the placeholder tokens with real tokens")
    print("5. Run individual example functions")
