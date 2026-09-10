from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from typing import Any
from collections import defaultdict, deque
from datetime import datetime, timezone
import hashlib, hmac, html, json, os, time

app = FastAPI(title="FlyRank Embeddable Widget Platform", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

DATA_FILE = os.getenv("DATA_FILE", "data.json")
DB: dict[str, list[dict[str, Any]]] = {"tenants": [], "widgets": [], "submissions": [], "users": []}
LIMITS: dict[str, deque[float]] = defaultdict(deque)

def now(): return datetime.now(timezone.utc).isoformat()

def load():
    global DB
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f: DB.update(json.load(f))
        except (OSError, json.JSONDecodeError): pass

def save():
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(DB, f, indent=2)
    os.replace(tmp, DATA_FILE)

load()

class WidgetIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str = Field(pattern="^(signup|cta|popover)$")
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    form_fields: list[str] = Field(default_factory=lambda: ["name", "email"], max_length=10)
    button_text: str = Field(default="Submit", min_length=1, max_length=40)
    display_options: dict[str, Any] = Field(default_factory=dict)
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])

class Widget(WidgetIn):
    id: str
    tenant_id: str
    version: int = 1
    created_at: str
    updated_at: str

class Submission(BaseModel):
    widget_id: str
    data: dict[str, Any] = Field(default_factory=dict)
    website_origin: str | None = None
    hp: str = Field(default="", max_length=200)

class Login(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=80)
    token: str = Field(min_length=1, max_length=200)

def auth_tenant(request: Request) -> str:
    token = request.headers.get("Authorization", "")
    if not token.startswith("Bearer "): raise HTTPException(401, "Valid bearer token required")
    raw = token[7:]
    for u in DB["users"]:
        if hmac.compare_digest(u["token"], raw): return u["tenant_id"]
    raise HTTPException(401, "Invalid bearer token")

def widget_for(tenant: str, wid: str):
    for w in DB["widgets"]:
        if w["id"] == wid and w["tenant_id"] == tenant: return w
    raise HTTPException(404, "Widget not found")

def public_widget(wid: str):
    for w in DB["widgets"]:
        if w["id"] == wid: return w
    raise HTTPException(404, "Widget not found")

def rate_ok(ip: str, wid: str, limit=20, window=60):
    key=f"{ip}:{wid}"; q=LIMITS[key]; cutoff=time.time()-window
    while q and q[0] < cutoff: q.popleft()
    if len(q) >= limit: return False
    q.append(time.time()); return True

def geo(ip: str):
    if os.getenv("GEO_PROVIDER_A_DOWN") != "1": return {"country":"IN", "city":"Kanpur", "provider":"A"}
    if os.getenv("GEO_PROVIDER_B_DOWN") != "1": return {"country":"IN", "city":"India", "provider":"B"}
    return {"country":None, "city":None, "provider":None}

def side_effect(sub):
    try:
        if os.getenv("SIDE_EFFECT_DOWN") == "1": raise RuntimeError("simulated notification outage")
        print("SIDE_EFFECT", json.dumps({"submission_id": sub["id"], "status":"accepted"}))
    except Exception as exc: print("SIDE_EFFECT_FAILED", str(exc))

@app.get("/")
def root(): return {"service":"flyrank-capstone-widget-platform", "status":"ok"}

@app.post("/auth/login")
def login(body: Login):
    for u in DB["users"]:
        if u["tenant_id"] == body.tenant_id and hmac.compare_digest(u["token"], body.token): return {"access_token": body.token, "token_type":"bearer", "tenant_id":body.tenant_id}
    raise HTTPException(401, "Invalid credentials")

@app.post("/widgets", response_model=Widget, status_code=201)
def create_widget(body: WidgetIn, request: Request):
    tenant=auth_tenant(request); wid=hashlib.sha256(f"{tenant}:{time.time_ns()}".encode()).hexdigest()[:12]
    w=Widget(id=wid, tenant_id=tenant, created_at=now(), updated_at=now(), **body.model_dump()).model_dump()
    DB["widgets"].append(w); save(); return w

@app.get("/widgets", response_model=list[Widget])
def list_widgets(request: Request):
    tenant=auth_tenant(request); return [w for w in DB["widgets"] if w["tenant_id"]==tenant]

@app.get("/widgets/{wid}", response_model=Widget)
def get_widget(wid: str, request: Request): return widget_for(auth_tenant(request), wid)

@app.put("/widgets/{wid}", response_model=Widget)
def update_widget(wid: str, body: WidgetIn, request: Request):
    w=widget_for(auth_tenant(request), wid); w.update(body.model_dump(), version=w["version"]+1, updated_at=now()); save(); return w

@app.delete("/widgets/{wid}")
def delete_widget(wid: str, request: Request):
    tenant=auth_tenant(request); widget_for(tenant,wid); DB["widgets"]=[w for w in DB["widgets"] if not (w["id"]==wid and w["tenant_id"]==tenant)]; save(); return {"deleted":True}

@app.get("/widgets/{wid}/embed")
def embed(wid: str, request: Request):
    w=widget_for(auth_tenant(request),wid)
    return {"snippet":f'<script src="{request.base_url}widget.v{w["version"]}.js?id={html.escape(wid)}"></script>', "version":w["version"]}

@app.get("/widgets/{wid}/config")
def config(wid: str, response: Response):
    w=public_widget(wid); response.headers["Cache-Control"]="public, max-age=60"; response.headers["ETag"]=f'W/{w["id"]}-{w["version"]}'
    return {k:w[k] for k in ("id","type","title","description","form_fields","button_text","display_options","version","allowed_origins")}

@app.get("/widget.v{version}.js")
def widget_js(version: int, id: str, response: Response):
    w=public_widget(id)
    if w["version"] != version: raise HTTPException(404,"Bundle version not found")
    return Response(open("static/widget.js",encoding="utf-8").read(), media_type="application/javascript", headers={"Cache-Control":"public, max-age=31536000, immutable"})

@app.options("/submissions")
def submission_preflight(): return Response(status_code=204)

@app.post("/submissions", status_code=201)
def submit(body: Submission, request: Request):
    if len(json.dumps(body.model_dump())) > 10000: raise HTTPException(413,"Payload too large")
    w=public_widget(body.widget_id); origin=body.website_origin or request.headers.get("origin"); allowed=w["allowed_origins"]
    if allowed != ["*"] and origin not in allowed: raise HTTPException(403,"Origin not allowed")
    if not rate_ok(request.client.host if request.client else "unknown", body.widget_id): raise HTTPException(429,"Rate limit exceeded")
    if body.hp.strip(): raise HTTPException(400,"Spam rejected")
    for field in w["form_fields"]:
        value=body.data.get(field)
        if value is None or (isinstance(value,str) and not value.strip()): raise HTTPException(422,f"Missing field: {field}")
    s={"id":hashlib.sha256(f"{body.widget_id}:{time.time_ns()}".encode()).hexdigest()[:16],"widget_id":body.widget_id,"data":body.data,"origin":origin,"geo":geo(request.client.host if request.client else "0.0.0.0"),"created_at":now()}
    DB["submissions"].append(s); save(); side_effect(s); return {"accepted":True,"submission_id":s["id"]}

@app.get("/dashboard/stats")
def stats(request: Request):
    tenant=auth_tenant(request); widgets=[w for w in DB["widgets"] if w["tenant_id"]==tenant]; ids={w["id"] for w in widgets}; rows=[s for s in DB["submissions"] if s["widget_id"] in ids]
    by_widget={w["id"]:sum(s["widget_id"]==w["id"] for s in rows) for w in widgets}; by_geo=defaultdict(int)
    for s in rows: by_geo[s["geo"].get("country") or "unknown"]+=1
    return {"total_submissions":len(rows),"widgets":len(widgets),"per_widget":by_widget,"geo_breakdown":dict(by_geo)}

@app.get("/dashboard/submissions")
def dashboard_submissions(request: Request):
    tenant=auth_tenant(request); ids={w["id"] for w in DB["widgets"] if w["tenant_id"]==tenant}; return [s for s in DB["submissions"] if s["widget_id"] in ids]
