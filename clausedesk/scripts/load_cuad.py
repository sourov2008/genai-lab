"""Load unique CUAD contracts and seed the local database."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
import json
import urllib.request
import logging

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models import Contract, User
from app.models.contract import ContractStatus

logger = logging.getLogger(__name__)

_SEED_EMAIL = "seed@clausedesk.local"
_SEED_PASSWORD_HASH = "!seed-not-loginable"
_CUAD_JSON_URL = "https://huggingface.co/datasets/theatticusproject/cuad/resolve/main/CUAD_v1/CUAD_v1.json"


def load_unique_contracts(limit: int = 50) -> list[dict[str, str]]:
    """Download CUAD JSON and return unique contracts by title.

    Keeps the longest combined paragraph text for each title.

    Args:
        limit: Maximum number of unique contracts to return.

    Returns:
        Dicts with keys `name` and `raw_text`. Empty list on download failure.
    """
    print("⏳ Downloading CUAD dataset (this may take a minute)...")
    
    unique: dict[str, dict[str, str]] = {}
    
    try:
        # সরাসরি JSON ডাউনলোড করা হচ্ছে (HuggingFace datasets এর ঝামেলা এড়াতে)
        with urllib.request.urlopen(_CUAD_JSON_URL) as response:
            raw_data = response.read().decode("utf-8")
            data = json.loads(raw_data)
    except Exception as e:
        print(f"❌ Failed to download dataset: {e}")
        return []

    print("✅ Download complete. Parsing contracts...")

    # SQuAD ফরম্যাট পার্স করা
    for item in data.get("data", []):
        title = item.get("title", "unknown_contract")
        paragraphs = item.get("paragraphs", [])
        
        # একটি কন্ট্রাক্টের সব প্যারাগ্রাফ মিলিয়ে পুরো টেক্সট বানানো
        full_text = "\n\n".join(p.get("context", "") for p in paragraphs)
        
        if not full_text.strip():
            continue
            
        existing = unique.get(title)
        if existing is not None:
            if len(full_text) > len(existing["raw_text"]):
                existing["raw_text"] = full_text
            continue
            
        if len(unique) >= limit:
            break
            
        unique[title] = {"name": title, "raw_text": full_text}
        
    return list(unique.values())


async def seed_database(contracts: list[dict[str, str]]) -> None:
    """Insert missing seed-user contracts into the database.

    Args:
        contracts: Unique contract dicts from `load_unique_contracts`.
    """
    settings = get_settings()
    async with get_session_factory()() as session:
        result = await session.execute(select(User).where(User.email == _SEED_EMAIL))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(email=_SEED_EMAIL, password_hash=_SEED_PASSWORD_HASH)
            session.add(user)
            await session.flush()

        created = 0
        for contract in contracts:
            filename = f"{contract['name']}.txt"
            existing = await session.execute(
                select(Contract).where(
                    Contract.filename == filename,
                    Contract.user_id == user.id,
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue
            session.add(
                Contract(
                    user_id=user.id,
                    filename=filename,
                    raw_text=contract["raw_text"],
                    status=ContractStatus.READY.value,
                )
            )
            created += 1

        await session.commit()
        print(f"🎉 Database seeded! Created {created} new contracts.")


async def main() -> None:
    """Load CUAD contracts and seed the database."""
    contracts = load_unique_contracts(limit=50)
    print(f"📄 Loaded {len(contracts)} unique contracts from CUAD.")
    await seed_database(contracts)
    print("✅ Seeding complete.")


if __name__ == "__main__":
    asyncio.run(main())
