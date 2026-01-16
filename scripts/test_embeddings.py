#!/usr/bin/env python3
"""Test embeddings model loading

This script tests if the embeddings model can load successfully.

Usage:
    python scripts/test_embeddings.py
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

print("=" * 80)
print("Testing Embeddings Model Loading")
print("=" * 80)
print()

try:
    print("1. Loading settings...")
    from app.core.config import settings
    print(f"   ✓ Model: {settings.embeddings_model}")
    print(f"   ✓ Provider: {settings.embeddings_provider}")
    print()

    print("2. Loading embeddings service...")
    from app.services.embeddings import get_embeddings_service

    embeddings_service = get_embeddings_service()
    print(f"   ✓ Service created")
    print()

    print("3. Testing embedding generation...")
    test_text = "python developer with 5 years experience"
    embedding = embeddings_service.embed_single(test_text, "staffing")
    print(f"   ✓ Generated embedding")
    print(f"   ✓ Dimension: {len(embedding)}")
    print(f"   ✓ First 5 values: {embedding[:5]}")
    print()

    print("=" * 80)
    print("✅ SUCCESS! Embeddings model is working correctly.")
    print("=" * 80)
    sys.exit(0)

except Exception as e:
    print()
    print("=" * 80)
    print("❌ ERROR! Embeddings model failed to load.")
    print("=" * 80)
    print()
    print(f"Error: {e}")
    print()
    print("Full traceback:")
    import traceback
    traceback.print_exc()
    print()
    sys.exit(1)
