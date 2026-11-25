import os, re, json, hmac, hashlib, secrets, shutil
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Header, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

BASE = Path(__file__).resolve().parent.parent
UPLOADS = BASE / "uploads"
UPLOADS.mkdir(exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./expando.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
SECRET = os.getenv("SECRET_KEY", "dev-only-change-this-secret")
TOKEN_HOURS = 72

app = FastAPI(title="Expando API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=str(BASE / "app" / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS)), name="uploads")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    plan = Column(String(20), default="free", nullable=False)
    subscription_status = Column(String(20), default="free", nullable=False)
    subscription_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String(180), nullable=False)
    product = Column(String(180), default="")
    category = Column(String(80), default="other")
    destination = Column(String(100), default="")
    status = Column(String(30), default="planning")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    invoice = Column(String(40), unique=True, index=True, nullable=False)
    plan = Column(String(20), default="premium")
    period = Column(String(20), default="monthly")
    amount = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    proof_path = Column(String(500), nullable=True)
    admin_note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    score = Column(Integer, nullable=False)
    answers = Column(Text, default="{}")
    recommendations = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)

class CostEstimate(Base):
    __tablename__ = "cost_estimates"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    title = Column(String(180), default="Export cost estimate")
    currency = Column(String(8), default="IDR")
    production = Column(Float, default=0)
    packaging = Column(Float, default=0)
    inland = Column(Float, default=0)
    freight = Column(Float, default=0)
    insurance = Column(Float, default=0)
    customs = Column(Float, default=0)
    other = Column(Float, default=0)
    total = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(220), nullable=False)
    category = Column(String(80), default="Preparation")
    done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    size = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(100), primary_key=True)
    value = Column(Text, default="")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)
    return salt.hex() + "$" + digest.hex()

def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 310000)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception: return False

def make_token(user: User) -> str:
    import base64
    payload = json.dumps({"sub": user.id, "role": user.role, "exp": int((datetime.now(timezone.utc)+timedelta(hours=TOKEN_HOURS)).timestamp())}, separators=(",", ":")).encode()
    body = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    sig = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return body + "." + sig

def current_user(authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401, "Silakan login terlebih dahulu.")
    token = authorization[7:]
    try:
        body, sig = token.rsplit(".", 1)
        expected = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected): raise ValueError()
        import base64
        data = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if data["exp"] < int(datetime.now(timezone.utc).timestamp()): raise ValueError()
        user = db.get(User, int(data["sub"]))
        if not user: raise ValueError()
        return user
    except Exception: raise HTTPException(401, "Sesi tidak valid atau sudah berakhir.")

def admin_user(user: User = Depends(current_user)):
    if user.role != "admin": raise HTTPException(403, "Akses khusus admin.")
    return user

def active_premium(user: User):
    if user.plan != "premium" or user.subscription_status != "active" or not user.subscription_until: return False
    until = user.subscription_until.replace(tzinfo=timezone.utc) if user.subscription_until.tzinfo is None else user.subscription_until
    return until > datetime.now(timezone.utc)

def is_premium(user: User):
    return user.role == "admin" or active_premium(user)

def ensure_project_limit(db: Session, user: User):
    if not is_premium(user):
        count = db.query(Project).filter_by(user_id=user.id).count()
        if count >= 1: raise HTTPException(402, "Paket Free hanya dapat memiliki 1 proyek. Upgrade ke Premium untuk hingga 10 proyek aktif.")

def setting(db, key, default=""):
    row = db.get(Setting, key)
    return row.value if row else default

def set_setting(db, key, value):
    row = db.get(Setting, key)
    if not row: row = Setting(key=key); db.add(row)
    row.value = value

def user_payload(u):
    premium = active_premium(u)
    return {"id":u.id,"name":u.name,"email":u.email,"role":u.role,"plan":"premium" if premium else "free",
            "subscription_status":"active" if premium else ("expired" if u.plan=="premium" else "free"),
            "subscription_until":u.subscription_until.isoformat() if u.subscription_until else None}

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str

class ProjectIn(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    product: str = ""
    category: str = "other"
    destination: str = ""
    notes: str = ""

class CostIn(BaseModel):
    title: str = "Export cost estimate"
    currency: str = "IDR"
    production: float = 0
    packaging: float = 0
    inland: float = 0
    freight: float = 0
    insurance: float = 0
    customs: float = 0
    other: float = 0
    project_id: Optional[int] = None

class AssessmentIn(BaseModel):
    project_id: Optional[int] = None
    answers: dict

class TaskIn(BaseModel):
    project_id: int
    title: str
    category: str = "Preparation"

class ReviewIn(BaseModel):
    action: str
    note: str = ""

@app.on_event("startup")
def seed_admin():
    db = SessionLocal()
    try:
        email = os.getenv("ADMIN_EMAIL", "admin@expando.local").lower()
        if not db.query(User).filter_by(email=email).first():
            db.add(User(name=os.getenv("ADMIN_NAME","Expando Admin"), email=email,
                        password_hash=hash_password(os.getenv("ADMIN_PASSWORD","ChangeMe123!")), role="admin"))
            db.commit()
        if not db.get(Setting, "premium_monthly_price"):
            set_setting(db, "premium_monthly_price", "99000")
            set_setting(db, "premium_yearly_price", "990000")
            set_setting(db, "qris_image", "")
            db.commit()
    finally: db.close()

@app.get("/")
def home(): return FileResponse(BASE / "app" / "static" / "index.html")

@app.get("/api/health")
def health(): return {"status":"ok","service":"Expando API"}

@app.post("/api/auth/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", data.email): raise HTTPException(422, "Format email tidak valid.")
    email = data.email.lower()
    if db.query(User).filter_by(email=email).first(): raise HTTPException(409, "Email sudah terdaftar.")
    user = User(name=data.name.strip(), email=email, password_hash=hash_password(data.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"token":make_token(user),"user":user_payload(user)}

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", data.email): raise HTTPException(422, "Format email tidak valid.")
    user = db.query(User).filter_by(email=data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash): raise HTTPException(401, "Email atau password salah.")
    return {"token":make_token(user),"user":user_payload(user)}

@app.get("/api/auth/me")
def me(user: User = Depends(current_user)): return user_payload(user)

@app.post("/api/auth/change-password")
def change_password(data: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not verify_password(data.get("current_password",""), user.password_hash): raise HTTPException(400,"Password saat ini salah.")
    new = data.get("new_password","")
    if len(new)<8: raise HTTPException(400,"Password baru minimal 8 karakter.")
    user.password_hash=hash_password(new); db.commit(); return {"message":"Password berhasil diubah."}

@app.get("/api/plans")
def plans(db: Session = Depends(get_db)):
    return {"free":{"price":0,"projects":1,"assessment":"1 kali","countries":2,"calculator":"1 kali/bulan","storage_mb":100},
            "premium":{"monthly":int(setting(db,"premium_monthly_price","99000")),"yearly":int(setting(db,"premium_yearly_price","990000")),
                       "projects":10,"assessment":"Unlimited","countries":"All available","calculator":"Unlimited","storage_mb":2048}}

@app.post("/api/payments/create")
def create_payment(data: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role=="admin": raise HTTPException(400,"Admin tidak memerlukan subscription.")
    period = data.get("period","monthly")
    if period not in ("monthly","yearly"): raise HTTPException(400,"Periode tidak valid.")
    amount = int(setting(db,"premium_yearly_price" if period=="yearly" else "premium_monthly_price","99000" if period=="monthly" else "990000"))
    invoice = "EXP-" + datetime.utcnow().strftime("%y%m%d") + "-" + secrets.token_hex(3).upper()
    payment = Payment(user_id=user.id, invoice=invoice, plan="premium", period=period, amount=amount)
    db.add(payment); db.commit(); db.refresh(payment)
    return {"id":payment.id,"invoice":invoice,"amount":amount,"period":period,"status":payment.status,"qris_url":setting(db,"qris_image","")}

@app.post("/api/payments/{payment_id}/proof")
def upload_proof(payment_id: int, file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    payment = db.get(Payment,payment_id)
    if not payment or payment.user_id != user.id: raise HTTPException(404,"Invoice tidak ditemukan.")
    if payment.status != "pending": raise HTTPException(400,"Invoice tidak dalam status menunggu pembayaran.")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".jpg",".jpeg",".png",".webp",".pdf"): raise HTTPException(400,"Format bukti harus JPG, PNG, WEBP, atau PDF.")
    content = file.file.read()
    if len(content)>5*1024*1024: raise HTTPException(400,"Ukuran maksimal 5 MB.")
    name = f"proof_{payment.invoice}{ext}"
    path = UPLOADS / name
    path.write_bytes(content)
    payment.proof_path = name; db.commit()
    return {"message":"Bukti pembayaran terkirim. Menunggu verifikasi admin."}

@app.get("/api/payments/mine")
def my_payments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Payment).filter_by(user_id=user.id).order_by(Payment.created_at.desc()).all()
    return [{"id":p.id,"invoice":p.invoice,"amount":p.amount,"period":p.period,"status":p.status,"proof":bool(p.proof_path),"created_at":p.created_at.isoformat(),"note":p.admin_note} for p in rows]

@app.get("/api/admin/payments")
def admin_payments(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    rows=db.query(Payment).order_by(Payment.created_at.desc()).all()
    return [{"id":p.id,"user":db.get(User,p.user_id).email,"name":db.get(User,p.user_id).name,"invoice":p.invoice,"amount":p.amount,"period":p.period,"status":p.status,"proof":p.proof_path,"created_at":p.created_at.isoformat()} for p in rows]

@app.post("/api/admin/payments/{payment_id}/review")
def review_payment(payment_id:int, data:ReviewIn, _:User=Depends(admin_user), db:Session=Depends(get_db)):
    p=db.get(Payment,payment_id)
    if not p: raise HTTPException(404,"Pembayaran tidak ditemukan.")
    if p.status!="pending": raise HTTPException(400,"Pembayaran sudah diproses.")
    if data.action not in ("approve","reject"): raise HTTPException(400,"Aksi tidak valid.")
    p.status="approved" if data.action=="approve" else "rejected"; p.admin_note=data.note; p.reviewed_at=datetime.utcnow()
    if data.action=="approve":
        u=db.get(User,p.user_id)
        now=datetime.utcnow()
        current=u.subscription_until if active_premium(u) else now
        if current and current.tzinfo: current=current.replace(tzinfo=None)
        u.plan="premium"; u.subscription_status="active"
        u.subscription_until=current + (timedelta(days=365) if p.period=="yearly" else timedelta(days=30))
    db.commit()
    return {"message":"Pembayaran disetujui dan Premium diaktifkan." if data.action=="approve" else "Pembayaran ditolak."}

@app.get("/api/admin/users")
def admin_users(_:User=Depends(admin_user), db:Session=Depends(get_db)):
    return [user_payload(u) | {"created_at":u.created_at.isoformat()} for u in db.query(User).order_by(User.created_at.desc()).all()]

@app.post("/api/admin/users/{user_id}/plan")
def admin_set_plan(user_id:int, data:dict, _:User=Depends(admin_user), db:Session=Depends(get_db)):
    u=db.get(User,user_id)
    if not u: raise HTTPException(404,"User tidak ditemukan.")
    if data.get("plan")=="premium":
        days=max(1,min(int(data.get("days",30)),3650))
        u.plan="premium"; u.subscription_status="active"; u.subscription_until=datetime.utcnow()+timedelta(days=days)
    else:
        u.plan="free"; u.subscription_status="free"; u.subscription_until=None
    db.commit(); return {"message":"Paket user diperbarui."}

@app.get("/api/admin/settings")
def admin_settings(_:User=Depends(admin_user), db:Session=Depends(get_db)):
    return {"monthly":setting(db,"premium_monthly_price","99000"),"yearly":setting(db,"premium_yearly_price","990000"),"qris_url":setting(db,"qris_image","")}

@app.post("/api/admin/settings/prices")
def admin_prices(data:dict, _:User=Depends(admin_user), db:Session=Depends(get_db)):
    monthly=int(data.get("monthly",99000)); yearly=int(data.get("yearly",990000))
    if monthly<1000 or yearly<1000: raise HTTPException(400,"Harga tidak valid.")
    set_setting(db,"premium_monthly_price",str(monthly)); set_setting(db,"premium_yearly_price",str(yearly)); db.commit()
    return {"message":"Harga paket diperbarui."}

@app.post("/api/admin/settings/qris")
def admin_qris(file:UploadFile=File(...), _:User=Depends(admin_user), db:Session=Depends(get_db)):
    ext=Path(file.filename or "").suffix.lower()
    if ext not in (".jpg",".jpeg",".png",".webp"): raise HTTPException(400,"QRIS harus berupa gambar JPG, PNG, atau WEBP.")
    content=file.file.read()
    if len(content)>5*1024*1024: raise HTTPException(400,"Ukuran maksimal 5 MB.")
    name="qris"+ext
    (UPLOADS/name).write_bytes(content)
    set_setting(db,"qris_image","/uploads/"+name); db.commit()
    return {"message":"QRIS berhasil diperbarui.","url":"/uploads/"+name}

@app.get("/api/dashboard")
def dashboard(user:User=Depends(current_user), db:Session=Depends(get_db)):
    projects=db.query(Project).filter_by(user_id=user.id).all()
    tasks=db.query(Task).filter_by(user_id=user.id).all()
    assessments=db.query(Assessment).filter_by(user_id=user.id).order_by(Assessment.created_at.desc()).first()
    costs=db.query(CostEstimate).filter_by(user_id=user.id).count()
    return {"user":user_payload(user),"project_count":len(projects),"project_limit":10 if is_premium(user) else 1,
            "task_count":len(tasks),"task_done":sum(1 for t in tasks if t.done),"cost_count":costs,
            "latest_score":assessments.score if assessments else None,
            "projects":[{"id":p.id,"name":p.name,"product":p.product,"destination":p.destination,"status":p.status} for p in projects[-5:]]}

@app.get("/api/projects")
def projects(user:User=Depends(current_user), db:Session=Depends(get_db)):
    rows=db.query(Project).filter_by(user_id=user.id).order_by(Project.created_at.desc()).all()
    return [{"id":p.id,"name":p.name,"product":p.product,"category":p.category,"destination":p.destination,"status":p.status,"notes":p.notes,"created_at":p.created_at.isoformat()} for p in rows]

@app.post("/api/projects")
def create_project(data:ProjectIn, user:User=Depends(current_user), db:Session=Depends(get_db)):
    ensure_project_limit(db,user)
    p=Project(user_id=user.id,**data.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    default_tasks=[
      ("Validasi legalitas usaha","Legalitas"),("Identifikasi kode HS produk","Produk"),
      ("Periksa standar dan sertifikasi produk","Compliance"),("Siapkan spesifikasi dan kemasan","Produk"),
      ("Riset persyaratan negara tujuan","Market"),("Hitung estimasi biaya ekspor","Logistik"),
      ("Tentukan Incoterms dengan pembeli","Logistik"),("Siapkan commercial invoice dan packing list","Dokumen"),
      ("Konfirmasi freight forwarder","Logistik"),("Evaluasi kesiapan pengiriman","Final review")]
    for title,cat in default_tasks: db.add(Task(user_id=user.id,project_id=p.id,title=title,category=cat))
    db.commit()
    return {"id":p.id,"message":"Proyek dan roadmap awal berhasil dibuat."}

@app.patch("/api/projects/{project_id}")
def update_project(project_id:int, data:dict, user:User=Depends(current_user), db:Session=Depends(get_db)):
    p=db.query(Project).filter_by(id=project_id,user_id=user.id).first()
    if not p: raise HTTPException(404,"Proyek tidak ditemukan.")
    for k in ("name","product","category","destination","status","notes"):
        if k in data: setattr(p,k,data[k])
    db.commit(); return {"message":"Proyek diperbarui."}

@app.delete("/api/projects/{project_id}")
def delete_project(project_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    p=db.query(Project).filter_by(id=project_id,user_id=user.id).first()
    if not p: raise HTTPException(404,"Proyek tidak ditemukan.")
    db.query(Task).filter_by(project_id=p.id,user_id=user.id).delete()
    db.query(Assessment).filter_by(project_id=p.id,user_id=user.id).delete()
    db.query(CostEstimate).filter_by(project_id=p.id,user_id=user.id).delete()
    db.query(Document).filter_by(project_id=p.id,user_id=user.id).delete()
    db.delete(p); db.commit(); return {"message":"Proyek dihapus."}

@app.get("/api/tasks")
def tasks(project_id:Optional[int]=None,user:User=Depends(current_user),db:Session=Depends(get_db)):
    q=db.query(Task).filter_by(user_id=user.id)
    if project_id: q=q.filter_by(project_id=project_id)
    return [{"id":t.id,"project_id":t.project_id,"title":t.title,"category":t.category,"done":t.done} for t in q.order_by(Task.id).all()]

@app.patch("/api/tasks/{task_id}")
def update_task(task_id:int,data:dict,user:User=Depends(current_user),db:Session=Depends(get_db)):
    t=db.query(Task).filter_by(id=task_id,user_id=user.id).first()
    if not t: raise HTTPException(404,"Task tidak ditemukan.")
    t.done=bool(data.get("done",t.done)); db.commit(); return {"message":"Progress disimpan."}

@app.post("/api/tasks")
def add_task(data:TaskIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if not db.query(Project).filter_by(id=data.project_id,user_id=user.id).first(): raise HTTPException(404,"Proyek tidak ditemukan.")
    t=Task(user_id=user.id,**data.model_dump()); db.add(t); db.commit(); return {"message":"Task ditambahkan."}

@app.post("/api/assessments")
def assessment(data:AssessmentIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if not is_premium(user) and db.query(Assessment).filter_by(user_id=user.id).count()>=1:
        raise HTTPException(402,"Paket Free mendapat 1 assessment. Upgrade untuk assessment tanpa batas.")
    if data.project_id and not db.query(Project).filter_by(id=data.project_id,user_id=user.id).first(): raise HTTPException(404,"Proyek tidak ditemukan.")
    answers=data.answers
    keys=["legal","capacity","quality","packaging","documents","market"]
    score=round(sum(max(0,min(4,int(answers.get(k,0)))) for k in keys)/24*100)
    rec=[]
    labels={"legal":"Lengkapi legalitas usaha dan perizinan dasar.","capacity":"Pastikan kapasitas produksi dan konsistensi pasokan.","quality":"Siapkan standar mutu, pengujian, dan sertifikasi yang relevan.","packaging":"Tinjau kemasan, label, bahasa, dan ketentuan negara tujuan.","documents":"Susun daftar dokumen ekspor dan verifikasi kebutuhan per produk.","market":"Validasi permintaan, calon pembeli, harga, dan aturan impor negara tujuan."}
    for k in keys:
        if int(answers.get(k,0))<3: rec.append(labels[k])
    a=Assessment(user_id=user.id,project_id=data.project_id,score=score,answers=json.dumps(answers),recommendations=json.dumps(rec))
    db.add(a); db.commit(); db.refresh(a)
    return {"id":a.id,"score":score,"recommendations":rec}

@app.get("/api/assessments")
def assessments(user:User=Depends(current_user),db:Session=Depends(get_db)):
    return [{"id":a.id,"score":a.score,"recommendations":json.loads(a.recommendations or "[]"),"created_at":a.created_at.isoformat()} for a in db.query(Assessment).filter_by(user_id=user.id).order_by(Assessment.created_at.desc()).all()]

@app.post("/api/cost-estimates")
def create_cost(data:CostIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if not is_premium(user) and db.query(CostEstimate).filter(CostEstimate.user_id==user.id,CostEstimate.created_at>=datetime.utcnow().replace(day=1,hour=0,minute=0,second=0,microsecond=0)).count()>=1:
        raise HTTPException(402,"Paket Free mendapat 1 kalkulasi per bulan. Upgrade untuk kalkulasi tanpa batas.")
    if data.project_id and not db.query(Project).filter_by(id=data.project_id,user_id=user.id).first(): raise HTTPException(404,"Proyek tidak ditemukan.")
    d=data.model_dump(); d.pop("project_id",None)
    total=sum(d[k] for k in ("production","packaging","inland","freight","insurance","customs","other"))
    row=CostEstimate(user_id=user.id,project_id=data.project_id,total=total,**d); db.add(row); db.commit(); db.refresh(row)
    return {"id":row.id,"total":total,"currency":row.currency}

@app.get("/api/cost-estimates")
def costs(user:User=Depends(current_user),db:Session=Depends(get_db)):
    return [{"id":c.id,"title":c.title,"total":c.total,"currency":c.currency,"created_at":c.created_at.isoformat()} for c in db.query(CostEstimate).filter_by(user_id=user.id).order_by(CostEstimate.created_at.desc()).all()]

COUNTRIES=[
 {"code":"SG","name":"Singapura","region":"ASEAN","currency":"SGD","notes":"Periksa ketentuan impor Singapore Customs, persyaratan produk, label, dan izin sektoral. Produk pangan dapat memerlukan persetujuan Singapore Food Agency."},
 {"code":"MY","name":"Malaysia","region":"ASEAN","currency":"MYR","notes":"Periksa tarif dan ketentuan melalui otoritas Malaysia serta persyaratan sektoral. Produk pangan dapat memerlukan persetujuan dan label berbahasa yang sesuai."},
 {"code":"JP","name":"Jepang","region":"Asia Timur","currency":"JPY","notes":"Periksa ketentuan bea cukai Jepang, standar teknis, keamanan pangan, label bahasa Jepang, serta persyaratan karantina sesuai produk."},
 {"code":"AU","name":"Australia","region":"Oseania","currency":"AUD","notes":"Periksa Biosecurity Import Conditions (BICON), persyaratan karantina, treatment, dan ketentuan impor berdasarkan komoditas."},
 {"code":"US","name":"Amerika Serikat","region":"Amerika Utara","currency":"USD","notes":"Periksa ketentuan CBP dan regulator produk terkait. Pangan dapat melibatkan FDA, sementara produk kayu/pertanian dapat memerlukan pemeriksaan tambahan."},
 {"code":"NL","name":"Belanda","region":"Uni Eropa","currency":"EUR","notes":"Periksa ketentuan impor UE, TARIC, standar produk, keamanan, pelabelan, dan aturan keberlanjutan yang relevan."},
 {"code":"AE","name":"Uni Emirat Arab","region":"Timur Tengah","currency":"AED","notes":"Periksa ketentuan bea cukai dan otoritas emirate tujuan, registrasi produk, sertifikasi, dan label sesuai kategori."}
]
@app.get("/api/countries")
def countries(user:User=Depends(current_user)):
    return COUNTRIES if is_premium(user) else COUNTRIES[:2]

@app.get("/api/guides/incoterms")
def incoterms(user:User=Depends(current_user)):
    return [
      {"code":"EXW","name":"Ex Works","seller":"Menyediakan barang di tempat yang disepakati.","buyer":"Mengatur hampir seluruh pengangkutan dan formalitas ekspor/impor sesuai kontrak."},
      {"code":"FOB","name":"Free On Board","seller":"Menyerahkan barang di atas kapal dan mengurus formalitas ekspor.","buyer":"Menanggung biaya dan risiko setelah barang berada di atas kapal."},
      {"code":"CFR","name":"Cost and Freight","seller":"Membayar biaya angkut sampai pelabuhan tujuan; risiko berpindah saat barang di atas kapal.","buyer":"Menanggung risiko setelah barang dimuat dan mengurus asuransi bila diperlukan."},
      {"code":"CIF","name":"Cost, Insurance and Freight","seller":"Membayar angkut dan asuransi minimum sampai pelabuhan tujuan; risiko tetap berpindah saat barang di atas kapal.","buyer":"Menanggung risiko sejak barang dimuat dan formalitas impor."},
      {"code":"DAP","name":"Delivered At Place","seller":"Mengatur pengiriman sampai tempat tujuan, siap dibongkar.","buyer":"Mengurus impor dan pembongkaran."},
      {"code":"DDP","name":"Delivered Duty Paid","seller":"Menanggung pengiriman dan formalitas impor termasuk bea/pajak sesuai kontrak.","buyer":"Menerima barang di tempat tujuan."}
    ]

@app.post("/api/documents")
def upload_document(project_id:Optional[int]=Form(default=None), doc_type:str=Form(default="general"), destination:str=Form(default=""), product_category:str=Form(default="general"), file:UploadFile=File(...), user:User=Depends(current_user), db:Session=Depends(get_db)):
    if project_id and not db.query(Project).filter_by(id=project_id,user_id=user.id).first(): raise HTTPException(404,"Proyek tidak ditemukan.")
    current=db.query(Document).filter_by(user_id=user.id).all(); used=sum(d.size for d in current)
    limit=2*1024*1024*1024 if is_premium(user) else 100*1024*1024
    content=file.file.read()
    if used+len(content)>limit: raise HTTPException(402,"Batas penyimpanan paket tercapai.")
    if len(content)>15*1024*1024: raise HTTPException(400,"Ukuran satu file maksimal 15 MB.")
    ext=Path(file.filename or "").suffix.lower()
    allowed=(".pdf",".docx",".txt",".csv",".xlsx",".png",".jpg",".jpeg")
    if ext not in allowed: raise HTTPException(400,"Format didukung: PDF, DOCX, TXT, CSV, XLSX, JPG, PNG.")
    safe=re.sub(r"[^a-zA-Z0-9._-]","_",file.filename or "document")
    name=f"doc_{user.id}_{secrets.token_hex(4)}_{safe}"; (UPLOADS/name).write_bytes(content)
    d=Document(user_id=user.id,project_id=project_id,filename=file.filename or safe,stored_path=name,size=len(content))
    db.add(d); db.commit(); db.refresh(d)
    text_content=""
    try:
        if ext==".txt" or ext==".csv": text_content=content.decode("utf-8",errors="ignore")
        elif ext==".pdf":
            try:
                from pypdf import PdfReader
                import io
                text_content="\n".join((pg.extract_text() or "") for pg in PdfReader(io.BytesIO(content)).pages)
            except Exception: text_content=""
        elif ext==".docx":
            import zipfile, io
            from xml.etree import ElementTree as ET
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                root=ET.fromstring(z.read("word/document.xml"))
                text_content=" ".join(t.text or "" for t in root.iter() if t.tag.endswith("}t"))
        elif ext==".xlsx":
            import io
            from openpyxl import load_workbook
            wb=load_workbook(io.BytesIO(content),read_only=True,data_only=True)
            text_content=" ".join(str(v) for ws in wb.worksheets for row in ws.iter_rows(values_only=True) for v in row if v is not None)
    except Exception: text_content=""
    normalized=re.sub(r"\s+"," ",text_content.lower())
    rules={
      "commercial_invoice":{"label":"Commercial Invoice","required":["invoice","seller","buyer","description","quantity","unit price","total"],"help":"Pastikan invoice memuat identitas eksportir/importir, nomor/tanggal, uraian barang, kuantitas, harga satuan, total, mata uang, dan Incoterms."},
      "packing_list":{"label":"Packing List","required":["packing","package","net weight","gross weight","quantity"],"help":"Periksa jumlah kemasan, jenis kemasan, dimensi, berat bersih/kotor, marks & numbers, dan rincian barang per kemasan."},
      "certificate_origin":{"label":"Certificate of Origin / SKA","required":["certificate","origin","exporter","consignee"],"help":"Pastikan skema SKA sesuai perjanjian dagang, data eksportir/importir, deskripsi/HS code, negara asal, dan penerbit berwenang."},
      "bill_lading":{"label":"Bill of Lading / Air Waybill","required":["shipper","consignee","port","vessel"],"help":"Cocokkan shipper, consignee, notify party, pelabuhan/bandara, uraian barang, jumlah/berat, dan nomor dokumen pengangkutan."},
      "health_certificate":{"label":"Health / Sanitary Certificate","required":["health","certificate","product","establishment"],"help":"Untuk produk pangan/hewani, periksa otoritas penerbit, fasilitas/establishment, komoditas, lot, negara tujuan, dan persyaratan importir."},
      "phytosanitary":{"label":"Phytosanitary Certificate","required":["phytosanitary","scientific","treatment","consignment"],"help":"Untuk komoditas tumbuhan, periksa nama botani, jumlah, negara asal/tujuan, treatment, dan pernyataan tambahan yang diminta negara tujuan."},
      "fumigation":{"label":"Fumigation Certificate","required":["fumigation","treatment","date","container"],"help":"Periksa metode/bahan fumigasi, konsentrasi/dosis, durasi, suhu, tanggal, lokasi, dan identitas kontainer/kemasan."},
      "product_spec":{"label":"Product Specification","required":["product","material","dimension","specification"],"help":"Pastikan spesifikasi produk, bahan/komposisi, ukuran, toleransi, standar mutu, HS code indikatif, dan versi dokumen tercantum."},
      "export_permit":{"label":"Export Permit / Perizinan","required":["permit","exporter","product","valid"],"help":"Cocokkan nama eksportir, komoditas/HS code, kuota atau jumlah, masa berlaku, dan instansi penerbit."},
      "general":{"label":"Dokumen umum","required":["date"],"help":"Pilih tipe dokumen yang lebih spesifik agar pemeriksaan dapat memberikan hasil lebih relevan."}
    }
    rule=rules.get(doc_type,rules["general"])
    if not normalized:
        checks=[{"item":"Ekstraksi teks","status":"manual","detail":"Teks tidak dapat dibaca otomatis dari file ini. Periksa dokumen secara manual atau unggah PDF berbasis teks/DOCX."}]
        missing=[]; status="needs_review"
    else:
        checks=[]; missing=[]
        for term in rule["required"]:
            ok=term in normalized
            checks.append({"item":term,"status":"pass" if ok else "review","detail":"Kata/indikator ditemukan" if ok else "Tidak ditemukan secara literal; bisa jadi memakai istilah/susunan berbeda."})
            if not ok: missing.append(term)
        status="preliminary_pass" if not missing else "needs_review"
    report={"document_type":rule["label"],"status":status,"status_label":"Lolos pemeriksaan awal" if status=="preliminary_pass" else "Perlu ditinjau","checks":checks,"missing":missing,"guidance":rule["help"],"destination":destination,"product_category":product_category,"limitations":"Rule engine hanya memeriksa indikator teks/kelengkapan awal. Sistem tidak memverifikasi keaslian, tanda tangan, format resmi, regulasi terkini, atau penerimaan oleh bea cukai/otoritas."}
    db.add(DocumentCheck(document_id=d.id,user_id=user.id,report=json.dumps(report,ensure_ascii=False))); db.commit()
    return {"message":"Dokumen diunggah dan diperiksa oleh rule engine.","document_id":d.id,"analysis":report}

@app.get("/api/documents")
def documents(user:User=Depends(current_user),db:Session=Depends(get_db)):
    return [{"id":d.id,"filename":d.filename,"size":d.size,"project_id":d.project_id,"url":"/api/documents/"+str(d.id)+"/download","created_at":d.created_at.isoformat(),"analysis":(json.loads(db.query(DocumentCheck).filter_by(document_id=d.id,user_id=user.id).first().report) if db.query(DocumentCheck).filter_by(document_id=d.id,user_id=user.id).first() else None)} for d in db.query(Document).filter_by(user_id=user.id).order_by(Document.created_at.desc()).all()]

@app.get("/api/documents/{doc_id}/download")
def download_document(doc_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    d=db.query(Document).filter_by(id=doc_id,user_id=user.id).first()
    if not d: raise HTTPException(404,"Dokumen tidak ditemukan.")
    return FileResponse(UPLOADS/d.stored_path,filename=d.filename)

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    d=db.query(Document).filter_by(id=doc_id,user_id=user.id).first()
    if not d: raise HTTPException(404,"Dokumen tidak ditemukan.")
    try: (UPLOADS/d.stored_path).unlink(missing_ok=True)
    except: pass
    db.delete(d); db.commit(); return {"message":"Dokumen dihapus."}

@app.get("/api/admin/summary")
def admin_summary(_:User=Depends(admin_user),db:Session=Depends(get_db)):
    users=db.query(User).count(); premium=db.query(User).filter_by(plan="premium",subscription_status="active").count()
    pending=db.query(Payment).filter_by(status="pending").count()
    approved=db.query(Payment).filter_by(status="approved").all()
    revenue=sum(p.amount for p in approved)
    return {"users":users,"premium":premium,"pending_payments":pending,"approved_revenue":revenue,"projects":db.query(Project).count()}

@app.get("/api/admin/content")
def admin_content(_:User=Depends(admin_user),db:Session=Depends(get_db)):
    return {"countries":COUNTRIES,"qris":setting(db,"qris_image","")}

@app.exception_handler(404)
async def not_found(request, exc):
    from fastapi.responses import JSONResponse
    if request.url.path.startswith("/api/"): return JSONResponse(status_code=404,content={"detail":"Resource tidak ditemukan."})
    return FileResponse(BASE/"app"/"static"/"index.html")


# --- Guided export workspace extensions ---
from sqlalchemy import inspect as sa_inspect
class RoadmapAction(Base):
    __tablename__="roadmap_actions"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("users.id"),index=True,nullable=False)
    project_id=Column(Integer,ForeignKey("projects.id"),index=True,nullable=False)
    code=Column(String(80),nullable=False)
    title=Column(String(220),nullable=False)
    stage=Column(String(100),default="Persiapan")
    why=Column(Text,default="")
    how=Column(Text,default="")
    evidence=Column(Text,default="")
    status=Column(String(30),default="not_started")
    updated_at=Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class DocumentCheck(Base):
    __tablename__="document_checks"
    id=Column(Integer,primary_key=True)
    document_id=Column(Integer,ForeignKey("documents.id"),index=True,nullable=False)
    user_id=Column(Integer,ForeignKey("users.id"),index=True,nullable=False)
    report=Column(Text,default="{}")
    created_at=Column(DateTime,default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def seed_demo_accounts():
    db=SessionLocal()
    try:
        demos=[
          ("Expando Admin Demo","admin@expando.local",os.getenv("ADMIN_PASSWORD","ChangeMe123!"),"admin","free"),
          ("Demo User Free","free@expando.local","DemoFree123!","user","free"),
          ("Demo User Premium","premium@expando.local","DemoPremium123!","user","premium")]
        for name,email,pw,role,plan in demos:
            u=db.query(User).filter_by(email=email).first()
            if not u:
                u=User(name=name,email=email,password_hash=hash_password(pw),role=role,plan=plan,
                       subscription_status="active" if plan=="premium" else "free",
                       subscription_until=datetime.utcnow()+timedelta(days=365) if plan=="premium" else None)
                db.add(u)
        db.commit()
    finally: db.close()

ASSESSMENT_STEPS=[
 {"key":"business","title":"Profil usaha","question":"Seberapa siap identitas dan legalitas usaha Anda?","guide":"Pembeli dan mitra logistik perlu mengetahui entitas penjual yang jelas. Untuk ekspor komersial, pastikan bentuk usaha, NIB/akses kepabeanan, NPWP, dan data eksportir konsisten.","options":[{"value":0,"label":"Belum memiliki legalitas usaha"},{"value":1,"label":"Ada NIB atau legalitas dasar, belum tertata"},{"value":2,"label":"Legalitas dasar lengkap, data belum dicek untuk ekspor"},{"value":3,"label":"Legalitas dan data eksportir sudah diverifikasi"}]},
 {"key":"product","title":"Kesiapan produk","question":"Seberapa jelas spesifikasi dan klasifikasi produk Anda?","guide":"Mulai dengan uraian teknis, komposisi/material, fungsi, ukuran, proses produksi, dan HS code indikatif. HS code final perlu dikonfirmasi karena menentukan tarif dan ketentuan larangan/pembatasan.","options":[{"value":0,"label":"Spesifikasi belum terdokumentasi"},{"value":1,"label":"Spesifikasi dasar tersedia"},{"value":2,"label":"Spesifikasi dan HS code indikatif sudah ada"},{"value":3,"label":"Spesifikasi, sampel, dan klasifikasi telah ditinjau"}]},
 {"key":"capacity","title":"Kapasitas & pasokan","question":"Seberapa konsisten Anda dapat memenuhi permintaan buyer?","guide":"Hitung kapasitas per bulan, lead time, minimum order, buffer stok, ketergantungan pemasok, dan kemampuan menjaga kualitas antar-batch.","options":[{"value":0,"label":"Belum tahu kapasitas dan lead time"},{"value":1,"label":"Kapasitas diketahui tetapi belum stabil"},{"value":2,"label":"Kapasitas dan pemasok cukup stabil"},{"value":3,"label":"Kapasitas, lead time, dan rencana cadangan teruji"}]},
 {"key":"quality","title":"Mutu & standar","question":"Bagaimana pengendalian mutu produk Anda?","guide":"Tentukan spesifikasi penerimaan, inspeksi, traceability lot/batch, hasil uji, sertifikasi wajib atau sukarela, dan prosedur penanganan komplain.","options":[{"value":0,"label":"Belum ada standar mutu tertulis"},{"value":1,"label":"Ada pemeriksaan internal sederhana"},{"value":2,"label":"Ada SOP dan sebagian hasil uji/sertifikasi"},{"value":3,"label":"SOP, traceability, dan bukti mutu siap ditunjukkan"}]},
 {"key":"packaging","title":"Kemasan & label","question":"Apakah kemasan sudah sesuai kebutuhan pengiriman dan negara tujuan?","guide":"Periksa ketahanan ekspor, dimensi/berat, palletisasi, material kemasan, label, bahasa, marking, serta ketentuan khusus pangan/kayu/produk berbahaya.","options":[{"value":0,"label":"Belum dirancang untuk pengiriman ekspor"},{"value":1,"label":"Kemasan domestik tersedia"},{"value":2,"label":"Kemasan ekspor dan draft label tersedia"},{"value":3,"label":"Kemasan, label, dan marking telah ditinjau untuk pasar tujuan"}]},
 {"key":"market","title":"Pasar & buyer","question":"Seberapa tervalidasi negara tujuan dan calon pembeli?","guide":"Cari kecocokan produk, harga landed, pesaing, kanal distribusi, buyer yang dapat diverifikasi, dan persyaratan impor. Jangan menganggap minat buyer sebagai purchase order.","options":[{"value":0,"label":"Belum menentukan negara tujuan"},{"value":1,"label":"Ada negara target berdasarkan dugaan awal"},{"value":2,"label":"Sudah riset pasar dan berbicara dengan calon buyer"},{"value":3,"label":"Ada buyer terverifikasi dan indikasi permintaan tertulis"}]},
 {"key":"documents","title":"Dokumen & kepatuhan","question":"Seberapa siap dokumen transaksi dan dokumen teknis ekspor?","guide":"Dokumen umum dapat mencakup invoice, packing list, PEB/NPE, dokumen pengangkutan, dan SKA bila relevan. Produk tertentu memerlukan sertifikat kesehatan, fitosanitari, halal, fumigasi, atau izin sektoral.","options":[{"value":0,"label":"Belum mengetahui dokumen yang diperlukan"},{"value":1,"label":"Mengetahui dokumen umum, belum menyiapkan"},{"value":2,"label":"Sebagian dokumen dan persyaratan produk sudah dipetakan"},{"value":3,"label":"Dokumen transaksi dan persyaratan khusus telah ditinjau"}]}
]

@app.get("/api/guided/assessment/questions")
def guided_questions(user:User=Depends(current_user)):
    return {"steps":ASSESSMENT_STEPS,"scale":"Pilih kondisi yang paling mendekati keadaan bisnis saat ini. Nilai bukan sertifikasi atau keputusan izin ekspor."}

@app.post("/api/guided/assessment/submit")
def guided_assessment(data:dict,user:User=Depends(current_user),db:Session=Depends(get_db)):
    project_id=data.get("project_id"); answers=data.get("answers",{})
    if not is_premium(user) and db.query(Assessment).filter_by(user_id=user.id).count()>=1:
        raise HTTPException(402,"Paket Free mendapat 1 assessment. Gunakan akun Premium untuk assessment lanjutan.")
    if project_id and not db.query(Project).filter_by(id=project_id,user_id=user.id).first(): raise HTTPException(404,"Proyek tidak ditemukan.")
    keys=[x["key"] for x in ASSESSMENT_STEPS]
    if any(k not in answers for k in keys): raise HTTPException(422,"Semua pertanyaan harus dijawab sebelum hasil dibuat.")
    score=round(sum(max(0,min(3,int(answers[k]))) for k in keys)/(3*len(keys))*100)
    bands="Belum siap" if score<40 else "Perlu penguatan" if score<70 else "Mendekati siap" if score<90 else "Siap untuk validasi akhir"
    recommendations=[]
    for step in ASSESSMENT_STEPS:
        val=int(answers[step["key"]])
        if val<2: recommendations.append({"area":step["title"],"priority":"Tinggi" if val==0 else "Menengah","action":step["guide"]})
    row=Assessment(user_id=user.id,project_id=project_id,score=score,answers=json.dumps(answers),recommendations=json.dumps(recommendations,ensure_ascii=False))
    db.add(row); db.commit(); db.refresh(row)
    return {"id":row.id,"score":score,"band":bands,"recommendations":recommendations,"answers":answers,"disclaimer":"Skor ini adalah self-assessment untuk memprioritaskan pekerjaan. Bukan sertifikasi, legal opinion, atau jaminan izin ekspor."}

@app.get("/api/guided/roadmap/{project_id}")
def guided_roadmap(project_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    project=db.query(Project).filter_by(id=project_id,user_id=user.id).first()
    if not project: raise HTTPException(404,"Proyek tidak ditemukan.")
    rows=db.query(RoadmapAction).filter_by(user_id=user.id,project_id=project_id).all()
    if not rows:
        templates=[
         ("market-validation","Validasi negara tujuan & buyer","Validasi pasar","Bandingkan kecocokan produk, kisaran harga, kompetitor, kanal distribusi, dan calon buyer. Jangan mengandalkan ukuran pasar saja.","Daftar 5 buyer terverifikasi, catatan wawancara, dan asumsi harga."),
         ("classification","Konfirmasi HS code dan ketentuan barang","Kepatuhan produk","Siapkan spesifikasi lengkap lalu minta konfirmasi klasifikasi melalui sumber/otoritas yang berwenang. Periksa larangan dan pembatasan ekspor-impor.","Spesifikasi produk, HS code yang dikonfirmasi, dan hasil pemeriksaan lartas."),
         ("compliance","Petakan izin dan sertifikasi produk","Kepatuhan produk","Identifikasi regulator Indonesia dan persyaratan negara tujuan. Untuk pangan, hasil pertanian, kayu, atau produk olahan, cek aturan sektoral.","Matriks persyaratan, regulator, pemilik tugas, biaya, dan masa berlaku."),
         ("capacity","Buktikan kapasitas dan konsistensi mutu","Operasional","Uji kapasitas bulanan, lead time, batch consistency, pemasok alternatif, SOP QC, dan prosedur traceability.","Kapasitas tertulis, SOP, hasil QC, dan rencana mitigasi pasokan."),
         ("commercial","Susun penawaran dan landed-cost","Komersial","Hitung biaya sampai titik serah berdasarkan Incoterms dan moda. Nyatakan asumsi kurs, freight, asuransi, bea, pajak, dan biaya lokal.","Quotation, cost sheet, masa berlaku harga, dan asumsi kurs/freight."),
         ("shipment","Sepakati shipping plan dan Incoterms","Logistik","Pilih aturan Incoterms 2020 beserta named place/port yang presisi. Sepakati siapa mengurus booking, ekspor, impor, asuransi, dan unloading.","Konfirmasi tertulis buyer, forwarder, moda, rute, dan titik serah."),
         ("documents","Siapkan dokumen transaksi & produk","Dokumentasi","Buat invoice, packing list, dokumen kepabeanan, dokumen angkut, SKA bila diperlukan, dan sertifikat khusus sesuai komoditas.","Draft dokumen konsisten pada nama pihak, barang, kuantitas, berat, nilai, dan HS code."),
         ("pre-shipment","Lakukan pemeriksaan pra-pengapalan","Eksekusi","Cocokkan barang, kemasan, label, dokumen, booking, jadwal, dan instruksi pengiriman sebelum barang diserahkan.","Pre-shipment checklist ditandatangani dan semua discrepancy ditutup.")]
        for code,title,stage,why,ev in templates:
            db.add(RoadmapAction(user_id=user.id,project_id=project_id,code=code,title=title,stage=stage,why=why,how=why,evidence=ev))
        db.commit(); rows=db.query(RoadmapAction).filter_by(user_id=user.id,project_id=project_id).all()
    total=len(rows); done=sum(r.status=="done" for r in rows)
    return {"project":{"id":project.id,"name":project.name,"product":project.product,"destination":project.destination},"progress":round(done/total*100) if total else 0,"items":[{"id":r.id,"code":r.code,"title":r.title,"stage":r.stage,"why":r.why,"how":r.how,"evidence":r.evidence,"status":r.status} for r in rows]}

@app.patch("/api/guided/roadmap/items/{item_id}")
def update_roadmap_item(item_id:int,data:dict,user:User=Depends(current_user),db:Session=Depends(get_db)):
    row=db.query(RoadmapAction).filter_by(id=item_id,user_id=user.id).first()
    if not row: raise HTTPException(404,"Langkah roadmap tidak ditemukan.")
    status=data.get("status")
    if status not in ("not_started","in_progress","done","blocked"): raise HTTPException(422,"Status tidak valid.")
    row.status=status; db.commit(); return {"message":"Status roadmap diperbarui."}

COUNTRY_INTEL=[
 {"code":"SG","name":"Singapura","region":"ASEAN","currency":"SGD","market":"Pasar dekat dengan rantai pasok Indonesia; persaingan dan konsistensi kualitas penting. Biaya logistik relatif mudah dibanding pasar jauh, tetapi ukuran pasar domestik terbatas.","customs":"Importir/deklaran mengurus deklarasi impor melalui Singapore Customs. Persyaratan tambahan bergantung pada klasifikasi dan jenis barang.","sectors":{"food":"Produk pangan dapat memerlukan registrasi/import approval dan pemenuhan ketentuan Singapore Food Agency (SFA). Label dan keamanan pangan perlu ditinjau.","agri":"Produk tumbuhan/hewan dapat memerlukan izin, sertifikat kesehatan/fitosanitari, dan pemeriksaan SFA/NParks.","wood":"Periksa ketentuan material, spesies kayu, CITES bila relevan, dan aturan produk kayu."},"sources":[{"name":"Singapore Customs — Import Procedures","url":"https://www.customs.gov.sg/businesses/importing-goods/import-procedures/"},{"name":"Singapore Food Agency","url":"https://www.sfa.gov.sg/"}]},
 {"code":"MY","name":"Malaysia","region":"ASEAN","currency":"MYR","market":"Kedekatan geografis dan bahasa memberi peluang, tetapi standar, persaingan harga, dan kanal distribusi perlu divalidasi per kategori.","customs":"Periksa tarif, aturan impor, dan larangan/pembatasan berdasarkan HS code dengan Royal Malaysian Customs serta kementerian teknis.","sectors":{"food":"Produk pangan perlu ditinjau terhadap ketentuan Food Act/Food Regulations, label, dan persetujuan otoritas terkait. Klaim halal harus memiliki dasar sertifikasi yang diterima.","agri":"Komoditas pertanian dapat memerlukan izin MAQIS dan sertifikat fitosanitari/kesehatan.","wood":"Periksa spesies, legalitas sumber, standar produk, dan ketentuan impor kayu."},"sources":[{"name":"Royal Malaysian Customs Department","url":"https://www.customs.gov.my/"},{"name":"MATRADE","url":"https://www.matrade.gov.my/"},{"name":"MAQIS","url":"https://www.maqis.gov.my/"}]},
 {"code":"JP","name":"Jepang","region":"Asia Timur","currency":"JPY","market":"Pasar bernilai tinggi dengan tuntutan mutu, traceability, kemasan, dan konsistensi yang ketat. Validasi buyer dan standar produk sebelum mengirim sampel komersial.","customs":"Tarif dan prosedur bergantung HS code. Importir perlu memastikan kepatuhan bea cukai, standar teknis, dan aturan sektoral.","sectors":{"food":"Pangan impor tunduk pada Food Sanitation Act dan notifikasi impor melalui MHLW. Produk tumbuhan/hewan dapat terkena karantina MAFF.","agri":"Periksa Plant Protection Station, animal quarantine, treatment, dan dokumen fitosanitari/kesehatan.","wood":"Periksa aturan spesies, karantina tumbuhan, legalitas kayu, dan standar bahan/produk."},"sources":[{"name":"Japan Customs","url":"https://www.customs.go.jp/english/"},{"name":"MHLW — Imported Foods","url":"https://www.mhlw.go.jp/english/topics/importedfoods/"},{"name":"MAFF Plant Protection Station","url":"https://www.maff.go.jp/pps/j/"}]},
 {"code":"AU","name":"Australia","region":"Oceania","currency":"AUD","market":"Pasar dengan daya beli tinggi namun kontrol biosecurity ketat. Kelayakan produk harus dicek sebelum menanggung biaya pengiriman.","customs":"Periksa tarif dan prosedur Australian Border Force serta persyaratan biosecurity Department of Agriculture.","sectors":{"food":"Persyaratan impor dan biosecurity dapat berbeda menurut produk/negara asal. Cari komoditas secara spesifik di BICON sebelum pengiriman.","agri":"BICON menentukan apakah impor diizinkan, perlakuan, sertifikat, dan kondisi biosecurity.","wood":"Produk kayu/kemasan kayu dapat memerlukan treatment ISPM 15 dan deklarasi biosecurity."},"sources":[{"name":"BICON — Biosecurity Import Conditions","url":"https://bicon.agriculture.gov.au/"},{"name":"Australian Border Force","url":"https://www.abf.gov.au/"}]},
 {"code":"NL","name":"Belanda","region":"Uni Eropa","currency":"EUR","market":"Gerbang distribusi Eropa dengan tuntutan standar, dokumentasi, keberlanjutan, dan traceability. Buyer sering meminta bukti kepatuhan sebelum kontrak.","customs":"Tarif dan measures dapat ditelusuri melalui TARIC/Access2Markets. Importir UE bertanggung jawab atas kewajiban impor dan kepatuhan produk.","sectors":{"food":"Periksa EU food law, kontaminan, residu, label, traceability, serta persyaratan komoditas pada otoritas UE.","agri":"Produk tanaman/hewan dapat memerlukan sertifikat resmi, pemeriksaan perbatasan, dan ketentuan SPS.","wood":"Periksa EUDR, legalitas dan geolokasi sumber kayu sesuai cakupan komoditas/tanggal penerapan, serta aturan produk."},"sources":[{"name":"EU Access2Markets","url":"https://trade.ec.europa.eu/access-to-markets/"},{"name":"EU TARIC","url":"https://taxation-customs.ec.europa.eu/customs-4/calculation-customs-duties/customs-tariff/eu-customs-tariff-taric_en"},{"name":"European Commission — Food Safety","url":"https://food.ec.europa.eu/"}]},
 {"code":"US","name":"Amerika Serikat","region":"North America","currency":"USD","market":"Pasar besar dan kompetitif. Persyaratan produk sangat sektoral; biaya kepatuhan dan distribusi perlu dihitung sebelum menetapkan harga.","customs":"Periksa tarif, entry requirements, dan trade remedies melalui US Customs and Border Protection.","sectors":{"food":"Produk pangan dapat tunduk pada FDA, facility registration, prior notice, FSVP, dan ketentuan label tergantung jenis produk.","agri":"Produk tanaman/hewan dapat memerlukan izin USDA-APHIS dan pemeriksaan CBP.","wood":"Periksa deklarasi Lacey Act, spesies kayu, legal harvest, dan ketentuan produk terkait."},"sources":[{"name":"US Customs and Border Protection","url":"https://www.cbp.gov/"},{"name":"US FDA — Importing Food Products","url":"https://www.fda.gov/industry/importing-fda-regulated-products/importing-food-products-united-states"},{"name":"USDA APHIS","url":"https://www.aphis.usda.gov/"}]}
]

@app.get("/api/country-intel")
def country_intel(code:str="SG",product_category:str="general",user:User=Depends(current_user)):
    if not is_premium(user) and code not in ("SG","MY"): raise HTTPException(402,"Akun Free dapat mengakses Singapura dan Malaysia. Upgrade untuk membuka negara lain.")
    row=next((x for x in COUNTRY_INTEL if x["code"]==code.upper()),None)
    if not row: raise HTTPException(404,"Negara belum tersedia dalam basis data Expando.")
    sector=row["sectors"].get(product_category,row["sectors"].get("food") if product_category=="fnb" else row["sectors"].get("agri") if product_category=="agriculture" else "Tidak ada catatan sektoral spesifik dalam ringkasan ini. Periksa HS code dan sumber otoritas resmi.")
    return {**row,"sector_guidance":sector,"data_note":"Ringkasan referensi kurasi, bukan feed real-time. Aturan, tarif, dan prosedur dapat berubah. Konfirmasi berdasarkan HS code, tanggal transaksi, dan otoritas resmi sebelum ekspor."}

INCOTERMS={
 "EXW":{"name":"Ex Works","mode":"Any mode","seller":"Menyediakan barang di tempat yang disebutkan; bantuan pemuatan/ekspor terbatas.","buyer":"Mengambil barang, mengurus muat, ekspor, angkut, impor, dan risiko hampir seluruh perjalanan.","risk":"Saat barang tersedia bagi pembeli di tempat yang disebutkan, belum dimuat.","insurance":"Tidak diwajibkan oleh rule Incoterms.","note":"Sering tidak ideal untuk eksportir pemula karena formalitas ekspor berada pada pembeli."},
 "FCA":{"name":"Free Carrier","mode":"Any mode","seller":"Mengurus clearance ekspor dan menyerahkan barang kepada carrier di tempat yang disepakati.","buyer":"Mengatur angkutan utama, impor, dan risiko setelah penyerahan kepada carrier.","risk":"Saat barang diserahkan kepada carrier/orang yang ditunjuk di titik FCA.","insurance":"Tidak diwajibkan.","note":"Sering lebih sesuai untuk kontainer/multimoda daripada FOB."},
 "CPT":{"name":"Carriage Paid To","mode":"Any mode","seller":"Mengurus ekspor dan membayar angkutan sampai tempat tujuan yang disebutkan.","buyer":"Menanggung risiko sejak barang diserahkan ke carrier pertama dan mengurus impor.","risk":"Saat diserahkan kepada carrier pertama, bukan saat tiba.","insurance":"Tidak diwajibkan.","note":"Biaya dan risiko berpindah pada titik yang berbeda; jelaskan titik serah carrier."},
 "CIP":{"name":"Carriage and Insurance Paid To","mode":"Any mode","seller":"Seperti CPT, ditambah mengadakan asuransi sesuai cakupan Incoterms 2020.","buyer":"Menanggung risiko sejak penyerahan ke carrier pertama dan mengurus impor.","risk":"Saat diserahkan kepada carrier pertama.","insurance":"Penjual wajib menyediakan cakupan lebih luas (umumnya Institute Cargo Clauses A) kecuali disepakati lain.","note":"Cocok untuk multimoda ketika pembeli meminta perlindungan asuransi dari penjual."},
 "DAP":{"name":"Delivered at Place","mode":"Any mode","seller":"Mengatur pengangkutan sampai tempat tujuan dan menanggung risiko sampai barang siap dibongkar.","buyer":"Mengurus impor, bea/pajak impor, dan pembongkaran.","risk":"Di tempat tujuan, siap dibongkar dari kendaraan.","insurance":"Tidak diwajibkan.","note":"Tentukan alamat/titik tujuan secara presisi."},
 "DPU":{"name":"Delivered at Place Unloaded","mode":"Any mode","seller":"Mengatur pengangkutan dan membongkar barang di tempat tujuan.","buyer":"Mengurus impor dan bea/pajak impor.","risk":"Setelah barang dibongkar di tempat tujuan.","insurance":"Tidak diwajibkan.","note":"Pastikan penjual benar-benar mampu dan diizinkan melakukan unloading."},
 "DDP":{"name":"Delivered Duty Paid","mode":"Any mode","seller":"Menanggung pengangkutan, clearance ekspor dan impor, bea/pajak impor.","buyer":"Menerima barang di tempat tujuan; pembongkaran umumnya tanggung jawab pembeli.","risk":"Di tempat tujuan, siap dibongkar.","insurance":"Tidak diwajibkan.","note":"Berisiko tinggi bagi penjual asing jika tidak dapat menjadi importir/registrasi pajak di negara tujuan."},
 "FAS":{"name":"Free Alongside Ship","mode":"Sea and inland waterway","seller":"Mengurus ekspor dan menempatkan barang di sisi kapal di pelabuhan muat.","buyer":"Menanggung pemuatan kapal, angkutan laut, impor, dan seterusnya.","risk":"Saat barang ditempatkan di sisi kapal.","insurance":"Tidak diwajibkan.","note":"Khusus laut/perairan; lazim untuk komoditas curah tertentu."},
 "FOB":{"name":"Free On Board","mode":"Sea and inland waterway","seller":"Mengurus ekspor dan memuat barang ke atas kapal di pelabuhan muat.","buyer":"Mengatur angkutan laut, impor, dan risiko setelah barang di atas kapal.","risk":"Saat barang berada di atas kapal.","insurance":"Tidak diwajibkan.","note":"Khusus laut/perairan dan umumnya bukan pilihan terbaik untuk kontainer yang diserahkan ke terminal lebih awal; pertimbangkan FCA."},
 "CFR":{"name":"Cost and Freight","mode":"Sea and inland waterway","seller":"Mengurus ekspor dan membayar freight sampai pelabuhan tujuan.","buyer":"Menanggung risiko sejak barang di atas kapal dan mengurus impor.","risk":"Saat barang berada di atas kapal di pelabuhan muat.","insurance":"Tidak diwajibkan.","note":"Penjual membayar freight tetapi risiko berpindah di pelabuhan muat."},
 "CIF":{"name":"Cost, Insurance and Freight","mode":"Sea and inland waterway","seller":"Seperti CFR, ditambah asuransi minimum untuk kepentingan pembeli.","buyer":"Menanggung risiko sejak barang di atas kapal dan mengurus impor.","risk":"Saat barang berada di atas kapal di pelabuhan muat.","insurance":"Penjual wajib menyediakan minimum cover (umumnya Institute Cargo Clauses C) kecuali disepakati lain.","note":"Biaya sampai pelabuhan tujuan, tetapi risiko berpindah sejak pelabuhan muat."}}

@app.post("/api/shipping/recommend")
def shipping_recommend(data:dict,user:User=Depends(current_user)):
    mode=data.get("mode","sea"); control=data.get("seller_control","medium"); buyer_import=bool(data.get("buyer_import",True)); container=bool(data.get("container",True)); destination=data.get("destination","named destination")
    if mode=="sea" and container: code="FCA" if control in ("low","medium") else "CPT"
    elif not buyer_import: code="DAP" if control!="high" else "DDP"
    elif control=="low": code="FCA" if mode=="sea" else "FCA"
    elif control=="high": code="CIP" if mode!="sea" else "CIF"
    else: code="CPT" if mode!="sea" else "CFR"
    if code not in INCOTERMS: code="FCA"
    term=INCOTERMS[code]
    return {"recommended":code,"term":term,"named_place":destination,"contract_wording":f"{code} {destination} — Incoterms® 2020","reason":"Rekomendasi awal berdasarkan moda, penggunaan kontainer, kemampuan mengatur pengangkutan, dan kesiapan importir. Negosiasikan titik serah dan pembagian biaya secara tertulis.","alternatives":[c for c in (["FCA","CPT","CIP"] if mode!="sea" or container else ["FOB","CFR","CIF"]) if c!=code],"warning":"Ini panduan pemilihan awal, bukan nasihat hukum. Konfirmasi kontrak, titik serah, kemampuan customs, dan asuransi dengan forwarder/buyer."}

@app.get("/api/guides/incoterms/full")
def incoterms_full(user:User=Depends(current_user)):
    return INCOTERMS
