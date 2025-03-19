from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship

class TagGroup(Base):
    __tablename__ = "tag_group"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    tags = relationship("Tag", back_populates="tag_group")