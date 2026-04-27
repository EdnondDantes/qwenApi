import io
import os
import gc
import torch
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from diffusers import FluxPipeline
from PIL import Image

app = FastAPI()
security = HTTPBearer()

API_TOKEN = os.environ.get("API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("API_TOKEN environment variable is not set")

MODEL_T2I = os.environ.get("MODEL_T2I", "models/flux-schnell")

pipe_t2i = None


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")


def load_t2i():
    global pipe_t2i
    if pipe_t2i is not None:
        return
    pipe_t2i = FluxPipeline.from_pretrained(
        MODEL_T2I, torch_dtype=torch.bfloat16
    ).to("cuda")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(
    prompt: str = Form(...),
    width: int = Form(1024),
    height: int = Form(1024),
    steps: int = Form(4),
    guidance_scale: float = Form(0.0),
    _=Depends(verify_token),
):
    try:
        load_t2i()
        image = pipe_t2i(
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
        ).images[0]
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
