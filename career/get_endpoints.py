import requests
import json

try:
    resp = requests.get('http://localhost:8011/openapi.json', timeout=5)
    d = resp.json()
    print("Auth Service Endpoints:")
    print("-" * 50)
    for path, methods in d.get('paths', {}).items():
        for method in methods.keys():
            print(f'{method.upper():8} {path}')
except Exception as e:
    print(f"Error: {e}")
