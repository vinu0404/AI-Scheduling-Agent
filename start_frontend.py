import subprocess

print("Starting frontend application...")
try:
    subprocess.run(["streamlit", "run", "frontend/app.py"], check=True)
except FileNotFoundError:
    print("Error: 'streamlit' command not found")
