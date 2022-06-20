from sqlalchemy import Column, Integer, String, Date, Time, Numeric, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Header(Base):
    __tablename__ = "header"
    name_id = Column(String, primary_key=True)
    measurement = Column(String)


class NameType(Base):
    __tablename__ = "name_type"
    orders = Column(Integer)
    key = Column(String, primary_key=True)
    type = Column(String)
    synonym = Column(String)
    description = Column(String)
    unit = Column(String)
    show = Column(String)


class TableNumerical(Base):
    __tablename__ = "examination_numerical"
    id = Column(Integer, primary_key=True)
    name_id = Column(String)
    case_id = Column(String)
    measurement = Column(Integer)
    date = Column(String)
    time = Column(String)
    key = Column(String, ForeignKey('name_type.key'))
    value = Column(Numeric)
    __table_args__ = (Index('idx_key_num', 'key'), Index('idx_name_id_num', 'name_id'))


class TableCategorical(Base):
    __tablename__ = "examination_categorical"
    id = Column(Integer, primary_key=True)
    name_id = Column(String)
    case_id = Column(String)
    measurement = Column(Integer)
    date = Column(String)
    time = Column(String)
    key = Column(String, ForeignKey('name_type.key'))
    value = Column(String)
    __table_args__ = (Index('idx_key_cat', 'key'),Index('idx_name_id_cat', 'name_id'))


class TableDate(Base):
    __tablename__ = "examination_date"
    id = Column(Integer, primary_key=True)
    name_id = Column(String)
    case_id = Column(String)
    measurement = Column(Integer)
    date = Column(String)
    time = Column(String)
    key = Column(String, ForeignKey('name_type.key'))
    value = Column(Date)
    __table_args__ = (Index('idx_key_date', 'key'), Index('idx_name_id_date', 'name_id'))


def drop_tables(rdb):
    Base.metadata.drop_all(rdb)


def create_tables(rdb):
    Base.metadata.create_all(rdb)


