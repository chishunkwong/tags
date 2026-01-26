from .base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship

class TagGroup(Base):
    __tablename__ = "tag_group"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    ui_addable: Mapped[bool]
    multiselect: Mapped[bool]
    show_size: Mapped[int]
    tag_per_line: Mapped[bool] = mapped_column(default=False, nullable=True)

    tags = relationship("Tag", order_by='Tag.name', back_populates="tag_group")