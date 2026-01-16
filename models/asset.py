from .base import Base, asset_tag_table
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Asset(Base):
    __tablename__ = "asset"
    id: Mapped[int] = mapped_column(primary_key=True)
    # The content of the asset is stored somewhere else, on disk or s3, etc
    path: Mapped[str]
    favorite: Mapped[bool]
    tags = relationship('Tag', secondary=asset_tag_table)