import subprocess

print("Starting backend server...")
try:
    subprocess.run(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"], check=True)
except FileNotFoundError:
    print("Error: 'uvicorn' command not found")
