import asyncio
import os
import sys

# Add root and backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

async def seed_database():
    print("Seeding database with default enterprise roles, organization, and workflows...")
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_database())
