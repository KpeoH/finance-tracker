import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import async_session_maker
from app.services.test_user import TestUserService

"""
Reset and re-seed data for the test user (role='test').

Manual run (from backend/):
    uv run python scripts/reset_test_user.py

Scheduled run:
    Will be triggered daily at 02:00 server time via Ofelia
    (or host cron) once the backend service is added to docker-compose.
"""


async def main() -> None:
    async with async_session_maker() as session:
        user = await TestUserService.reset(session)
        print(f"Test user reset complete: id={user.id}, name={user.name}")


if __name__ == "__main__":
    asyncio.run(main())
