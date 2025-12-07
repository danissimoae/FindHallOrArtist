from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database.database import Base

class UserRole(str, enum.Enum):
    artist = "artist"
    organizer = "organizer"
    admin = "admin"


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    declined = "declined"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), nullable=False)

    # Связи
    artist_profile = relationship("Artist", back_populates="user", uselist=False)
    organizer_profile = relationship("Organizer", back_populates="user", uselist=False)
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    reviews_written = relationship("Review", foreign_keys="Review.reviewer_id", back_populates="reviewer")
    reviews_received = relationship("Review", foreign_keys="Review.reviewed_id", back_populates="reviewed")


class Artist(Base):
    __tablename__ = "artists"

    artist_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    stage_name = Column(String, nullable=False)
    bio = Column(Text, nullable=True)
    genres = Column(String, nullable=True)  # Хранится как строка через запятую
    price_min = Column(Float, nullable=True)
    price_max = Column(Float, nullable=True)
    rating = Column(Float, default=0.0)

    # Связи
    user = relationship("User", back_populates="artist_profile")
    bookings = relationship("Booking", back_populates="artist")


class Organizer(Base):
    __tablename__ = "organizers"

    organizer_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String, nullable=True)
    website = Column(String, nullable=True)
    rating = Column(Float, default=0.0)

    # Связи
    user = relationship("User", back_populates="organizer_profile")
    bookings = relationship("Booking", back_populates="organizer")


class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, nullable=True)  # Связь с событием (пока не реализовано)
    artist_id = Column(Integer, ForeignKey("artists.artist_id"), nullable=False)
    organizer_id = Column(Integer, ForeignKey("organizers.organizer_id"), nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.pending)
    proposed_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    response_deadline = Column(DateTime, nullable=True)
    technical_requirements = Column(Text, nullable=True)

    # Связи
    artist = relationship("Artist", back_populates="bookings")
    organizer = relationship("Organizer", back_populates="bookings")
    reviews = relationship("Review", back_populates="booking")
    messages = relationship("Message", back_populates="booking")


class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating_score = Column(Float, nullable=False)  # От 1.0 до 5.0
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_verified = Column(Boolean, default=False)

    # Связи
    booking = relationship("Booking", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_written")
    reviewed = relationship("User", foreign_keys=[reviewed_id], back_populates="reviews_received")


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"), nullable=True)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    # Связи
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")
    booking = relationship("Booking", back_populates="messages")