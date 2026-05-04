import asyncio
from app.config import get_settings
from app.database import execute_query, init_db

async def test():
    settings = get_settings()
    print(f"DB Config: host={settings.DB_HOST}, password={settings.DB_PASSWORD}, schema={settings.DB_SCHEMA}")

    try:
        await init_db()
        print("DB Init OK")

        # Check table structure
        query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'idino_career' AND table_name = 'tb_coaching_goal'
            ORDER BY ordinal_position
        """
        columns = await execute_query(query)
        print(f"tb_coaching_goal columns: {[c['column_name'] for c in columns]}")

        # Test actual query
        test_query = """
            SELECT goal_id, std_id, title, description, goal_type, status
            FROM tb_coaching_goal WHERE std_id = $1
            LIMIT 5
        """
        result = await execute_query(test_query, "2021010001")
        print(f"Query result count: {len(result)}")
        if result:
            print(f"First row: {result[0]}")
    except Exception as e:
        import traceback
        print(f"Error: {type(e).__name__}: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
