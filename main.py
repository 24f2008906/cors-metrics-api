import os
import yaml
from dotenv import dotenv_values
from typing import List
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt
from jwt import InvalidTokenError
import uuid
import time

app = FastAPI()

# ============================================
# CONFIGURATION
# ============================================

EMAIL = "24f2008906@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://dash-hairwn.example.com"

ISSUER = "https://idp.exam.local"

AUDIENCE = "tds-duuxuxsv.apps.exam.local"

PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----
"""

# ============================================
# CORS
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# MIDDLEWARE
# ============================================

@app.middleware("http")
async def add_headers(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start

    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{process_time:.6f}"

    return response

# ============================================
# REQUEST MODEL
# ============================================

class TokenRequest(BaseModel):
    token: str

# ============================================
# ASSIGNMENT 1
# GET /stats
# ============================================

@app.get("/stats")
async def stats(values: str = Query(...)):
    nums = [int(x) for x in values.split(",")]

    return {
        "email": EMAIL,
        "count": len(nums),
        "sum": sum(nums),
        "min": min(nums),
        "max": max(nums),
        "mean": sum(nums) / len(nums)
    }

# ============================================
# ASSIGNMENT 2
# POST /verify
# ============================================

@app.post("/verify")
async def verify(request: TokenRequest):
    try:
        payload = jwt.decode(
            request.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE
        )

        return {
            "valid": True,
            "email": payload["email"],
            "sub": payload["sub"],
            "aud": payload["aud"]
        }

    except InvalidTokenError:
        return JSONResponse(
            status_code=401,
            content={
                "valid": False
            }
        )
    # ============================================
# ASSIGNMENT 3
# GET /effective-config
# ============================================

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000"
}

# Simulated OS environment variables from the assignment
os_env = {
    "APP_PORT": "8505",
    "APP_WORKERS": "11",
    "APP_DEBUG": "true",
    "APP_LOG_LEVEL": "warning",
    "APP_API_KEY": "key-svd0yvqhlm",
}


def to_bool(value):
    return str(value).lower() in ("true", "1", "yes", "on")


@app.get("/effective-config")
async def effective_config(set: List[str] = Query(default=[])):

    config = DEFAULTS.copy()

    # YAML layer
    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml") as f:
            config.update(yaml.safe_load(f))

    # .env layer
    env = dotenv_values(".env")

    if "NUM_WORKERS" in env:
        config["workers"] = int(env["NUM_WORKERS"])

    if "APP_LOG_LEVEL" in env:
        config["log_level"] = env["APP_LOG_LEVEL"]

    if "APP_API_KEY" in env:
        config["api_key"] = env["APP_API_KEY"]

    # OS environment layer
    if "APP_PORT" in os.environ:
        config["port"] = int(os.environ["APP_PORT"])

    if "APP_WORKERS" in os.environ:
        config["workers"] = int(os.environ["APP_WORKERS"])

    if "APP_DEBUG" in os.environ:
        config["debug"] = to_bool(os.environ["APP_DEBUG"])

    if "APP_LOG_LEVEL" in os.environ:
        config["log_level"] = os.environ["APP_LOG_LEVEL"]

    if "APP_API_KEY" in os.environ:
        config["api_key"] = os.environ["APP_API_KEY"]

    # CLI overrides
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        if key in ("port", "workers"):
            config[key] = int(value)

        elif key == "debug":
            config[key] = to_bool(value)

        else:
            config[key] = value

    # Secret masking
    config["api_key"] = "****"

    return config
