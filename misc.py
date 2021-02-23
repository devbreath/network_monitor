from datetime import datetime
# import pandas as pd
from uuid import uuid4
import zipfile
import time
from db import BaseModel


def conv_params2dbfields(param_fields: str, otable: BaseModel) -> list:
    str_fields = param_fields
    if str_fields is not None:
        fields = str_fields.split(',')
    else:
        fields = []
    fields_list = []
    for fieldname in fields:
        fields_list.append(otable._meta.fields[fieldname])
    if len(fields_list) == 0:
        fields_list = otable._meta.sorted_fields
    return fields_list


def conv_str2time(in_array: []) -> []:
    out_array = []
    try:
        prev_time = datetime.strptime(f'{in_array[0]["date"]} {in_array[0]["time"]}', '%Y%m%d %H%M%S')
    except Exception as e:
        pass
    for item in in_array[1::1]:
        curr_time = datetime.strptime(f'{item["date"]} {item["time"]}', '%Y%m%d %H%M%S')
        out_array.append(curr_time - prev_time)
        prev_time = curr_time
    return out_array


# def get_std(in_array: []):
#     df = pd.DataFrame(in_array)
#     return df.std()[0].seconds


def get_uuid():
    return str(uuid4())


def zip_db(db_name, zip_name):
    with zipfile.ZipFile(zip_name, mode='w', compression=zipfile.ZIP_DEFLATED) as z_out:
        z_out.write(db_name)
    return


class PerfMetric(object):
    def __init__(self):
        self._start_time = 0
        self.start()

    def start(self):
        self._start_time = time.time()

    def finish(self):
        spend = (time.time() - self._start_time) * 1000
        spend = round(spend, 1)
        return spend


class PerfFacade(object):
    TOTAL = 'total'
    DB = 'db'
    JSON = 'json'
    PARAMS = 'params'

    def __init__(self):
        self._perfspend = PerfMetric()
        self._metrics = dict()
        self._metric_name = ''

    def start(self, metric_name: str):
        self._metrics[metric_name] = 0
        self._metric_name = metric_name
        self._perfspend.start()

    def finish(self):
        self._metrics[self._metric_name] = self._perfspend.finish()

    @property
    def metric(self):
        return self._metrics

    def __getitem__(self, metric_name):
        return self._metrics[self._metric_name]

    def clear(self):
        self._metrics = dict()


class PerfSingleton(object):
    __instance = None

    @staticmethod
    def get() -> PerfFacade:
        if PerfSingleton.__instance is None:
            PerfSingleton.__instance = PerfFacade()
        return PerfSingleton.__instance

