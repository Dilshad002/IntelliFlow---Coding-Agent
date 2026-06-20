from fastapi import FastAPI
from pydantic import BaseModel
from agent import app as agent_app

app = FastAPI()

class RunRequest(BaseModel):
    user_prompt: str

@app.post('/run')
def run(request: RunRequest):
    result = agent_app.invoke({
        "user_prompt": request.user_prompt,
        "code": "",
        "output": "",
        "error": "",
        "attempts": 0,
        "success": False,
        "trace": []
    })
    out = {"code": result["code"], 
            "output": result["output"], 
            "error": result["error"], 
            "attempts": result["attempts"], 
            "success": result["success"],
            "trace": result["trace"]
            }
    return out
