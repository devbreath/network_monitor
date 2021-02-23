from jsonify_misc import jsonify
from misc import PerfSingleton, PerfFacade, conv_params2dbfields
from db import database, Measurements, Wireless, Latency
import urllib
from flask import Blueprint, request, Response, abort
import re
import socket
from flask_timing import timing

api = Blueprint('api', __name__)


@api.route('/speed', methods=['GET'])
def get():
    # Select data from DB
    perf = PerfSingleton.get()
    perf.start(PerfFacade.DB)
    query = Measurements.select(Measurements.source).distinct().dicts()
    result = list(query)
    perf.finish()

    # Make response with JSON
    perf.start(PerfFacade.JSON)
    json_resp = jsonify(result)
    perf.finish()
    return json_resp


@api.route('/speed/<string:source>/<string:begda>-<string:endda>', methods=['GET'])
@timing
def get_source_period(source: str, begda: str = '19000101', endda: str = '99991231') -> object:
    perf = PerfSingleton.get()
    # Parse request parameters
    perf.start(PerfFacade.PARAMS)
    try:
        fields_list = conv_params2dbfields(request.args.get('fields'), Measurements)
    except KeyError:
        abort(400)
    perf.finish()

    # Select data from DB
    perf.start(PerfFacade.DB)
    query = Measurements.select(*fields_list).where(
        (Measurements.source == source) & (begda <= Measurements.date) & (Measurements.date <= endda)
    ).distinct().dicts()
    perf.finish()

    # Make response with JSON
    perf.start(PerfFacade.JSON)
    result = list(query)
    json_resp = jsonify(result)
    perf.finish()

    return json_resp


@api.route('/speed/<string:source>', methods=['GET'])
def get_source(source: str = ''):
    return get_source_period(source=source)


@api.route('/speed', methods=['POST'])
def create():
    # {"source":"CCRU","rx":15,"tx":40,"date":"20200401","time":"120000","localCPU":50,"remoteCPU":23}

    data = request.get_json(force=True)

    # database.connect()
    meas = Measurements.create(
        source=data["source"],
        date=data["date"],
        time=str(data["time"]).replace(':', ''),
        send=data["tx"],
        receive=data["rx"],
        localCPU=data["localCPU"] if "localCPU" in data else 0,
        remoteCPU=data["remoteCPU"] if "remoteCPU" in data else 0
    )
    meas.save()
    database.commit()
    # database.close()

    return f'OK'


@api.route('/anomality/<string:source>')
def anomality(source: str):
    # # get timestamps from db
    # database.connect()
    # query = Measurements.select(Measurements.date, Measurements.time).where(
    #         (Measurements.source == source)
    #     ).distinct().dicts()
    # str_array = list(query)
    # database.close()
    #
    # # calc diff
    # diff_array = conv_str2time(str_array)
    # if get_std(diff_array) > 120:
    #     abort(400)
    #
    return f'Ok'


@api.route('/wireless', methods=['POST'])
def wireless_post():
    data = request.get_json(force=True)
    ldate = data["date"]
    ltime = data["time"]

    try:
        records = [Wireless(
            source=item["source"],
            date=ldate,
            time=ltime,
            ap=item["AP"],
            mac=item["MAC"],
            lastip=item["Last IP"],
            dnsname=item["DNSname"],
            rx=item["RX"],
            tx=item["TX"],
            uptime=item["Uptime"],
            lastact=item["LastACT"],
            signalstrength=item["SignalStrength"],
            snr=item["SNR"],
            ccq=item["TX/RX-CCQ"],
            throughput=item["PThroughput"]) for item in data["items"]]
        with database.atomic():
            Wireless.bulk_create(records, batch_size=10)
        database.commit()
    except Exception as e:
        # make_dump(ldate, data, e)
        raise e
    return 'Ok'


@api.route('/ping', methods=['POST'])
def ping_post_parse():
    # Parse request
    str_data = str(request.data)
    pattern = '\[source=\'(?P<source>\S+)\'\s+date=\'(?P<dt>\d+)\'\s+time=\'(?P<tm>[\d\:]+)\'\s+host=\'(?P<host>\S+)\'\][\S\s]+min-rtt=(?P<min>\d+)[\S\s]+avg-rtt=(?P<avg>\d+)[\S\s]+max-rtt=(?P<max>\d+)'
    match = re.search(pattern, str_data)
    if not match:
        abort(400)

    try:
        ip = socket.gethostbyname(match.group('host'))
    except socket.gaierror:
        ip = socket.getaddrinfo(match.group('host'), None, socket.AF_INET6)[0][4][0]

    # Database
    record = Latency.create(
        source=match.group('source'),
        date=match.group('dt'),
        time=str(match.group('tm')).replace(':', ''),
        ip=ip,
        dnsname=match.group('host'),
        minrtt=match.group('min'),
        maxrtt=match.group('max'),
        avgrtt=match.group('avg')
    )
    record.save()
    database.commit()
    # database.close()

    return f'Ok'


@api.route('/ping', methods=['GET'])
@timing
def ping_list():
    perf = PerfSingleton.get()
    # Select data from DB
    perf.start(PerfFacade.DB)
    query = Latency.select(Latency.dnsname).distinct().dicts()
    result = list(query)
    perf.finish()
    # Make response with JSON
    perf.start(PerfFacade.JSON)
    json_resp = jsonify(result)
    perf.finish()
    return json_resp


@api.route('/ping/<string:dnsname>', methods=['GET'])
@timing
def ping_get(dnsname: str):
    perf = PerfSingleton.get()
    # Parse input parameters
    perf.start(PerfFacade.PARAMS)
    try:
        fields_list = conv_params2dbfields(request.args.get('fields'), Latency)
    except KeyError:
        abort(400)
    perf.finish()
    # Select data from DB
    perf.start(PerfFacade.DB)
    query = Latency.select(*fields_list) \
        .where(Latency.dnsname == dnsname) \
        .order_by(Latency.date, Latency.time) \
        .distinct().dicts()
    result = list(query)
    perf.finish()
    # Make response with JSON
    perf.start(PerfFacade.JSON)
    json_resp = jsonify(result)
    perf.finish()

    return json_resp


@api.route('/health', methods=['HEAD', 'GET'])
def health():
    query = Latency.select().limit(1)
    result = query.count()
    if result != 1:
        abort(503)
    return f'Ok'


@api.route('/http_img', methods=['GET'])
@timing
def proxy_get():
    def generator(req):
        # req = urllib.request.urlopen(url)
        if req.getcode() == 200:
            yield req.read()

    perf = PerfSingleton.get()
    perf.start(PerfFacade.PARAMS)
    url = request.args.get('src')
    lv_index = str(url).find('192.168.')
    if lv_index == -1 or lv_index > 10:
        abort(403)
    perf.finish()
    perf.start('download_header')
    req = urllib.request.urlopen(url)
    perf.finish()
    return Response(generator(req), mimetype=req.headers['content-type'])
    # url = request.args.get('src')
    # req = requests.get(url, stream=True)
    # return Response(stream_with_context(req.iter_content()), content_type=req.headers['content-type'])


# import requests
# import aiohttp as aiohttp
# import asyncio

# @app.route('/use-external-api', methods=['GET'])
# def use_external_api():
#    response = yield from aiohttp.request(
#        'GET', 'https://api.ccru-monitor.duckdns.org:8888/v1/speed')
#    data = yield from response.read()
#    return 'Ok'
