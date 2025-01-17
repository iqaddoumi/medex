from datetime import datetime
from medex.dto.entity import EntityType
from medex.services.database_info import DatabaseInfoService
from medex.database_schema import NameType, TableCategorical, TableNumerical, Patient, TableDate
# noinspection PyUnresolvedReferences
from tests.fixtures.db_session import db_session


def test_empty_database(db_session):
    service = DatabaseInfoService(db_session)
    result = service.get()
    assert result.number_of_patients == 0
    assert result.number_of_numerical_entities == 0
    assert result.number_of_categorical_entities == 0
    assert result.number_of_date_entities == 0
    assert result.number_of_numerical_data_items == 0
    assert result.number_of_categorical_data_items == 0
    assert result.number_of_date_data_items == 0


def test_simple_database(db_session):
    db_session.add_all([
        Patient(name_id='nn', case_id='1'),
        NameType(key='n1', type=str(EntityType.NUMERICAL.value)),
        NameType(key='n2', type=str(EntityType.NUMERICAL.value)),
        NameType(key='c1', type=str(EntityType.CATEGORICAL.value)),
        NameType(key='c2', type=str(EntityType.CATEGORICAL.value)),
        NameType(key='c3', type=str(EntityType.CATEGORICAL.value)),
        NameType(key='d1', type=str(EntityType.DATE.value)),
        TableNumerical(key='n1', value=1.1),
        TableNumerical(key='n1', value=2.1),
        TableNumerical(key='n1', value=3.1),
        TableCategorical(key='c1', value='x'),
        TableCategorical(key='c1', value='x'),
        TableDate(key='d1', value=datetime(year=1970, month=1, day=1)),
    ])
    service = DatabaseInfoService(db_session)
    result = service.get()
    assert result.number_of_patients == 1
    assert result.number_of_numerical_entities == 2
    assert result.number_of_categorical_entities == 3
    assert result.number_of_date_entities == 1
    assert result.number_of_numerical_data_items == 3
    assert result.number_of_categorical_data_items == 2
    assert result.number_of_date_data_items == 1