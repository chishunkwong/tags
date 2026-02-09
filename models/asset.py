from typing import Optional
from .base import Base, asset_tag_table
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Asset(Base):
    __tablename__ = "asset"
    id: Mapped[int] = mapped_column(primary_key=True)
    # The content of the asset is stored somewhere else, on disk or s3, etc
    path: Mapped[str] = mapped_column(index=True)
    favorite: Mapped[bool] = mapped_column(index=True, nullable=True)
    bookmark: Mapped[bool] = mapped_column(index=True, nullable=True)
    #Intentionally use two differnt ways for nullable, just to learn
    should_delete: Mapped[Optional[bool]]
    tags = relationship('Tag', order_by='Tag.name', secondary=asset_tag_table, passive_deletes=True)

    def to_dict(self):
        return {
            'id': self.id,
            'path': self.path,
            'favorite': self.favorite,
            'bookmark': self.bookmark,
            'should_delete': self.should_delete,
            'tag_ids': [tag.id for tag in self.tags]
        }