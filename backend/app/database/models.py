from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ContractorRow(Base):
    __tablename__ = "contractors"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    anon_name: Mapped[str] = mapped_column(String(255), nullable=False)
    categories: Mapped[list[str]] = mapped_column(ARRAY(String(120)), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    city_imputed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False)
    price_from_kzt: Mapped[int] = mapped_column(Integer, nullable=False)
    price_imputed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    event_formats: Mapped[list[str]] = mapped_column(ARRAY(String(120)), nullable=False)
    languages: Mapped[list[str]] = mapped_column(ARRAY(String(80)), nullable=False)
    max_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    busy_dates: Mapped[list[date]] = mapped_column(ARRAY(Date), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

