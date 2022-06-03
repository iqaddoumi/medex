from flask import Flask, send_file, request, redirect, session, g, jsonify
import requests
from modules.import_scheduler import Scheduler
from modules.database_sessions import DatabaseSessionFactory
import modules.load_data_postgre as ps
from flask_cors import CORS
from db import connect_db, close_db
import pandas as pd
import os
import io
from flask import send_from_directory
from serverside.serverside_table import ServerSideTable


# create the application object
app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)

with app.app_context():
    connect_db()
    rdb = g.db


@app.teardown_appcontext
def teardown_db(exception):
    close_db()


factory = DatabaseSessionFactory(rdb)


def collect_data_server_side(data_sample, columns):
    return ServerSideTable(request, data_sample, columns).output_result()


# I have to remove this
class DataStore:

    case_ids = []
    table_case_ids = None
    df = None
    column = None
    dict = None

    # for table browser server side
    table_schema = None
    table_browser_column = None
    table_browser_entities = None
    table_browser_what_table = None
    table_browser_column2 = None

    year = None
    new_table = pd.DataFrame()
    new_table_dict = None
    new_table_schema = None

    # for download
    csv = None
    csv_new_table = None

    information = None


data = DataStore()


def check_for_env(key: str, default=None, cast=None):
    if key in os.environ:
        if cast:
            return cast(os.environ.get(key))
        return os.environ.get(key)
    return default


# date and hours to import data
day_of_week = check_for_env('IMPORT_DAY_OF_WEEK', default='mon-sun')
hour = check_for_env('IMPORT_HOUR', default=5)
minute = check_for_env('IMPORT_MINUTE', default=5)


# Import data using function scheduler from package modules
if os.environ.get('IMPORT_DISABLED') is None:
    scheduler = Scheduler(rdb, day_of_week=day_of_week, hour=hour, minute=minute)
    scheduler.start()
    scheduler.stop()


# get all numeric and categorical entities from database
Name_ID, measurement_name = ps.get_header(rdb)
size_num_tab, size_date_tab, size_cat_tab = ps.get_database_information(rdb)
start_date, end_date = ps.get_date(rdb)
all_patient = ps.patient(rdb)
all_entities, all_num_entities, all_cat_entities, all_date_entities,  all_num_entities_list, all_cat_entities_list, all_date_entities_list, all_entities_list = ps.get_entities(rdb)
df_min_max = ps.min_max_value_numeric_entities(rdb)
all_subcategory_entities = ps.get_subcategories_from_categorical_entities(rdb)
all_measurement, block_measurement = ps.get_measurement(rdb)



Meddusa = 'none'
try:
    EXPRESS_MEDEX_MEDDUSA_URL = os.environ['EXPRESS_MEDEX_MEDDUSA_URL']
    MEDDUSA_URL = os.environ['MEDDUSA_URL']
    Meddusa = 'block'
except (Exception,):
    EXPRESS_MEDEX_MEDDUSA_URL = 'http://localhost:3500'
    MEDDUSA_URL = 'http://localhost:3000'
    Meddusa = 'none'


# favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='vnd.microsoft.icon')


# information about database
@app.context_processor
def data_information():

    database_name = os.environ['POSTGRES_DB']
    database = '{} data'.format(database_name)

    len_numeric = 'number of numerical entities: ' + str(len(all_num_entities_list))
    size_numeric = 'the size of the numeric table: ' + str(size_num_tab) + ' rows'
    len_categorical = 'number of categorical entities: ' + str(len(all_cat_entities_list))
    size_categorical = 'the size of the categorical table: ' + str(size_cat_tab) + ' rows'

    return dict(database_information=(database, len_numeric, size_numeric, len_categorical, size_categorical),
                entities=(all_num_entities, all_cat_entities, all_subcategory_entities, all_date_entities),
                measurement=(all_measurement, '{}'.format(measurement_name), block_measurement),
                df_min_max=df_min_max,
                meddusa=(Meddusa, MEDDUSA_URL),
                limit_offset=(True, 1000, 0),
                )


# information about database
@app.context_processor
def message_count():

    case = session.get('case_ids')
    if case is None or case == 'No':
        data.case_ids = []
        case_display = 'none'
        session['case_ids'] = 'No'
    else:
        case_display = 'block'

    session['start_date'] = start_date
    session['end_date'] = end_date
    session['change_date'] = 0

    if start_date == end_date:
        date_block = 'none'
    else:
        date_block = 'block'

    return dict(date_block=date_block,
                case_display=case_display,
                )


# import a Blueprint
from url_handlers.data import data_page
from url_handlers.basic_stats import basic_stats_page
from url_handlers.histogram import histogram_page
from url_handlers.boxplot import boxplot_page
from url_handlers.scatter_plot import scatter_plot_page
from url_handlers.barchart import barchart_page
from url_handlers.heatmap import heatmap_plot_page
from url_handlers.logout import logout_page
from url_handlers.tutorial import tutorial_page
from url_handlers.calculator import calculator_page

# register blueprints here:\
app.register_blueprint(data_page)
app.register_blueprint(logout_page)
app.register_blueprint(tutorial_page)
app.register_blueprint(basic_stats_page)
app.register_blueprint(histogram_page)
app.register_blueprint(boxplot_page)
app.register_blueprint(scatter_plot_page)
app.register_blueprint(barchart_page)
app.register_blueprint(heatmap_plot_page)
app.register_blueprint(calculator_page)


@app.route('/_session', methods=['GET'])
def get_cases():
    session_id = request.args.get('sessionid')
    session_id_json = {"session_id": "{}".format(session_id)}
    session['session_id'] = session_id
    cases_get = requests.post(EXPRESS_MEDEX_MEDDUSA_URL + '/result/cases/get', json=session_id_json)
    case_ids = cases_get.json()
    data.case_ids = case_ids['cases_ids']
    ps.create_temp_table_case_id(case_ids['cases_ids'], rdb)
    data.table_case_ids = pd.DataFrame(case_ids['cases_ids'], columns=["Case_ID"]).to_csv(index=False)

    session['case_ids'] = 'Yes'
    return redirect('/')


# Direct to Data browser website during opening the program.
@app.route('/', methods=['GET'])
def login_get():
    # get selected entities
    session['session_id'] = os.urandom(10)
    a = factory.get_session(session.get('session_id'))

    session['date_update'] = {'start': start_date, 'end': end_date, 'update': 0}
    session['limit_offset'] = {'limit': 10000, 'offset': 0, 'selected': True}
    session['filter'] = {'categorical_filter': None, 'numerical_filter_name': None, 'numerical_filter_from': None,
                         'numerical_filter_to': None, 'numerical_filter_min': None, 'numerical_filter_get': None,
                         'update': '0,0'}

    if session.get('case_ids') is None or session.get('case_ids') == 'No':
        session['case_ids'] = 'No'
    else:
        session['case_ids'] = 'Yes'
    return redirect('/data')


@app.route('/filtering', methods=['POST', 'GET'])
def filter_data():
    if request.is_json:
        qtc_data = request.get_json()
        print('done',qtc_data)


    results = {'processed': 'true'}
    return jsonify(results)


@app.route("/download/<path:filename>", methods=['GET', 'POST'])
def download(filename):
    if filename == 'data.csv':
        csv = data.csv
    elif filename == 'case_ids.csv':
        csv = data.table_case_ids
    else:
        csv = ''
    # Create a string buffer
    buf_str = io.StringIO(csv)

    # Create a bytes buffer from the string buffer
    buf_byt = io.BytesIO(buf_str.read().encode("utf-8"))
    # Return the CSV data as an attachment
    return send_file(buf_byt,
                     mimetype="text/csv",
                     as_attachment=True,
                     attachment_filename=filename)


def main():
    return app
