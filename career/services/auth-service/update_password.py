"""Update password hash for test user."""
import asyncio
import asyncpg
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


async def update_password():
    # Generate bcrypt hash for '1234'
    password_hash = pwd_context.hash('1234')
    print(f'Generated hash: {password_hash[:30]}...')

    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='2012',
        database='postgres'
    )

    # Update password for test users
    result = await conn.execute(
        'UPDATE idino_career.tb_user SET password_hash = $1 WHERE login_id = $2',
        password_hash,
        '2021010001'
    )
    print(f'Updated 2021010001: {result}')

    # Also update STU001
    result = await conn.execute(
        'UPDATE idino_career.tb_user SET password_hash = $1 WHERE login_id = $2',
        password_hash,
        'STU001'
    )
    print(f'Updated STU001: {result}')

    await conn.close()
    print('Done!')


if __name__ == '__main__':
    asyncio.run(update_password())
