#!/usr/bin/env python3
"""Clear sentence-transformers model cache

This script clears the cached sentence-transformers models to force re-download.
Useful when model files get corrupted or when there are compatibility issues.

Usage:
    python scripts/clear_model_cache.py [model_name]

Examples:
    python scripts/clear_model_cache.py
    python scripts/clear_model_cache.py BAAI/bge-small-en
"""

import shutil
import sys
from pathlib import Path


def get_cache_dir():
    """Get the sentence-transformers cache directory"""
    # Default cache location
    home = Path.home()
    cache_dir = home / ".cache" / "torch" / "sentence_transformers"

    if not cache_dir.exists():
        # Try alternative location
        cache_dir = home / ".cache" / "huggingface" / "hub"

    return cache_dir


def clear_cache(model_name=None):
    """Clear the model cache"""
    cache_dir = get_cache_dir()

    if not cache_dir.exists():
        print(f"Cache directory not found: {cache_dir}")
        print("No cached models to clear.")
        return 0

    print(f"Cache directory: {cache_dir}")
    print()

    if model_name:
        # Clear specific model
        model_safe_name = model_name.replace("/", "_")
        cleared = False

        for item in cache_dir.iterdir():
            if model_safe_name in item.name:
                print(f"Removing cached model: {item.name}")
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                cleared = True

        if not cleared:
            print(f"No cached files found for model: {model_name}")
            return 1
        else:
            print()
            print(f"✓ Cleared cache for model: {model_name}")
            return 0
    else:
        # Clear all models
        print("WARNING: This will clear ALL cached sentence-transformers models.")
        response = input("Are you sure? (yes/no): ")

        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return 1

        print()
        count = 0
        for item in cache_dir.iterdir():
            print(f"Removing: {item.name}")
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            count += 1

        print()
        print(f"✓ Cleared {count} cached items")
        return 0


def main():
    """Main entry point"""
    model_name = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 80)
    print("Sentence-Transformers Model Cache Cleaner")
    print("=" * 80)
    print()

    try:
        return clear_cache(model_name)
    except Exception as e:
        print()
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
