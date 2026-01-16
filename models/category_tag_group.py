from .base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import ForeignKey

class CategoryTagGroup(Base):
    __tablename__ = "category_tag_group"
    name: Mapped[str] = mapped_column(primary_key=True)
    tag_group_id: Mapped[int] = mapped_column(ForeignKey("tag_group.id"), primary_key=True)
    display_order: Mapped[int]