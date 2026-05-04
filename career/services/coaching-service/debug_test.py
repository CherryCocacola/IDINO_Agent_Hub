import asyncio
import asyncpg
import traceback

async def test_query():
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            database='postgres',
            user='postgres',
            password='2012'
        )
        await conn.execute('SET search_path TO idino_career, public')

        query = """
            SELECT
                g.goal_id, g.std_id as student_id, g.title, g.description,
                g.goal_type, g.priority, g.status, g.progress_percentage,
                g.target_date, g.target_role_cd, g.related_skills,
                g.success_criteria, g.motivation,
                g.created_at, g.updated_at, g.completed_at,
                COALESCE(p.plan_count, 0) as plan_items_count,
                COALESCE(p.completed_count, 0) as completed_items_count,
                COALESCE(c.checkin_count, 0) as checkins_count,
                c.last_checkin_at
            FROM tb_coaching_goal g
            LEFT JOIN (
                SELECT goal_id,
                       COUNT(*) as plan_count,
                       COUNT(*) FILTER (WHERE is_completed) as completed_count
                FROM tb_coaching_plan
                GROUP BY goal_id
            ) p ON g.goal_id = p.goal_id
            LEFT JOIN (
                SELECT goal_id,
                       COUNT(*) as checkin_count,
                       MAX(created_at) as last_checkin_at
                FROM tb_coaching_checkin
                GROUP BY goal_id
            ) c ON g.goal_id = c.goal_id
            WHERE g.std_id = $1
            ORDER BY
                CASE g.status WHEN 'active' THEN 0 WHEN 'paused' THEN 1 ELSE 2 END,
                CASE g.priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 WHEN 'low' THEN 2 ELSE 1 END,
                g.created_at DESC
        """

        rows = await conn.fetch(query, '2021010001')
        print(f"SUCCESS! Found {len(rows)} rows")
        for row in rows[:2]:
            print(dict(row))
        await conn.close()
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_query())
