import asyncio
from app.db.session import get_session_factory
from app.llm.factory import make_llm_provider
from app.core.config import get_settings
from app.services.agent_service import run_compliance_check
from app.models import Contract

async def test():
    settings = get_settings()
    llm = make_llm_provider(settings)
    async with get_session_factory()() as db:
        # টেস্টের জন্য একটি কন্ট্র্যাক্ট আইডি দিন (যেটাতে ক্লজ আছে)
        contract = await db.get(Contract, 1) 
        result = await run_compliance_check(db, contract, llm)
        print("\n=== AGENT RESULT ===")
        print(result)

asyncio.run(test())