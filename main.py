import io
import os
from contextlib import asynccontextmanager

import torch
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from PIL import Image

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN", "")
MODEL_PATH = os.getenv("MODEL_PATH", "models/qwen-image-edit")

pipe = None
auth_scheme = HTTPBearer()


def check_token(creds: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    if not API_TOKEN or creds.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipe
    from diffusers import QwenImageEditPlusPipeline

    pipe = QwenImageEditPlusPipeline.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    yield
    del pipe


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/edit")
async def edit(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    num_inference_steps: int = Form(50),
    _: None = Depends(check_token),
):
    raw = await image.read()
    src = Image.open(io.BytesIO(raw)).convert("RGB")

    result = pipe(
        image=src,
        prompt=prompt,
        num_inference_steps=num_inference_steps,
    ).images[0]

    buf = io.BytesIO()
    result.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
