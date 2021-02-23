from misc import PerfSingleton
from functools import wraps


def timing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        perf = PerfSingleton.get()
        # perf.start(PerfFacade.TOTAL)
        res = func(*args, **kwargs)
        # perf.finish()
        resp = res
        # resp = app.make_response(res)
        s_timing = ''
        for (mn, mv) in perf.metric.items():
            s_timing = s_timing + f"{mn}; dur={mv}, "
        resp.headers.add("Server-Timing", s_timing)
        perf.clear()
        return res

    return wrapper
