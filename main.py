import io
import os
import gc
import torch
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from diffusers import DiffusionPipeline
from transformers import BitsAndBytesConfig
from PIL import Image

app = FastAPI()
security = HTTPBearer()

API_TOKEN = os.environ.get("API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("API_TOKEN environment variable is not set")
MODEL_T2I = os.environ.get("MODEL_T2I", "models/qwen-image-int8")
MODEL_BASE = os.environ.get("MODEL_BASE", "models/qwen-image-base")
MODEL_EDIT = os.environ.get("MODEL_EDIT", "models/qwen-image-edit")

pipe_t2i = None
pipe_edit = None


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")


def unload_all():
    global pipe_t2i, pipe_edit
    if pipe_t2i is not None:
        del pipe_t2i
        pipe_t2i = None
    if pipe_edit is not None:
        del pipe_edit
        pipe_edit = None
    gc.collect()
    torch.cuda.empty_cache()


def load_t2i():
    global pipe_t2i, pipe_edit
    if pipe_t2i is not None:
        return
    if pipe_edit is not None:
        del pipe_edit
        pipe_edit = None
        gc.collect()
        torch.cuda.empty_cache()
    pipe_t2i = DiffusionPipeline.from_pretrained(
        MODEL_BASE,
        torch_dtype=torch.bfloat16,
        load_in_8bit=True,
    )
    pipe_t2i.enable_vae_tiling()


def load_edit():
    global pipe_t2i, pipe_edit
    if pipe_edit is not None:
        return
    if pipe_t2i is not None:
        del pipe_t2i
        pipe_t2i = None
        gc.collect()
        torch.cuda.empty_cache()
    pipe_edit = DiffusionPipeline.from_pretrained(
        MODEL_EDIT, torch_dtype=torch.bfloat16
    ).to("cuda")
    pipe_edit.enable_attention_slicing()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(
    prompt: str = Form(...),
    width: int = Form(1024),
    height: int = Form(1024),
    steps: int = Form(50),
    cfg_scale: float = Form(4.0),
    _=Depends(verify_token),
):
    try:
        load_t2i()
        image = pipe_t2i(
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            true_cfg_scale=cfg_scale,
        ).images[0]
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/edit")
async def edit(
    prompt: str = Form(...),
    image: UploadFile = File(...),
    steps: int = Form(50),
    _=Depends(verify_token),
):
    try:
        load_edit()
        ref = Image.open(io.BytesIO(await image.read())).convert("RGB")
        result = pipe_edit(
            prompt=prompt,
            image=ref,
            num_inference_steps=steps,
        ).images[0]
        buf = io.BytesIO()
        result.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
