from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = 'users'

    user_phone = Column(String(50), primary_key=True)
    user_name = Column(String(80), nullable=False)
    records = relationship("Record")

    def __repr__(self):
        return '<Post %r>' % self.user_name


class Record(Base):
    __tablename__ = 'records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    price = Column(Integer, nullable=False)
    date = Column(String(10), nullable=False)
    time = Column(String(5), nullable=False)
    user_phone = Column(String(50), ForeignKey('users.user_phone'))
    confirmed = Column(Boolean, default=False)
