"""
Test script for the new transaction extraction features
"""
import requests
import json
import time
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

def test_transaction_extraction():
    """Test the transaction extraction functionality"""
    print("🧪 Testing Transaction Extraction API")
    print("=" * 50)
    
    # Test basic API status
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ API Status: {response.json()['message']}")
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return
    
    # Test getting transactions for a sample statement (should be empty initially)
    sample_statement_id = "test_statement_001"
    
    print(f"\n📋 Testing transactions for statement: {sample_statement_id}")
    try:
        response = requests.get(f"{BASE_URL}/statements/{sample_statement_id}/transactions")
        if response.status_code == 200:
            transactions = response.json()
            print(f"✅ Found {len(transactions)} existing transactions")
            
            # Display transactions if any exist
            if transactions:
                print("\n📊 Existing Transactions:")
                for i, transaction in enumerate(transactions[:5]):  # Show first 5
                    print(f"  {i+1}. {transaction.get('description', 'N/A')} - "
                          f"${transaction.get('amount', 'N/A')} - "
                          f"{transaction.get('transaction_date', 'N/A')}")
                if len(transactions) > 5:
                    print(f"  ... and {len(transactions) - 5} more")
        else:
            print(f"⚠️  No transactions found (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error getting transactions: {e}")
    
    # Test transaction summary
    print(f"\n📈 Testing transaction summary for statement: {sample_statement_id}")
    try:
        response = requests.get(f"{BASE_URL}/statements/{sample_statement_id}/transactions/summary")
        if response.status_code == 200:
            summary = response.json()
            print(f"✅ Transaction Summary:")
            print(f"  📊 Total Transactions: {summary.get('total_transactions', 0)}")
            print(f"  💰 Total Credits: ${summary.get('total_credits', 0):.2f}")
            print(f"  💸 Total Debits: ${summary.get('total_debits', 0):.2f}")
            print(f"  🏦 Net Amount: ${summary.get('net_amount', 0):.2f}")
            
            categories = summary.get('categories', {})
            if categories:
                print(f"  🏷️  Categories: {', '.join(categories.keys())}")
        else:
            print(f"⚠️  Summary not available (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error getting summary: {e}")
    
    # Test all documents endpoint
    print(f"\n📄 Testing documents endpoint")
    try:
        response = requests.get(f"{BASE_URL}/documents/")
        if response.status_code == 200:
            documents = response.json()
            print(f"✅ Found {len(documents)} documents in database")
            
            # Show recent documents
            if documents:
                print("\n📁 Recent Documents:")
                for i, doc in enumerate(documents[:3]):  # Show first 3
                    print(f"  {i+1}. {doc.get('original_filename', 'N/A')} - "
                          f"Statement ID: {doc.get('statement_id', 'N/A')}")
                          
                # Test transaction extraction for first document if available
                if documents:
                    test_doc = documents[0]
                    test_statement_id = test_doc.get('statement_id')
                    if test_statement_id:
                        print(f"\n🔄 Testing manual transaction extraction for: {test_statement_id}")
                        try:
                            response = requests.post(
                                f"{BASE_URL}/statements/{test_statement_id}/extract-transactions"
                            )
                            if response.status_code == 200:
                                result = response.json()
                                print(f"✅ Extraction started: {result.get('message')}")
                                print(f"   Processing time: {result.get('processing_time_seconds', 0):.2f}s")
                            else:
                                print(f"⚠️  Extraction failed (Status: {response.status_code})")
                                print(f"   Error: {response.text}")
                        except Exception as e:
                            print(f"❌ Error starting extraction: {e}")
        else:
            print(f"⚠️  Documents not available (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error getting documents: {e}")
    
    print(f"\n✨ Test completed!")
    print("\n💡 To fully test transaction extraction:")
    print("   1. Upload a PDF statement using: POST /upload-document/")
    print("   2. Wait for text processing to complete")
    print("   3. Check extracted transactions using the endpoints above")
    print("   4. Make sure GROQ_API_KEY is set in your .env file")

def test_api_documentation():
    """Test if API documentation is available"""
    print("\n📚 Testing API Documentation")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ API Documentation available at: http://localhost:8000/docs")
        else:
            print("⚠️  API Documentation not accessible")
    except Exception as e:
        print(f"❌ Error accessing docs: {e}")

if __name__ == "__main__":
    print("🚀 MonitorCredit Transaction Extraction Test")
    print("Make sure the API server is running (python run.py)")
    print()
    
    test_transaction_extraction()
    test_api_documentation()
    
    print("\n🎯 New API Endpoints Added:")
    print("  GET    /statements/{statement_id}/transactions")
    print("  GET    /transactions/{transaction_id}")
    print("  POST   /statements/{statement_id}/extract-transactions")
    print("  DELETE /transactions/{transaction_id}")
    print("  DELETE /statements/{statement_id}/transactions")
    print("  GET    /statements/{statement_id}/transactions/summary")