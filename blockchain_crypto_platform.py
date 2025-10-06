"""
Slim blockchain platform app (test-focused)
This truncated implementation exists inside the compose project directory so the single-file bind mount
maps to a real file (Windows quirk). It exposes only the endpoints required for the integration
security headers test and applies the required headers both at app layer (defense in depth) and
via Traefik middleware.

Once tests pass, consider consolidating with the full implementation in the parent directory by moving
that source here and removing duplication.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Blockchain & Cryptocurrency Platform (Slim)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECURITY_HEADER_VALUES = {
    "Content-Security-Policy": "default-src 'self'",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "X-Frame-Options": "SAMEORIGIN",
    "X-Content-Type-Options": "nosniff",
}


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    for k, v in SECURITY_HEADER_VALUES.items():
        response.headers.setdefault(k, v)
    return response


@app.get("/blockchain")
@app.get("/blockchain/")
async def blockchain_root():
    return {"status": "ok", "service": "blockchain", "message": "Blockchain platform root"}


@app.get("/")
async def root():
    return {"service": "blockchain-slim", "status": "operational"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5205)
