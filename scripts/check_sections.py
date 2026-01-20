#!/usr/bin/env python3
"""Check sections for a specific document/candidate"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.db.session import SessionLocal
from app.models import Candidate, Document, Section, Embedding

def check_document_by_id(doc_id: str):
    """Check sections for a specific document ID"""
    db = SessionLocal()
    try:
        # Find document
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            print(f"❌ Document {doc_id} not found")
            return

        print(f"✅ Found document: {doc.filename} (type: {doc.mime_type})")
        print(f"   SHA256: {doc.sha256}")
        print(f"   Agent: {doc.agent_id}")

        # Check for candidate
        candidate = db.query(Candidate).filter(Candidate.document_id == doc.id).first()
        if candidate:
            print(f"\n✅ Linked candidate:")
            print(f"   ID: {candidate.id}")
            print(f"   Name: {candidate.name}")
            print(f"   Email: {candidate.email}")
            print(f"   Phone: {candidate.phone}")
        else:
            print(f"\n⚠️ No candidate linked to this document")

        # Check sections
        sections = db.query(Section).filter(Section.document_id == doc.id).all()
        print(f"\n📄 Sections: {len(sections)} found")
        for sec in sections:
            text_preview = sec.text[:100] if sec.text else "EMPTY"
            print(f"   - Type: {sec.type:15} | Length: {len(sec.text) if sec.text else 0:6} chars | Preview: {text_preview}...")

        # Check embeddings
        embeddings = db.query(Embedding).filter(Embedding.document_id == doc.id).all()
        print(f"\n🔢 Embeddings: {len(embeddings)} found")
        if embeddings:
            print(f"   Model: {embeddings[0].model}")
            print(f"   Dimension: {embeddings[0].dim}")
            print(f"   Provider: {embeddings[0].agent_id}")

    finally:
        db.close()

def check_candidate_by_id(candidate_id: str):
    """Check sections for a specific candidate ID"""
    db = SessionLocal()
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            print(f"❌ Candidate {candidate_id} not found")
            return

        print(f"✅ Found candidate:")
        print(f"   ID: {candidate.id}")
        print(f"   Name: {candidate.name}")
        print(f"   Email: {candidate.email}")
        print(f"   Phone: {candidate.phone}")
        print(f"   Document ID: {candidate.document_id}")

        check_document_by_id(str(candidate.document_id))

    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_sections.py <document_id_or_candidate_id>")
        print("\nOr to check latest candidate:")
        print("  python check_sections.py --latest")
        sys.exit(1)

    id_arg = sys.argv[1]

    if id_arg == "--latest":
        db = SessionLocal()
        try:
            latest = db.query(Candidate).order_by(Candidate.id.desc()).first()
            if latest:
                print(f"Checking latest candidate: {latest.name}\n")
                check_candidate_by_id(str(latest.id))
            else:
                print("No candidates found")
        finally:
            db.close()
    else:
        # Try as candidate ID first, then document ID
        try:
            check_candidate_by_id(id_arg)
        except:
            check_document_by_id(id_arg)
