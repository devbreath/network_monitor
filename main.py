import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_compress import Compress

from db import db_name, database, Measurements, Latency, Wireless, LatencyView
from misc import zip_db, PerfSingleton

from v1.endpoints import api as api_v1

app = Flask(__name__)

# TODO: implement GET for /v1/wireless
# TODO: dump income request data to filesystem in case of error
# TODO: add token for each source/service
# TODO: 12 factor app
# TODO: write implementation to method anomality. It should check that all call of WS was with out failtures

COMPRESS_MIMETYPES = ['text/html', 'text/css', 'text/xml', 'application/json', 'application/javascript']
COMPRESS_LEVEL = 6
COMPRESS_BR_LEVEL = 6
COMPRESS_MIN_SIZE = 500


# def make_dump(iv_date: str, iv_data: {}, e: Exception):
#     str_uuid = f"{iv_date}_{get_uuid()}.json"
#     dump = dict()
#     dump['exception'] = str(e)
#     dump['request_data'] = iv_data
#     with open(str_uuid, "w") as fp:
#         json.dump(dump, fp)
#     print(f"Found duplicates! Dump in file {str_uuid}")
#     return abort(400)


@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'

    perf = PerfSingleton.get()
    s_timing = ''
    for (mn, mv) in perf.metric.items():
        s_timing = s_timing + f"{mn}; dur={mv}, "
    perf.clear()
    response.headers.add("Server-Timing", s_timing)
    return response


def schedule_jobs(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=make_db_backup, trigger="interval", hours=1)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    return


def configure_app(app):
    # app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    Compress(app)
    app.config['JSON_SORT_KEYS'] = False
    pass


def make_db_backup():
    from datetime import datetime
    import os
    (path, filename) = os.path.split(os.path.abspath(db_name))
    arch_dir = f"{path}\\backup"
    if not os.path.isdir(arch_dir):
        os.mkdir(arch_dir)

    now = datetime.now()
    ids = now.strftime("%Y_%H")
    dest_name = f'{arch_dir}\\{filename}_{ids}.zip'
    print(f"Make backup from {db_name} to {dest_name}")
    zip_db(db_name, dest_name)


def init_db():
    database.connect()
    database.create_tables([Measurements, Latency, Wireless])
    LatencyView.create_view_latency()
    LatencyView.create_view_latency_day()
    LatencyView.create_view_latency_anomality()
    database.close()


def start_app():
    init_db()
    schedule_jobs(app)
    configure_app(app)
    app.register_blueprint(api_v1, url_prefix='/v1')
    app.run(debug=False, host='0.0.0.0', port=50000)


if __name__ == "__main__":
    start_app()
