from sqlalchemy import Table, func
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

Base = declarative_base()

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=True)


asset_tag_table = Table(
    "asset_tag",
    Base.metadata,
    Column("asset_id", ForeignKey("asset.id", ondelete='CASCADE'), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)