# experiments/01_first_call.py
import asyncio
from pydantic import BaseModel
from src.config import get_settings
from src.llm.base import LLMRequest, Message
from src.llm.factory import make_llm_provider


# ১. ডেটা স্ট্রাকচার (Pydantic Model) ডিফাইন করা
class ClauseSchema(BaseModel):
    clause_type: str
    quote: str
    confidence: float


# ২. টেস্ট করার জন্য প্রম্পট
PROMPT = """Extract the termination clause from this contract excerpt.

Contract:
"Either party may terminate this Agreement upon thirty (30) days 
written notice. Termination for cause is effective immediately."

Return JSON: {"clause_type": str, "quote": str, "confidence": float}
The quote MUST be an exact substring of the contract."""


async def run(provider_name: str):
    # ৩. কোন প্রোভাইডার কল করা হচ্ছে তা টার্মিনালে দেখানোর জন্য (হ্যাং টেস্ট)
    print(f"⏳ Calling {provider_name.upper()}...")
    
    settings = get_settings()
    settings.llm_provider = provider_name
    provider = make_llm_provider(settings)

    req = LLMRequest(
        messages=[Message(role="user", content=PROMPT)],
        temperature=0.0,
        max_tokens=512,
    )
    
    # ৪. try-except ব্লক: যাতে এক প্রোভাইডার ফেইল করলে অন্যটা রান হতে পারে
    try:
        resp = await provider.complete_json(req, ClauseSchema)
        print(f"=== {resp.provider.upper()} ===")
        print(f"model={resp.model}")
        print(f"parsed={resp.parsed}")
        print(f"tokens in/out={resp.usage.input_tokens}/{resp.usage.output_tokens}")
        print(f"latency_ms={resp.latency_ms}")
        print(f"cost_usd={resp.usage.cost_usd:.6f}\n")
    except Exception as e:
        # ৫. এরর আসলে সুন্দরভাবে প্রিন্ট করবে, ক্র্যাশ করবে না
        print(f"❌ {provider_name.upper()} Error: {e}\n")


async def main():
    # ৬. প্রথমে Gemini চেষ্টা করবে, ব্যর্থ হলেও Groq-এ চলে যাবে
    await run("gemini")
    
    print("-" * 40)
    
    # ৭. এরপর Groq চেষ্টা করবে
    await run("groq")


if __name__ == "__main__":
    # ৮. Async মেইন ফাংশন রান করা
    asyncio.run(main())
