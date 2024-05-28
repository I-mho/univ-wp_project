from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from uuid import uuid4

# 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 모델 정의
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    password = Column(String)
    session_id = Column(String)

# 데이터베이스 초기화
Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# DB 세션 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def base_page(req: Request):
    return templates.TemplateResponse("base.html", {"request": req})

@app.get("/sign_up")
def sign_up_page(req: Request):
    return templates.TemplateResponse("sign_up.html", {"request": req})

@app.post("/sign_up/", response_class=HTMLResponse)
def sign_up(name: str = Form(...), id: str = Form(...), pw: str = Form(...), db: Session = Depends(get_db)):
    session_id = str(uuid4())
    db_user = User(id=id, name=name, password=pw, session_id=session_id)
    db.add(db_user)
    db.commit()
    return RedirectResponse(url='/sign_up-success', status_code=303)

@app.get("/sign_up-success")
def success(req: Request):
    return templates.TemplateResponse("success.html", {"request": req})

@app.get("/sign_in")
def sign_in_page(req: Request):
    return templates.TemplateResponse("sign_in.html", {"request": req})

@app.post("/sign_in/")
def sign_in(id: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # 로그인 시도: 데이터베이스에서 사용자 확인 및 세션 설정
    db_user = db.query(User).filter(User.id == id, User.password == password).first()
    if db_user:
        # 로그인 성공: 세션 설정 및 메인 페이지로 이동
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="session_id", value=db_user.session_id)
        return response
    else:
        return {"message": "로그인 실패!"}