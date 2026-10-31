"""Manual smoke checks against a running ClauseDesk API."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_get_contracts():
    """GET `/contracts/` and print a short sample of the response."""
    print("📡 Fetching contracts from API...")
    async with httpx.AsyncClient() as client:
        # GET রিকোয়েস্ট পাঠানো হচ্ছে
        response = await client.get(f"{BASE_URL}/contracts/")
        
        # স্ট্যাটাস কোড চেক (Swift-এর response.statusCode এর মতো)
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            contracts = response.json()
            print(f"📦 Found {len(contracts)} contracts.")
            # প্রথম ৩টি কন্ট্রাক্টের নাম প্রিন্ট করা হচ্ছে
            for c in contracts[:3]:
                print(f"   - ID: {c['id']}, Filename: {c['filename']}")

async def test_post_contract():
    """POST a sample contract as form data to `/contracts/`."""
    print("\n📤 Sending new contract to API...")
    # Form ডেটা তৈরি (JSON নয়, কারণ আমরা Form(...) ব্যবহার করেছি)
    payload = {
        "filename": "python_script_test.txt",
        "raw_text": "This contract was uploaded via a Python script."
    }
    
    async with httpx.AsyncClient() as client:
        # POST রিকোয়েস্ট পাঠানো হচ্ছে (data= ব্যবহার করা হয় Form ডেটার জন্য)
        response = await client.post(f"{BASE_URL}/contracts/", data=payload)
        
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 201:
            new_contract = response.json()
            print("🎉 Successfully created new contract:")
            print(f"   - New ID: {new_contract['id']}")
            print(f"   - Status: {new_contract['status']}")

async def main():
    """Run GET then POST smoke checks against localhost."""
    # একটার পর একটা ফাংশন রান করা হচ্ছে
    await test_get_contracts()
    await test_post_contract()

if __name__ == "__main__":
    # Async মেইন ফাংশন রান
    asyncio.run(main())
