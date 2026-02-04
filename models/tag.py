from .base import Base
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey

class Tag(Base):
    __tablename__ = "tag"
    id: Mapped[int] = mapped_column(primary_key=True)
    tag_group_id: Mapped[int] = mapped_column(ForeignKey("tag_group.id"))
    name: Mapped[str]

    tag_group = relationship("TagGroup", back_populates="tags")

    __table_args__ = (
        UniqueConstraint('tag_group_id', 'name', name='uix_tag_group_name'),
    )