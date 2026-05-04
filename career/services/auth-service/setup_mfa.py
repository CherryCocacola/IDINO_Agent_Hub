"""Setup MFA for test user."""
import asyncio
import asyncpg
import pyotp


async def update_mfa():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='2012',
        database='postgres'
    )

    # Check current users
    users = await conn.fetch(
        'SELECT user_id, login_id, email, mfa_enabled, totp_secret, totp_verified '
        'FROM idino_career.tb_user LIMIT 5'
    )
    print('Current users:')
    for u in users:
        print(f"  {u['login_id']}: mfa_enabled={u['mfa_enabled']}, totp_verified={u['totp_verified']}")

    # Generate TOTP secret for test user
    secret = pyotp.random_base32()
    print(f'\nGenerated TOTP secret: {secret}')

    # Update first user with MFA enabled
    if users:
        user_id = users[0]['user_id']
        await conn.execute('''
            UPDATE idino_career.tb_user
            SET mfa_enabled = true,
                totp_secret = $1,
                totp_verified = true,
                upd_dt = NOW()
            WHERE user_id = $2
        ''', secret, user_id)
        print(f"Updated user {users[0]['login_id']} with MFA enabled")

        # Show TOTP code for testing
        totp = pyotp.TOTP(secret)
        print(f'Current TOTP code: {totp.now()}')
        print(f'\nTo test, use this code within 30 seconds: {totp.now()}')
        print(f'Or scan this URI in authenticator app:')
        print(f'  {totp.provisioning_uri(users[0]["login_id"], issuer_name="IDINO Career")}')

    await conn.close()


if __name__ == '__main__':
    asyncio.run(update_mfa())
