from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import String

class Base(DeclarativeBase):
    pass

class Game(Base):
    __tablename__ = "games"
    gameId: Mapped[int] = mapped_column('appid', primary_key=True)
    gameName: Mapped[str] = mapped_column('name', String(200))