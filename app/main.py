from fastapi import FastAPI, Request, Form, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from uuid import uuid4

# 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 모델 정의
Base = declarative_base()

# 사용자 데이터베이스 정의
class User(Base):
    __tablename__ = "users"

    # 사용자 id
    id = Column(String, primary_key=True, index=True)
    # 사용자 이름
    name = Column(String)
    # 사용자 비밀번호
    password = Column(String)
    # 사용자 세션
    session_id = Column(String)

# 게시글 데이터베이스 정의
class Post(Base):
    __tablename__ = "posts"

    # 게시글 id
    id = Column(Integer, primary_key=True, index=True)
    # 게시글 제목
    title = Column(String, index=True)
    # 게시글 내용
    content = Column(Text)
    # 게시글 작성자
    author = Column(String)
    # 게시글 작성 시각
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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

def check_session(session_id: str = Cookie(None), db: Session = Depends(get_db)):
    if session_id:
        user = db.query(User).filter(User.session_id == session_id).first()
        return user if user else False
    else:
        return False

@app.get("/")
def base_page(req: Request, session: bool = Depends(check_session)):
    if session:
        return templates.TemplateResponse("base_s.html", {"request": req})
    else:
        return templates.TemplateResponse("base.html", {"request": req})

@app.get("/sign_up")
def sign_up_page(req: Request):
    return templates.TemplateResponse("signup.html", {"request": req})

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
    return templates.TemplateResponse("login.html", {"request": req})

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

@app.get("/logout")
def logout():
    res = RedirectResponse(url='/')
    res.delete_cookie("session_id")
    return res

@app.get("/mypage")
def mypage(req: Request, session: User = Depends(check_session)):
    if session:
        return templates.TemplateResponse("mypage.html", {"request": req, "user": session})
    else:
        return RedirectResponse(url='/sign_in')

@app.get("/myaccount")
def myaccount_page(req: Request, db: Session = Depends(get_db), session_id: str = Cookie(None)):
    db_user = db.query(User).filter(User.session_id == session_id).first()
    if db_user:
        return templates.TemplateResponse("myaccount.html", {"request": req, "user": db_user})
    else:
        return RedirectResponse(url="/sign_in", status_code=303)

@app.post("/myaccount/")
def update_account(name: str = Form(...), password: str = Form(...), db: Session = Depends(get_db), session_id: str = Cookie(None)):
    db_user = db.query(User).filter(User.session_id == session_id).first()
    if db_user:
        db_user.name = name
        db_user.password = password
        db.commit()
        return RedirectResponse(url="/mypage", status_code=303)
    else:
        return RedirectResponse(url="/sign_in", status_code=303)