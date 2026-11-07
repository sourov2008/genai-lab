import asyncio
import sys
from pathlib import Path

# This ensures Python can find the 'app' folder from the scripts directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import get_session_factory
from app.services.agent_tools import get_clause, search_similar_clauses
from app.models import Clause
from sqlalchemy import select

async def test_tools():
    async with get_session_factory()() as db:
        # ১. ডেটাবেস থেকে যেকোনো একটি ক্লজ খুঁজে বের করা
        result = await db.execute(select(Clause).limit(1))
        existing_clause = result.scalar_one_or_none()

        if not existing_clause:
            print("❌ ডেটাবেসে কোনো ক্লজ নেই! আগে Swagger থেকে ডেটা এক্সট্রাক্ট করুন।")
            return

        print(f"✅ টেস্টের জন্য পাওয়া গেল: Contract ID: {existing_clause.contract_id}, Type: {existing_clause.clause_type}")

        # ২. Tool 1: get_clause (ডাইনামিক আইডি দিয়ে)
        res1 = await get_clause(db, contract_id=existing_clause.contract_id, clause_type=existing_clause.clause_type)
        print("\n🎯 Tool 1 (get_clause) Result:\n", res1)
        
        # ৩. Tool 2: search_similar_clauses
        res2 = await search_similar_clauses(db, query="terminate")
        print("\n🎯 Tool 2 (search_similar_clauses) Result:\n", res2)

if __name__ == "__main__":
    asyncio.run(test_tools())