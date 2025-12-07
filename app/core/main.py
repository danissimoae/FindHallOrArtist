from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import uvicorn

from database.database import engine, get_db, Base
from app.models.models import User, Artist, Organizer, Booking, Review, Message
from app.schemas.schemas import (
    UserCreate, UserResponse, Token,
    ArtistCreate, ArtistResponse, ArtistUpdate,
    OrganizerCreate, OrganizerResponse,
    BookingCreate, BookingResponse, BookingUpdate,
    ReviewCreate, ReviewResponse,
    MessageCreate, MessageResponse,
    ArtistSearch
)
from app.services.auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, get_current_active_user
)

# Создание таблиц в БД
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="МузПлатформа API",
    description="API для платформы взаимодействия музыкальных исполнителей и организаторов",
    version="1.0.0"
)

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтирование статических файлов
import os

if not os.path.exists("static"):
    os.makedirs("static")
    os.makedirs("static/css")
    os.makedirs("static/js")
    os.makedirs("static/images")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Главная страница перенаправляет на static/index.html
from fastapi.responses import RedirectResponse


@app.get("/")
def root():
    """Перенаправление на главную страницу"""
    return RedirectResponse(url="/static/index.html")


# ==================== Ф1: РЕГИСТРАЦИЯ И АУТЕНТИФИКАЦИЯ ====================

@app.post("/api/register", response_model=UserResponse, tags=["Аутентификация"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя (артист/организатор/админ)"""
    # Проверка существования email
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    # Создание пользователя
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        password_hash=hashed_password,
        phone=user.phone,
        role=user.role,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.post("/api/token", response_model=Token, tags=["Аутентификация"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Аутентификация и получение токена"""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/users/me", response_model=UserResponse, tags=["Пользователи"])
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Получение информации о текущем пользователе"""
    return current_user


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

# ИСПРАВЛЕНИЕ: Функция для преобразования строки жанров в список для Pydantic
def _prepare_artist_response(artist_db):
    """Преобразует строку жанров из БД в список для схемы ответа Pydantic."""
    # Если genres — строка (из БД), преобразуем ее в список
    if artist_db and isinstance(artist_db.genres, str):
        # Разделяем строку, удаляем пробелы и фильтруем пустые элементы
        artist_db.genres = [g.strip() for g in artist_db.genres.split(',') if g.strip()]
    elif artist_db and artist_db.genres is None:
        artist_db.genres = []

    return artist_db

# ==================== Ф2: УПРАВЛЕНИЕ ПРОФИЛЕМ АРТИСТА ====================

@app.post("/api/artists", response_model=ArtistResponse, tags=["Артисты"])
def create_artist_profile(
        artist: ArtistCreate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Создание профиля артиста"""
    if current_user.role != "artist":
        raise HTTPException(status_code=403, detail="Только артисты могут создавать профиль артиста")

    # Проверка существования профиля
    existing = db.query(Artist).filter(Artist.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Профиль артиста уже существует")

    db_artist = Artist(
        user_id=current_user.id,
        stage_name=artist.stage_name,
        bio=artist.bio,
        genres=",".join(artist.genres),
        price_min=artist.price_min,
        price_max=artist.price_max
    )
    db.add(db_artist)
    db.commit()
    db.refresh(db_artist)

    return _prepare_artist_response(db_artist)


@app.get("/api/artists/{artist_id}", response_model=ArtistResponse, tags=["Артисты"])
def get_artist_profile(artist_id: int, db: Session = Depends(get_db)):
    """Получение профиля артиста"""
    artist = db.query(Artist).filter(Artist.artist_id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Артист не найден")
    return _prepare_artist_response(artist)


@app.put("/api/artists/{artist_id}", response_model=ArtistResponse, tags=["Артисты"])
def update_artist_profile(
        artist_id: int,
        artist_update: ArtistUpdate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Обновление профиля артиста"""
    artist = db.query(Artist).filter(Artist.artist_id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Артист не найден")

    if artist.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет прав для редактирования")

    update_data = artist_update.dict(exclude_unset=True)
    if "genres" in update_data:
        update_data["genres"] = ",".join(update_data["genres"])

    for key, value in update_data.items():
        setattr(artist, key, value)

    db.commit()
    db.refresh(artist)
    return _prepare_artist_response(artist)


# ==================== Ф3: УПРАВЛЕНИЕ ПРОФИЛЕМ ОРГАНИЗАТОРА ====================

@app.post("/api/organizers", response_model=OrganizerResponse, tags=["Организаторы"])
def create_organizer_profile(
        organizer: OrganizerCreate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Создание профиля организатора"""
    if current_user.role != "organizer":
        raise HTTPException(status_code=403, detail="Только организаторы могут создавать профиль")

    existing = db.query(Organizer).filter(Organizer.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Профиль организатора уже существует")

    db_organizer = Organizer(
        user_id=current_user.id,
        company_name=organizer.company_name,
        description=organizer.description,
        address=organizer.address,
        website=organizer.website
    )
    db.add(db_organizer)
    db.commit()
    db.refresh(db_organizer)

    return db_organizer


@app.get("/api/organizers/{organizer_id}", response_model=OrganizerResponse, tags=["Организаторы"])
def get_organizer_profile(organizer_id: int, db: Session = Depends(get_db)):
    """Получение профиля организатора"""
    organizer = db.query(Organizer).filter(Organizer.organizer_id == organizer_id).first()
    if not organizer:
        raise HTTPException(status_code=404, detail="Организатор не найден")
    return organizer


# ==================== Ф4: ПОИСК И ФИЛЬТРАЦИЯ АРТИСТОВ ====================

@app.get("/api/artists", response_model=List[ArtistResponse], tags=["Артисты"])
def search_artists(
        genre: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        search: Optional[str] = None,
        db: Session = Depends(get_db)
):
    """Поиск и фильтрация артистов"""
    query = db.query(Artist)

    if genre:
        query = query.filter(Artist.genres.contains(genre))

    if price_min:
        query = query.filter(Artist.price_min >= price_min)

    if price_max:
        query = query.filter(Artist.price_max <= price_max)

    if search:
        query = query.filter(
            (Artist.stage_name.contains(search)) | (Artist.bio.contains(search))
        )

    artists = query.all()
    return [_prepare_artist_response(a) for a in artists]


# ==================== Ф5: ПОДАЧА И ОБРАБОТКА ЗАЯВОК ====================

@app.post("/api/bookings", response_model=BookingResponse, tags=["Бронирования"])
def create_booking(
        booking: BookingCreate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Создание заявки на бронирование"""
    if current_user.role != "organizer":
        raise HTTPException(status_code=403, detail="Только организаторы могут создавать заявки")

    # Проверка существования артиста
    artist = db.query(Artist).filter(Artist.artist_id == booking.artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Артист не найден")

    # Получение ID организатора
    organizer = db.query(Organizer).filter(Organizer.user_id == current_user.id).first()
    if not organizer:
        raise HTTPException(status_code=400, detail="Создайте профиль организатора")

    db_booking = Booking(
        event_id=booking.event_id,
        artist_id=booking.artist_id,
        organizer_id=organizer.organizer_id,
        status="pending",
        proposed_price=booking.proposed_price,
        technical_requirements=booking.technical_requirements
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    return db_booking


@app.get("/api/bookings", response_model=List[BookingResponse], tags=["Бронирования"])
def get_bookings(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Получение списка бронирований пользователя"""
    if current_user.role == "artist":
        artist = db.query(Artist).filter(Artist.user_id == current_user.id).first()
        if not artist:
            return []
        return db.query(Booking).filter(Booking.artist_id == artist.artist_id).all()

    elif current_user.role == "organizer":
        organizer = db.query(Organizer).filter(Organizer.user_id == current_user.id).first()
        if not organizer:
            return []
        return db.query(Booking).filter(Booking.organizer_id == organizer.organizer_id).all()

    return []


@app.patch("/api/bookings/{booking_id}", response_model=BookingResponse, tags=["Бронирования"])
def update_booking_status(
        booking_id: int,
        booking_update: BookingUpdate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Обновление статуса бронирования"""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")

    # Проверка прав доступа
    if current_user.role == "artist":
        artist = db.query(Artist).filter(Artist.user_id == current_user.id).first()
        if not artist or booking.artist_id != artist.artist_id:
            raise HTTPException(status_code=403, detail="Нет прав для изменения")

    if booking_update.status:
        booking.status = booking_update.status

    if booking_update.response_deadline:
        booking.response_deadline = booking_update.response_deadline

    db.commit()
    db.refresh(booking)
    return booking


# ==================== Ф7: СИСТЕМА КОММУНИКАЦИИ ====================

@app.post("/api/messages", response_model=MessageResponse, tags=["Сообщения"])
def send_message(
        message: MessageCreate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Отправка сообщения"""
    # Проверка существования получателя
    receiver = db.query(User).filter(User.id == message.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Получатель не найден")

    db_message = Message(
        sender_id=current_user.id,
        receiver_id=message.receiver_id,
        booking_id=message.booking_id,
        content=message.content,
        is_read=False
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    return db_message


@app.get("/api/messages", response_model=List[MessageResponse], tags=["Сообщения"])
def get_messages(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Получение сообщений текущего пользователя"""
    messages = db.query(Message).filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).order_by(Message.sent_at.desc()).all()

    return messages


# ==================== Ф8: РЕЙТИНГ И ОТЗЫВЫ ====================

@app.post("/api/reviews", response_model=ReviewResponse, tags=["Отзывы"])
def create_review(
        review: ReviewCreate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Создание отзыва"""
    # Проверка существования бронирования
    booking = db.query(Booking).filter(Booking.booking_id == review.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")

    if booking.status != "confirmed":
        raise HTTPException(status_code=400, detail="Можно оставлять отзывы только для подтвержденных бронирований")

    db_review = Review(
        booking_id=review.booking_id,
        reviewer_id=current_user.id,
        reviewed_id=review.reviewed_id,
        rating_score=review.rating_score,
        comment=review.comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    # Обновление рейтинга артиста
    if current_user.role == "organizer":
        artist = db.query(Artist).filter(Artist.artist_id == booking.artist_id).first()
        if artist:
            reviews = db.query(Review).join(Booking).filter(
                Booking.artist_id == artist.artist_id
            ).all()
            if reviews:
                avg_rating = sum(r.rating_score for r in reviews) / len(reviews)
                artist.rating = round(avg_rating, 2)
                db.commit()

    return db_review


@app.get("/api/reviews/artist/{artist_id}", response_model=List[ReviewResponse], tags=["Отзывы"])
def get_artist_reviews(artist_id: int, db: Session = Depends(get_db)):
    """Получение отзывов об артисте"""
    reviews = db.query(Review).join(Booking).filter(
        Booking.artist_id == artist_id
    ).all()
    return reviews


# ==================== ГЛАВНАЯ СТРАНИЦА ====================

@app.get("/", tags=["Главная"])
def read_root():
    """Главная страница с информацией об API"""
    return {
        "message": "Добро пожаловать в МузПлатформу API",
        "version": "1.0.0",
        "docs": "/docs",
        "features": [
            "Регистрация и аутентификация пользователей",
            "Управление профилями артистов и организаторов",
            "Поиск и фильтрация артистов",
            "Система бронирования",
            "Внутренние сообщения",
            "Рейтинги и отзывы"
        ]
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8010, reload=True)