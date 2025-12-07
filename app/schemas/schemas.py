from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums
class UserRole(str, Enum):
    artist = "artist"
    organizer = "organizer"
    admin = "admin"


class BookingStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    declined = "declined"
    cancelled = "cancelled"


# ==================== USER SCHEMAS ====================

class UserBase(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# ==================== ARTIST SCHEMAS ====================

class ArtistBase(BaseModel):
    stage_name: str = Field(..., min_length=2, max_length=100)
    bio: Optional[str] = Field(None, max_length=2000)
    genres: List[str] = Field(default_factory=list)
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)

    @validator('price_max')
    def validate_price_range(cls, v, values):
        if v is not None and 'price_min' in values and values['price_min'] is not None:
            if v < values['price_min']:
                raise ValueError('price_max должен быть больше или равен price_min')
        return v


class ArtistCreate(ArtistBase):
    pass


class ArtistUpdate(BaseModel):
    stage_name: Optional[str] = Field(None, min_length=2, max_length=100)
    bio: Optional[str] = Field(None, max_length=2000)
    genres: Optional[List[str]] = None
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)


class ArtistResponse(ArtistBase):
    artist_id: int
    user_id: int
    rating: float

    class Config:
        from_attributes = True


class ArtistSearch(BaseModel):
    genre: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    search: Optional[str] = None


# ==================== ORGANIZER SCHEMAS ====================

class OrganizerBase(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    address: Optional[str] = None
    website: Optional[str] = None


class OrganizerCreate(OrganizerBase):
    pass


class OrganizerUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    address: Optional[str] = None
    website: Optional[str] = None


class OrganizerResponse(OrganizerBase):
    organizer_id: int
    user_id: int
    rating: float

    class Config:
        from_attributes = True


# ==================== BOOKING SCHEMAS ====================

class BookingBase(BaseModel):
    artist_id: int
    proposed_price: Optional[float] = Field(None, ge=0)
    technical_requirements: Optional[str] = Field(None, max_length=2000)


class BookingCreate(BookingBase):
    event_id: Optional[int] = None
    response_deadline: Optional[datetime] = None


class BookingUpdate(BaseModel):
    status: Optional[BookingStatus] = None
    response_deadline: Optional[datetime] = None


class BookingResponse(BaseModel):
    booking_id: int
    event_id: Optional[int]
    artist_id: int
    organizer_id: int
    status: BookingStatus
    proposed_price: Optional[float]
    created_at: datetime
    updated_at: datetime
    response_deadline: Optional[datetime]
    technical_requirements: Optional[str]

    class Config:
        from_attributes = True


# ==================== REVIEW SCHEMAS ====================

class ReviewBase(BaseModel):
    booking_id: int
    reviewed_id: int
    rating_score: float = Field(..., ge=1.0, le=5.0)
    comment: Optional[str] = Field(None, max_length=1000)


class ReviewCreate(ReviewBase):
    pass


class ReviewResponse(ReviewBase):
    review_id: int
    reviewer_id: int
    created_at: datetime
    is_verified: bool

    class Config:
        from_attributes = True


# ==================== MESSAGE SCHEMAS ====================

class MessageBase(BaseModel):
    receiver_id: int
    content: str = Field(..., min_length=1, max_length=2000)
    booking_id: Optional[int] = None


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    message_id: int
    sender_id: int
    sent_at: datetime
    is_read: bool

    class Config:
        from_attributes = True