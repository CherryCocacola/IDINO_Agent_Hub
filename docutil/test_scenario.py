import urllib.request, json, os, io, mimetypes

BASE = 'http://localhost:8040/api/v1'
ORG_ID = '00000000-0000-4000-a000-000000000001'

DEPT_CEO    = 'fa312738-88dd-48eb-8652-e74aa975b6e3'
DEPT_FUTURE = '724b95ad-9c7e-45cb-857d-91570b39fcb8'
DEPT_AI     = '6534247e-c550-4f35-8686-6ea8f92e0239'

def api(method, path, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f'{BASE}{path}', data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        if resp.status == 204:
            return {'status': 204}
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {'error': e.code, 'detail': e.read().decode()[:500]}

def upload_file(filepath, token, visibility='public', department_id=None):
    boundary = '----FormBoundary7MA4YWxkTrZu0gW'
    filename = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        file_data = f.read()

    body = io.BytesIO()
    body.write(f'--{boundary}\r\n'.encode())
    body.write(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    ct = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    body.write(f'Content-Type: {ct}\r\n\r\n'.encode())
    body.write(file_data)
    body.write(f'\r\n--{boundary}--\r\n'.encode())

    url = f'{BASE}/documents/upload?visibility={visibility}'
    if department_id:
        url += f'&department_id={department_id}'

    req = urllib.request.Request(url, data=body.getvalue(), method='POST')
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {'error': e.code, 'detail': e.read().decode()[:500]}

def login(username, password):
    r = api('POST', '/auth/login', {'username': username, 'password': password})
    if 'error' in r:
        return None, r
    return r['access_token'], r

# ============================================================
admin_token, _ = login('admin', 'admin123!')
print('Admin login OK')

# STEP 1
print('\n=== STEP 1: Create user dongun (CEO dept) ===')
r = api('POST', '/users', {
    'username': 'dongun',
    'email': 'dongun@idino.co.kr',
    'password': 'idino!@#$',
    'role': 'member',
    'organization_id': ORG_ID,
    'department_id': DEPT_CEO,
}, admin_token)
print(f'  Result: {r.get("username") or str(r.get("detail",""))[:100]}')

# STEP 2
print('\n=== STEP 2: Login as dongun, upload 2 PDFs (public) ===')
dongun_token, lr = login('dongun', 'idino!@#$')
if not dongun_token:
    print(f'  Login FAIL: {lr}')
else:
    print('  Login OK')
    files = [
        r'C:\Users\IDINO_USER\Downloads\품의서(내부 20241018-01)_(주)아이디노 조직개편의 건.pdf',
        r'C:\Users\IDINO_USER\Downloads\품의서(내부 20241018-02)_인사발령.pdf',
    ]
    doc_ids = []
    for fpath in files:
        fname = os.path.basename(fpath)
        r = upload_file(fpath, dongun_token, visibility='public', department_id=DEPT_CEO)
        if 'error' in r:
            print(f'  Upload FAIL [{fname[:30]}]: {r["detail"][:200]}')
        else:
            doc_ids.append(r['id'])
            print(f'  Upload OK [{fname[:30]}]: id={r["id"][:8]}... vis={r.get("visibility")}')
    print(f'  Doc IDs: {doc_ids}')

# STEP 4
print('\n=== STEP 4: Create user yhkim (Future Lab dept) ===')
r = api('POST', '/users', {
    'username': 'yhkim',
    'email': 'yhkim@idino.co.kr',
    'password': 'idino!@#$',
    'role': 'member',
    'organization_id': ORG_ID,
    'department_id': DEPT_FUTURE,
}, admin_token)
print(f'  Result: {r.get("username") or str(r.get("detail",""))[:100]}')

# STEP 5
print('\n=== STEP 5: Login as yhkim, create chat session ===')
yhkim_token, lr = login('yhkim', 'idino!@#$')
if not yhkim_token:
    print(f'  Login FAIL: {lr}')
else:
    print('  Login OK')
    session_data = {'title': 'Document Q&A', 'scoped_document_ids': doc_ids if doc_ids else None}
    r = api('POST', '/chat/sessions', session_data, yhkim_token)
    if 'error' in r:
        print(f'  Session FAIL: {r}')
        sid = None
    else:
        sid = r['id']
        print(f'  Session: {sid[:8]}...')

    if sid:
        r = api('POST', f'/chat/sessions/{sid}/messages',
                {'content': 'Upload documents summary please'}, yhkim_token)
        if 'error' in r:
            print(f'  Chat FAIL: {r["detail"][:300]}')
        else:
            msg = r.get('message', {})
            print(f'  Chat OK (model={msg.get("model_used")}): {msg.get("content","")[:200]}')

# STEP 6
print('\n=== STEP 6: yhkim uploads hwpx (department_only) ===')
if yhkim_token:
    hwpx_path = r'C:\Users\IDINO_USER\Downloads\[붙임2-10] 부산지역 중소기업유망기술개발(소부장) 세부 지원내용1.hwpx'
    r = upload_file(hwpx_path, yhkim_token, visibility='department_only', department_id=DEPT_FUTURE)
    if 'error' in r:
        print(f'  Upload FAIL: {r["detail"][:300]}')
        hwpx_id = None
    else:
        hwpx_id = r['id']
        print(f'  Upload OK: id={r["id"][:8]}... vis={r.get("visibility")}')
else:
    hwpx_id = None

# STEP 7
print('\n=== STEP 7: Create user hslee (AI Team dept) ===')
r = api('POST', '/users', {
    'username': 'hslee',
    'email': 'hslee@idino.co.kr',
    'password': 'idino!@#$',
    'role': 'member',
    'organization_id': ORG_ID,
    'department_id': DEPT_AI,
}, admin_token)
print(f'  Result: {r.get("username") or str(r.get("detail",""))[:100]}')

# STEP 8
print('\n=== STEP 8: Login as hslee, test document access & chat ===')
hslee_token, lr = login('hslee', 'idino!@#$')
if not hslee_token:
    print(f'  Login FAIL: {lr}')
else:
    print('  Login OK')

    if hwpx_id:
        r = api('GET', f'/documents/{hwpx_id}', token=hslee_token)
        if 'error' in r:
            print(f'  Doc access: DENIED ({r["error"]})')
        else:
            print(f'  Doc access: OK - {r.get("name","?")} (vis={r.get("visibility")})')

    r = api('GET', '/documents?page=1&size=50', token=hslee_token)
    if 'error' not in r:
        print(f'  Visible docs: {r.get("total", len(r.get("items",[])))}')
        for d in r.get('items', []):
            print(f'    - {d.get("name","?")[:40]} (vis={d.get("visibility","?")})')

    if hwpx_id:
        r = api('POST', '/chat/sessions',
                {'title': 'HWPX Q&A', 'scoped_document_ids': [hwpx_id]}, hslee_token)
        if 'error' in r:
            print(f'  Session FAIL: {r}')
            sid2 = None
        else:
            sid2 = r['id']
            print(f'  Session: {sid2[:8]}...')

        if sid2:
            r = api('POST', f'/chat/sessions/{sid2}/messages',
                    {'content': 'Summarize the document'}, hslee_token)
            if 'error' in r:
                print(f'  Chat FAIL: {r["detail"][:300]}')
            else:
                msg = r.get('message', {})
                print(f'  Chat OK (model={msg.get("model_used")}): {msg.get("content","")[:200]}')

print('\n========== ALL STEPS COMPLETE ==========')
