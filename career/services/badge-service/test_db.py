import asyncio
from app.config import get_settings
from app.database import execute_query, init_db

async def test():
    settings = get_settings()
    print(f"DB Config: host={settings.DB_HOST}, password={settings.DB_PASSWORD}, schema={settings.DB_SCHEMA}")

    try:
        await init_db()
        print("DB Init OK")

        query = """
            SELECT badge_id, badge_cd, badge_nm, description, category, level,
                   icon_url, criteria, points, related_skill_cd, is_active, created_at
            FROM tb_badge WHERE is_active = $1
            ORDER BY level DESC, points DESC
        """
        result = await execute_query(query, True)
        print(f"Query result count: {len(result)}")
        if result:
            print(f"First row: {result[0]}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test())
