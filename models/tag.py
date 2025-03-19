from .base import Base
from .tag_group import TagGroup
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey

class Tag(Base):
    __tablename__ = "tag"
    id: Mapped[int] = mapped_column(primary_key=True)
    tag_group_id: Mapped[int] = mapped_column(ForeignKey("tag_group.id"))
    name: Mapped[str]

    tag_group = relationship("TagGroup", back_populates="tags")