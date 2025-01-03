from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI()

# Allow all origins for simplicity (adjust as needed for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/generate")
async def generate(
    service_llm_provider: str = Query(...),
    service_llm_model: str = Query(...),
    max_tokens: int = Query(...),
    temperature: float = Query(...),
    repo_url: str = Query(...),
    prompt: str = Query(...),
    timestamp: int = Query(...),
):
    """
    Simulates graph generation based on provided parameters.

    For demonstration, it returns a simple HTML response after a delay.
    In a real application, you would use these parameters to interact with
    your graph generation logic and an LLM.
    """
    print(f"Received request with parameters: {service_llm_provider=}, {service_llm_model=}, {max_tokens=}, {temperature=}, {repo_url=}, {prompt=}, {timestamp=}")

    # Simulate processing time (replace with actual graph generation logic)
    time.sleep(2)

    # Placeholder for a generated HTML graph (replace with your actual output)
    html_content = f"""
    <html>
    <head><title>Generated Graph</title></head>
    <body>
        <h1>Graph generated for {repo_url}</h1>
        <p>Prompt: {prompt}</p>
        <p>LLM Provider: {service_llm_provider}</p>
        <p>LLM Model: {service_llm_model}</p>
        <p>Max Tokens: {max_tokens}</p>
        <p>Temperature: {temperature}</p>
        <p>Timestamp: {timestamp}</p>
        <p> This is a placeholder for a graph. Imagine a beautiful graph here! </p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)