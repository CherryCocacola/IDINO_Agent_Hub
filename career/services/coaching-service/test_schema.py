import asyncio
from app.database import execute_query, init_db
from app.schemas.coaching import GoalResponse

async def test():
    await init_db()
    print("DB Init OK")

    query = """
        SELECT
            g.goal_id, g.std_id as student_id, g.title, g.description,
            g.goal_type, g.priority, g.status, g.progress_percentage,
            g.target_date, g.target_role_cd, g.related_skills,
            g.success_criteria, g.motivation,
            g.created_at, g.updated_at, g.completed_at,
            COALESCE(p.plan_count, 0) as plan_items_count,
            COALESCE(p.completed_count, 0) as completed_items_count,
            COALESCE(c.checkin_count, 0) as checkin_count,
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
        ORDER BY g.created_at DESC
    """
    result = await execute_query(query, "2020020025")
    print(f"Query result count: {len(result)}")

    if result:
        row = result[0]
        print(f"Row keys: {row.keys()}")
        print(f"Row data: {row}")

        try:
            # Convert Decimal to float for progress_percentage
            if row.get('progress_percentage'):
                row['progress_percentage'] = float(row['progress_percentage'])

            response = GoalResponse(**row)
            print(f"GoalResponse created successfully: {response.goal_id}")
        except Exception as e:
            import traceback
            print(f"Schema validation error: {type(e).__name__}: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
