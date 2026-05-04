import subprocess
import time
import os

# Find and kill process on port 8009
result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if ':8009' in line and 'LISTENING' in line:
        parts = line.split()
        pid = parts[-1]
        print(f"Killing process {pid} on port 8009")
        subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)

time.sleep(2)

# Start coaching service
print("Starting coaching service on port 8009...")
os.chdir(r'E:\workspace\idino_career\services\coaching-service')
subprocess.Popen(['python', '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8009'])
print("Service started!")
