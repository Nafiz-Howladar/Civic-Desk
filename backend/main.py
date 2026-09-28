import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func, or_
from sqlalchemy.orm import Session, relationship

from database import Base, configure_database, get_db

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('complain.api')
SECRET_KEY = os.getenv('SECRET_KEY', 'development-only-change-me')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
TOKEN_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '1440'))
password_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth_scheme = OAuth2PasswordBearer(tokenUrl='User_Login')
optional_oauth_scheme = OAuth2PasswordBearer(tokenUrl='User_Login', auto_error=False)

app = FastAPI(title='CivicDesk Complaint Management API', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default='user')
    complaints = relationship('Complaint', back_populates='owner', cascade='all, delete-orphan')


class Complaint(Base):
    __tablename__ = 'complains'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(60), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    image = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default='Pending')
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    owner = relationship('User', back_populates='complaints')


class UserCreate(BaseModel):
    name: str = Field(min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8, max_length=30)
    role: str = Field(default='user', min_length=3, max_length=30)


class UserEdit(BaseModel):
    name: str = Field(min_length=3, max_length=30)
    email: EmailStr


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=30)


class ComplaintCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(default=None, max_length=60)
    location: Optional[str] = Field(default=None, max_length=255)
    image: Optional[str] = None


class ComplaintUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(default=None, max_length=60)
    location: Optional[str] = Field(default=None, max_length=255)
    image: Optional[str] = None
    status: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    model_config = ConfigDict(from_attributes=True)


class ComplaintOut(BaseModel):
    id: int
    title: Optional[str]
    description: Optional[str]
    category: Optional[str]
    location: Optional[str]
    image: Optional[str]
    status: str
    created_at: datetime
    user_email: str
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_complaint(cls, complaint: Complaint):
        return cls(id=complaint.id, title=complaint.title, description=complaint.description,
                   category=complaint.category, location=complaint.location, image=complaint.image,
                   status=complaint.status, created_at=complaint.created_at,
                   user_email=complaint.owner.email)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def create_access_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES)
    payload = {'sub': str(user.id), 'email': user.email, 'name': user.name, 'role': user.role, 'exp': expires}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def user_from_token(token: str, db: Session) -> User:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired authentication token', headers={'WWW-Authenticate': 'Bearer'})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get('sub', ''))
    except (JWTError, ValueError, TypeError):
        raise unauthorized
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise unauthorized
    return user


def current_user(token: str = Depends(oauth_scheme), db: Session = Depends(get_db)) -> User:
    return user_from_token(token, db)


def admin_user(user: User = Depends(current_user)) -> User:
    if user.role.lower() != 'admin':
        raise HTTPException(status_code=403, detail='Administrator access required')
    return user


def complaint_or_404(db: Session, complain_id: int) -> Complaint:
    item = db.query(Complaint).filter(Complaint.id == complain_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail='Complaint not found')
    return item


@app.on_event('startup')
def startup() -> None:
    configure_database()
    Base.metadata.create_all(bind=__import__('database').engine)
    db = next(get_db())
    try:
        admin = db.query(User).filter(func.lower(User.email) == 'admin@example.com').first()
        user = db.query(User).filter(func.lower(User.email) == 'jubayer@example.com').first()
        if admin is None:
            admin = User(name='Admin', email='admin@example.com', password_hash=hash_password('admin1234'), role='admin')
            db.add(admin)
        if user is None:
            user = User(name='Jubayer', email='jubayer@example.com', password_hash=hash_password('12345678'), role='user')
            db.add(user)
        db.flush()
        sample_complaints = [
            ('electricity', 'Street lights are out', 'Several street lights need repair along the main road.', 'Main Road, Ward 1', 'Pending', user),
            ('water', 'Water leak by the park', 'A water pipe is leaking near the park entrance.', 'Community Park', 'Progress', user),
            ('road', 'Pothole needs repair', 'A large pothole is affecting traffic and needs attention.', 'Central Avenue', 'Complete', admin),
        ]
        existing_categories = {
            category.lower() for (category,) in db.query(Complaint.category).filter(Complaint.category.isnot(None)).distinct()
        }
        missing_samples = [sample for sample in sample_complaints if sample[0] not in existing_categories]
        if missing_samples:
            db.add_all([
                Complaint(category=category, title=title, description=description, location=location, status=complaint_status, owner=owner)
                for category, title, description, location, complaint_status, owner in missing_samples
            ])
            db.commit()
            logger.info('Seeded missing demo complaint categories: %s', ', '.join(sample[0] for sample in missing_samples))
    finally:
        db.close()


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.get('/me', response_model=UserOut)
def get_current_profile(user: User = Depends(current_user)):
    return user


@app.post('/create_user', response_model=UserOut)
def create_user(body: UserCreate, db: Session = Depends(get_db), token: Optional[str] = Depends(optional_oauth_scheme)):
    role = 'user'
    if body.role.lower() == 'admin':
        if token is None:
            raise HTTPException(status_code=401, detail='Admin authentication required', headers={'WWW-Authenticate': 'Bearer'})
        creator = user_from_token(token, db)
        if creator.role.lower() != 'admin':
            raise HTTPException(status_code=403, detail='Administrator access required')
        role = 'admin'
    if db.query(User).filter(func.lower(User.email) == body.email.lower()).first():
        raise HTTPException(status_code=409, detail='An account with this email already exists')
    user = User(name=body.name.strip(), email=body.email.lower(), password_hash=hash_password(body.password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post('/User_Login')
def user_login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(or_(func.lower(User.email) == form.username.lower(), func.lower(User.name) == form.username.lower())).first()
    if user is None or not password_context.verify(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Incorrect username or password', headers={'WWW-Authenticate': 'Bearer'})
    return {'access_token': create_access_token(user), 'token_type': 'bearer', 'role': user.role, 'name': user.name, 'email': user.email}


@app.put('/edituser', response_model=UserOut)
def edit_user(body: UserEdit, user: User = Depends(current_user), db: Session = Depends(get_db)):
    existing = db.query(User).filter(func.lower(User.email) == body.email.lower(), User.id != user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail='That email address is already in use')
    user.name = body.name.strip()
    user.email = body.email.lower()
    db.commit()
    db.refresh(user)
    return user


@app.put('/passwordchange')
def password_change(body: PasswordChange, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not password_context.verify(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail='Current password is incorrect')
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {'message': 'Password updated successfully'}


@app.get('/', response_model=list[ComplaintOut])
def public_complaints(db: Session = Depends(get_db)):
    complaints = db.query(Complaint).order_by(Complaint.created_at.desc(), Complaint.id.desc()).all()
    return [ComplaintOut.from_complaint(item) for item in complaints]


@app.post('/complain_create', response_model=ComplaintOut)
def create_complaint(body: ComplaintCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = Complaint(**body.model_dump(), status='Pending', owner=user)
    db.add(item)
    db.commit()
    db.refresh(item)
    return ComplaintOut.from_complaint(item)


@app.get('/ComplainList', response_model=list[ComplaintOut])
def user_complaints(user: User = Depends(current_user), db: Session = Depends(get_db)):
    items = db.query(Complaint).filter(Complaint.user_id == user.id).order_by(Complaint.created_at.desc(), Complaint.id.desc()).all()
    return [ComplaintOut.from_complaint(item) for item in items]


@app.get('/admin/allcomplain', response_model=list[ComplaintOut])
def all_complaints(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    items = db.query(Complaint).order_by(Complaint.created_at.desc(), Complaint.id.desc()).all()
    return [ComplaintOut.from_complaint(item) for item in items]


@app.get('/admin_search_complain/{complain_id}', response_model=ComplaintOut)
def search_complaint(complain_id: int, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    return ComplaintOut.from_complaint(complaint_or_404(db, complain_id))


@app.get('/admin_filter_category/', response_model=list[ComplaintOut])
def filter_complaints(category: str, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    items = db.query(Complaint).filter(func.lower(Complaint.category) == category.lower()).order_by(Complaint.created_at.desc()).all()
    return [ComplaintOut.from_complaint(item) for item in items]


def update_complaint_status(complain_id: int, value: str, db: Session) -> ComplaintOut:
    item = complaint_or_404(db, complain_id)
    item.status = value
    db.commit()
    db.refresh(item)
    return ComplaintOut.from_complaint(item)


@app.put('/admin_status_progress/{complain_id}', response_model=ComplaintOut)
def mark_progress(complain_id: int, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    return update_complaint_status(complain_id, 'Progress', db)


@app.put('/admin_status_complete/{complain_id}', response_model=ComplaintOut)
def mark_complete(complain_id: int, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    return update_complaint_status(complain_id, 'Complete', db)


@app.put('/complain_update/{complain_id}', response_model=ComplaintOut)
def update_complaint(complain_id: int, body: ComplaintUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = complaint_or_404(db, complain_id)
    if user.role.lower() != 'admin' and item.user_id != user.id:
        raise HTTPException(status_code=403, detail='You can only update your own complaint')
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == 'status' and user.role.lower() != 'admin':
            continue
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return ComplaintOut.from_complaint(item)


@app.delete('/complain_delete/{complain_id}')
def delete_complaint(complain_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = complaint_or_404(db, complain_id)
    if user.role.lower() != 'admin' and item.user_id != user.id:
        raise HTTPException(status_code=403, detail='You can only delete your own complaint')
    db.delete(item)
    db.commit()
    return {'message': 'Complaint deleted successfully'}


@app.post('/forgot_password')
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Production reset delivery needs an email provider and signed one-time reset flow.
    exists = db.query(User.id).filter(func.lower(User.email) == body.email.lower()).first()
    return {'message': 'If the account exists, reset instructions are ready.' if exists else 'If the account exists, reset instructions are ready.'}
