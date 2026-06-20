import subprocess

def execute_code(code: str) -> dict:
    try:
        result = subprocess.run(['python', '-c', code], 
        capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        return {"output": "", "error": "Code execution timed out after 10 seconds"}
    out = {"output": result.stdout, "error": result.stderr}
    return out