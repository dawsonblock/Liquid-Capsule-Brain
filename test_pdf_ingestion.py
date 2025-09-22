#!/usr/bin/env python3
"""PDF ingestion test for Capsule Brain Supreme AGI system."""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests


def create_test_pdf() -> bytes:
    """Create a simple test PDF for ingestion testing."""
    # This is a minimal valid PDF that should work with pypdf
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 100
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test PDF Document for Capsule Brain) Tj
0 -20 Td
(This is a test document to verify PDF ingestion.) Tj
0 -20 Td
(It contains multiple lines of text.) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
355
%%EOF"""
    return pdf_content


def test_pdf_extraction_local() -> bool:
    """Test PDF extraction locally without server."""
    print("🔍 Testing PDF extraction locally...")
    try:
        from capsule_brain.ingestion.extractor import extract_bytes
        
        pdf_content = create_test_pdf()
        text, meta = extract_bytes("test.pdf", "application/pdf", pdf_content)
        
        print(f"Extracted text: {text[:200]}...")
        print(f"Metadata: {meta}")
        
        if "Test PDF Document" in text and "Capsule Brain" in text:
            print("✅ Local PDF extraction working")
            return True
        else:
            print(f"❌ Local PDF extraction failed. Got: {text[:100]}...")
            return False
            
    except Exception as e:
        print(f"❌ Local PDF extraction failed: {e}")
        return False


async def test_pdf_upload_to_server() -> bool:
    """Test PDF upload to running server."""
    print("🔍 Testing PDF upload to server...")
    
    try:
        # Start server in background
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "capsule_brain.api.server:app", 
            "--host", "127.0.0.1", 
            "--port", "8002",  # Use different port
            "--log-level", "error"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        await asyncio.sleep(3)
        
        # Test PDF upload
        pdf_content = create_test_pdf()
        
        files = {
            'file': ('test.pdf', pdf_content, 'application/pdf')
        }
        data = {
            'q': 'What is this document about?'
        }
        
        try:
            response = requests.post(
                "http://127.0.0.1:8002/ask_with_document",
                files=files,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Upload response: {json.dumps(result, indent=2)[:500]}...")
                
                if result.get('ack') and 'file_processed' in result:
                    print("✅ PDF upload to server successful")
                    success = True
                else:
                    print("❌ PDF upload response invalid")
                    success = False
            else:
                print(f"❌ PDF upload failed: {response.status_code}")
                success = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ PDF upload request failed: {e}")
            success = False
        
        # Clean up
        process.terminate()
        process.wait(timeout=5)
        
        return success
        
    except Exception as e:
        print(f"❌ PDF upload test failed: {e}")
        return False


def test_zip_extraction() -> bool:
    """Test ZIP file extraction."""
    print("🔍 Testing ZIP file extraction...")
    try:
        from capsule_brain.ingestion.extractor import extract_bytes
        import zipfile
        import io
        
        # Create a ZIP file with text content
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.writestr("test1.txt", "This is the first file in the ZIP.")
            zip_file.writestr("test2.txt", "This is the second file in the ZIP.")
            zip_file.writestr("subfolder/test3.txt", "This is in a subfolder.")
        
        zip_content = zip_buffer.getvalue()
        text, meta = extract_bytes("test.zip", "application/zip", zip_content)
        
        print(f"Extracted text: {text[:200]}...")
        print(f"Metadata: {meta}")
        
        if "first file" in text and "second file" in text and "subfolder" in text:
            print("✅ ZIP extraction working")
            return True
        else:
            print(f"❌ ZIP extraction failed. Got: {text[:100]}...")
            return False
            
    except Exception as e:
        print(f"❌ ZIP extraction failed: {e}")
        return False


def main():
    """Run PDF ingestion tests."""
    print("🚀 Starting PDF Ingestion Tests\n")
    
    tests = [
        ("Local PDF Extraction", test_pdf_extraction_local),
        ("ZIP File Extraction", test_zip_extraction),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Run async test
    print(f"\n{'='*50}")
    print("Running: PDF Upload to Server")
    print('='*50)
    try:
        result = asyncio.run(test_pdf_upload_to_server())
        results.append(("PDF Upload to Server", result))
    except Exception as e:
        print(f"❌ PDF Upload to Server crashed: {e}")
        results.append(("PDF Upload to Server", False))
    
    # Summary
    print(f"\n{'='*50}")
    print("PDF INGESTION TEST SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All PDF ingestion tests passed!")
        return 0
    else:
        print("💥 Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
