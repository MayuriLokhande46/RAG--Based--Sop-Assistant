#!/usr/bin/env python3
"""
Test script for DocuMind RAG Assistant - Multi-user Document Management
Tests the new document management APIs and mobile responsive features
"""

import requests
import json
import time
import os
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_document_management():
    """Test the new document management features"""
    print("🧪 Testing DocuMind Document Management APIs...")

    # Test data
    test_user = {
        "username": "testuser",  # Simple username with only letters
        "password": "TestPass123!"
    }

    # Create test user
    print("\n1. Creating test user...")
    try:
        response = requests.post(f"{BASE_URL}/signup", json=test_user)
        if response.status_code == 200:
            print("✅ User registration successful")
        else:
            print(f"⚠️  User registration failed (might already exist): {response.text}")
    except Exception as e:
        print(f"❌ User registration error: {e}")

    # Login to get token (try anyway)
    print("\n2. Logging in...")
    try:
        response = requests.post(f"{BASE_URL}/login", data=test_user)  # Use form data, not JSON
        if response.status_code == 200:
            token = response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return

    # Test document list (should be empty initially)
    print("\n3. Testing document list (should be empty)...")
    try:
        response = requests.get(f"{BASE_URL}/documents", headers=headers)
        if response.status_code == 200:
            docs = response.json()
            print(f"✅ Document list retrieved: {len(docs)} documents")
        else:
            print(f"❌ Document list failed: {response.text}")
    except Exception as e:
        print(f"❌ Document list error: {e}")

    # Create a test file for upload
    print("\n4. Creating test document...")
    test_file_path = Path("test_document.txt")
    test_content = "This is a test document for the DocuMind RAG Assistant.\nIt contains some sample text to test the document upload and processing functionality."

    try:
        with open(test_file_path, "w") as f:
            f.write(test_content)
        print("✅ Test document created")
    except Exception as e:
        print(f"❌ Failed to create test document: {e}")
        return

    # Upload document
    print("\n5. Uploading test document...")
    try:
        with open(test_file_path, "rb") as f:
            files = {"file": ("test_document.txt", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/ingest", files=files, headers=headers)

        if response.status_code == 200:
            result = response.json()
            print("✅ Document upload successful")
            print(f"   Response: {result}")
        else:
            print(f"❌ Document upload failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Document upload error: {e}")

    # Wait a moment for processing
    time.sleep(2)

    # Test document list again (should have 1 document)
    print("\n6. Testing document list after upload...")
    try:
        response = requests.get(f"{BASE_URL}/documents", headers=headers)
        if response.status_code == 200:
            docs = response.json()
            print(f"✅ Document list retrieved: {len(docs)} documents")
            if docs:
                doc = docs[0]
                print(f"   Document: {doc.get('filename')} ({doc.get('file_size')} bytes)")
                doc_id = doc.get('id')
            else:
                doc_id = None
        else:
            print(f"❌ Document list failed: {response.text}")
            doc_id = None
    except Exception as e:
        print(f"❌ Document list error: {e}")
        doc_id = None

    # Test document deletion if we have a document
    if doc_id:
        print(f"\n7. Testing document deletion (ID: {doc_id})...")
        try:
            response = requests.delete(f"{BASE_URL}/documents/{doc_id}", headers=headers)
            if response.status_code == 200:
                print("✅ Document deletion successful")
            else:
                print(f"❌ Document deletion failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Document deletion error: {e}")

        # Test document list after deletion (should be empty)
        print("\n8. Testing document list after deletion...")
        try:
            response = requests.get(f"{BASE_URL}/documents", headers=headers)
            if response.status_code == 200:
                docs = response.json()
                print(f"✅ Document list retrieved: {len(docs)} documents (should be 0)")
            else:
                print(f"❌ Document list failed: {response.text}")
        except Exception as e:
            print(f"❌ Document list error: {e}")

    # Clean up test file
    try:
        if test_file_path.exists():
            test_file_path.unlink()
        print("✅ Test file cleaned up")
    except Exception as e:
        print(f"⚠️  Failed to clean up test file: {e}")

    print("\n🎉 Document Management API Testing Complete!")

def test_mobile_responsive():
    """Test mobile responsive features by checking CSS"""
    print("\n📱 Testing Mobile Responsive Features...")

    css_path = Path("static/style.css")
    if css_path.exists():
        with open(css_path, "r") as f:
            css_content = f.read()

        # Check for mobile responsive features
        mobile_features = [
            "@media (max-width: 850px)",
            "@media (max-width: 480px)",
            "flex-direction: column",
            "display: none",
            "margin-left: 0",
            "prefers-reduced-motion",
            "prefers-contrast: high"
        ]

        found_features = []
        for feature in mobile_features:
            if feature in css_content:
                found_features.append(feature)

        if len(found_features) >= 6:
            print("✅ Mobile responsive CSS features detected:")
            for feature in found_features:
                print(f"   ✓ {feature}")
        else:
            print(f"⚠️  Only {len(found_features)} mobile features found")
    else:
        print("❌ CSS file not found")

    print("🎉 Mobile Responsive Testing Complete!")

if __name__ == "__main__":
    print("🚀 DocuMind RAG Assistant - Feature Testing Suite")
    print("=" * 60)

    # Test document management APIs
    test_document_management()

    # Test mobile responsive features
    test_mobile_responsive()

    print("\n" + "=" * 60)
    print("✨ All tests completed! Check the results above.")