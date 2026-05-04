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
            SELECT a.assignment_id, a.advisor_id, a.std_id as student_id,
                   a.assigned_at, a.is_primary, a.notes,
                   s.std_nm as student_name
            FROM tb_advisor_assignment a
            JOIN tb_student s ON a.std_id = s.std_id
            WHERE a.advisor_id = $1
            ORDER BY s.std_nm
            LIMIT 5
        """
        result = await execute_query(query, "0a014940-0776-4de8-88fd-3536f792ea80")
        print(f"Query result count: {len(result)}")
        if result:
            print(f"First row: {result[0]}")
    except Exception as e:
        import traceback
        print(f"Error: {type(e).__name__}: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
