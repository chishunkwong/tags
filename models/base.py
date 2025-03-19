from sqlalchemy import Table
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

asset_tag_table = Table(
    "asset_tag",
    Base.metadata,
    Column("asset_id", ForeignKey("asset.id"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)