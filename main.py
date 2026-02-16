from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import User, Post
from datetime import datetime, timedelta
import secrets
from email_utils import send_reset_email
from datetime import datetime, timedelta
import uuid

from schemas import ResetPasswordRequest
from schemas import UserCreate, UserResponse, PostCreate, PostResponse
from auth import hash_password, verify_password, create_access_token
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://rajneeti-frontend.vercel.app"
]



load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# =====================
# AUTH HELPERS
# =====================

def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user

@app.get("/")
def root():
    return {"message": "Rajneeti Backend is Live 🇮🇳"}

# =====================
# REGISTER
# =====================

@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):

    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


# =====================
# LOGIN
# =====================

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    identifier = form_data.username.strip()

    # Check email or username
    if "@" in identifier:
        user = db.query(User).filter(User.email == identifier).first()
    else:
        user = db.query(User).filter(User.username == identifier).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password"
        )

    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "email": user.email
    }
# =====================
# FORGOT PASSWORD
# =====================
@app.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Return success anyway to prevent email enumeration attacks
        return {"message": "Password reset link sent to email"}

    # Create reset token (valid for 30 minutes)
    reset_token = create_access_token(
        data={"sub": str(user.id), "type": "reset"},
        expires_delta=timedelta(minutes=30)
    )

    # ✅ KEY FIX: Save token + expiry to DB so /reset-password can look it up
    user.reset_token = reset_token
    user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=30)
    db.commit()

    # Create reset link
    reset_link = f"https://rajneeti-frontend.vercel.app/reset-password.html?token={reset_token}"

    # Send email
    send_reset_email(user.email, reset_link)

    return {"message": "Password reset link sent to email"}
# =====================
# RESET PASSWORD
# =====================

@app.post("/reset-password")
def reset_password(data: ResetPasswordRequest,
                   db: Session = Depends(get_db)):

    token = data.token
    new_password = data.new_password

    # ✅ Look up user by the stored reset_token in DB
    user = db.query(User).filter(User.reset_token == token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or already used token")

    if user.reset_token_expiry is None or user.reset_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token has expired. Please request a new reset link.")

    # Update password and clear the token
    user.hashed_password = hash_password(new_password)
    user.reset_token = None
    user.reset_token_expiry = None

    db.commit()

    return {"message": "Password reset successful"}




# =====================
# CREATE POST
# =====================

@app.post("/posts", response_model=PostResponse)
def create_post(post: PostCreate,
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):

    db_post = Post(
        title=post.title,
        body=post.body,
        category=post.category,
        language=post.language,
        state=post.state,
        user_id=current_user.id
    )

    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    return db_post


# =====================
# GET ALL POSTS (Pagination)
# =====================

@app.get("/posts", response_model=list[PostResponse])
def get_posts(page: int = 1,
              limit: int = 10,
              db: Session = Depends(get_db)):

    skip = (page - 1) * limit

    posts = db.query(Post).offset(skip).limit(limit).all()

    return posts


# =====================
# GET MY POSTS
# =====================

@app.get("/my-posts", response_model=list[PostResponse])
def get_my_posts(db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):

    return db.query(Post).filter(Post.user_id == current_user.id).all()


# =====================
# DELETE POST
# =====================

@app.delete("/posts/{post_id}")
def delete_post(post_id: str,
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):

    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(post)
    db.commit()

    return {"detail": "Post deleted successfully"}
