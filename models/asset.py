from typing import Optional
from .base import Base, asset_tag_table
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Asset(Base):
    __tablename__ = "asset"
    id: Mapped[int] = mapped_column(primary_key=True)
    # The content of the asset is stored somewhere else, on disk or s3, etc
    path: Mapped[str]
    favorite: Mapped[bool] = mapped_column(index=True, nullable=True)
    bookmark: Mapped[bool] = mapped_column(index=True, nullable=True)
    #Intentionally use two differnt ways for nullable, just to learn
    should_delete: Mapped[Optional[bool]]
    tags = relationship('Tag', secondary=asset_tag_table)