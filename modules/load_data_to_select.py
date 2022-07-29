from modules.models import Header
from sqlalchemy.sql import select
import pandas as pd
import datetime
from collections import ChainMap


def get_header(r):
    sql = select(Header)
    try:
        df = pd.read_sql(sql, r)
        name_id, measurement_name = df['name_id'][0], df['measurement'][0]
    except (Exception,):
        name_id, measurement_name = 'name_id', 'measurement'
    return name_id, measurement_name


def get_database_information(r):
    size_num_table = """SELECT count(*) FROM examination_numerical"""
    size_date_table = """SELECT count(*) FROM examination_date"""
    size_cat_table = """SELECT count(*) FROM examination_categorical"""
    try:
        size_num_tab, size_date_tab, size_cat_tab = pd.read_sql(size_num_table, r), pd.read_sql(size_date_table, r), \
                                                    pd.read_sql(size_cat_table, r)
        size_num_tab, size_date_tab, size_cat_tab = \
            size_num_tab.iloc[0]['count'], size_date_tab.iloc[0]['count'], \
            size_cat_tab.iloc[0]['count']
    except (Exception,):
        size_num_tab, size_date_tab, size_cat_tab = 0, 0, 0
    return size_num_tab, size_date_tab, size_cat_tab


def get_date(r):
    sql = """ SELECT min("date"),max("date") FROM examination_numerical """
    try:
        df = pd.read_sql(sql, r)
        start_date = datetime.datetime.strptime(df['min'][0], '%Y-%m-%d').timestamp() * 1000
        end_date = datetime.datetime.strptime(df['max'][0], '%Y-%m-%d').timestamp() * 1000
    except (Exception,):
        now = datetime.datetime.now()
        start_date = datetime.datetime.timestamp(now - datetime.timedelta(days=365.24 * 100)) * 1000
        end_date = datetime.datetime.timestamp(now) * 1000
    return start_date, end_date


def patient(r):
    sql = """SELECT * FROM Patient"""
    try:
        df = pd.read_sql(sql, r)
        return df['name_id'], None
    except (Exception,):
        return None, "Problem with load data from database"


def get_entities(r):
    all_entities = """SELECT key,type,description,synonym FROM name_type ORDER BY orders """
    try:
        entities = pd.read_sql(all_entities, r)
        entities = entities.replace([None], ' ')
        num_entities = entities[entities['type'] == 'Double'].drop(columns=['type'])
        cat_entities = entities[entities['type'] == 'String'].drop(columns=['type'])
        date_entities = entities[entities['type'] == 'Date'].drop(columns=['type'])
        entities = entities.drop(columns=['type'])

        all_num_entities, all_cat_entities = num_entities.to_dict('index'), cat_entities.to_dict('index')
        all_date_entities, all_entities = date_entities.to_dict('index'), entities.to_dict('index')
        length = (str(len(num_entities)), str(len(cat_entities)), str(len(date_entities)))
    except (Exception,):
        all_entities, all_num_entities, all_cat_entities, all_date_entities, length = {}, {}, {}, {}, ('0', '0', '0')
    return all_entities, all_num_entities, all_cat_entities, all_date_entities, length


def min_max_value_numeric_entities(r):
    min_max = """SELECT key,max(value),min(value) FROM examination_numerical GROUP BY key """
    try:
        df_min_max = pd.read_sql(min_max, r)
        df_min_max = df_min_max.set_index('key')
        df_min_max = df_min_max.to_dict('index')
    except (Exception,):
        df_min_max = pd.DataFrame()
        df_min_max = df_min_max.to_dict('index')
    return df_min_max


def get_subcategories_from_categorical_entities(r):
    all_subcategories = """SELECT key,array_agg(distinct value) as value FROM examination_categorical 
    WHERE key in (select key from name_type where type ='String') Group by key 
                            ORDER by key """
    try:
        df = pd.read_sql(all_subcategories, r)
        df.set_index('key', inplace=True)
        df_dict = df.to_dict()
    except (Exception,):
        df_dict = {}
    return df_dict


def get_measurement(r):
    sql = """SELECT DISTINCT measurement:: int FROM examination_numerical ORDER BY measurement """
    try:
        df = pd.read_sql(sql, r)
        df['measurement'] = df['measurement'].astype(str)
        # show all hide measurement selector when was only one measurement for all entities
        if len(df['measurement']) < 2:
            block_measurement = 'none'
        else:
            block_measurement = 'block'
    except (Exception,):
        df = ["No data"]
        block_measurement = 'none'
    return df['measurement'], block_measurement
