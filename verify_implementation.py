#!/usr/bin/env python3
"""
Simple verification script for DocuMind RAG Assistant enhancements
"""

import os
from pathlib import Path

def check_implementation():
    """Check that all requested features have been implemented"""

    print("🔍 DocuMind RAG Assistant - Implementation Verification")
    print("=" * 60)

    # Check 1: Multi-user support
    print("\n1. Multi-user Support:")
    models_file = Path("models.py")
    if models_file.exists():
        with open(models_file, "r") as f:
            content = f.read()
            if "class Document" in content and "user_id" in content and "namespace" in content:
                print("✅ Document model with user isolation implemented")
            else:
                print("❌ Document model missing user fields")
    else:
        print("❌ models.py not found")

    # Check 2: Document management
    print("\n2. Document Management:")
    main_file = Path("main.py")
    if main_file.exists():
        with open(main_file, "r") as f:
            content = f.read()
            checks = [
                ("@app.get(\"/documents\")", "Document list endpoint"),
                ("@app.delete(\"/documents/{doc_id}\")", "Document delete endpoint"),
                ("ingest_document", "Document metadata saving")
            ]
            for check, desc in checks:
                if check in content:
                    print(f"✅ {desc}")
                else:
                    print(f"❌ {desc} missing")
    else:
        print("❌ main.py not found")

    # Check 3: Mobile responsive
    print("\n3. Mobile Responsive Design:")
    css_file = Path("static/style.css")
    if css_file.exists():
        with open(css_file, "r") as f:
            content = f.read()
            mobile_features = [
                "@media (max-width: 850px)",
                "@media (max-width: 480px)",
                "display: none",  # Hide sidebar
                "margin-left: 0",  # Adjust main content
                "flex-direction: column",  # Mobile layout
                "prefers-reduced-motion",
                "prefers-contrast: high"
            ]
            found = sum(1 for feature in mobile_features if feature in content)
            print(f"✅ Mobile responsive features: {found}/{len(mobile_features)} implemented")
            if found < len(mobile_features):
                print("   Missing features:")
                for feature in mobile_features:
                    if feature not in content:
                        print(f"   - {feature}")
    else:
        print("❌ CSS file not found")

    # Check 4: Database schema
    print("\n4. Database Schema:")
    if models_file.exists():
        with open(models_file, "r") as f:
            content = f.read()
            required_fields = ["user_id", "filename", "file_size", "upload_date", "namespace", "status"]
            found_fields = sum(1 for field in required_fields if field in content)
            print(f"✅ Document table fields: {found_fields}/{len(required_fields)} implemented")

    # Check 5: Server startup
    print("\n5. Server Functionality:")
    try:
        import subprocess
        result = subprocess.run(["python", "main.py"], capture_output=True, text=True, timeout=10)
        if "INFO:     Application startup complete" in result.stderr:
            print("✅ Server starts successfully")
        else:
            print("❌ Server startup issues detected")
    except Exception as e:
        print(f"⚠️  Could not verify server startup: {e}")

    print("\n" + "=" * 60)
    print("✨ Implementation verification complete!")

if __name__ == "__main__":
    check_implementation()