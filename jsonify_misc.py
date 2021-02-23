from flask import current_app
# from json import dumps
from orjson import dumps


def jsonify(*args, **kwargs):
    if args and kwargs:
        raise TypeError('jsonify() behavior undefined when passed both args and kwargs')
    elif len(args) == 1:  # single args are passed directly to dumps()
        data = args[0]
    else:
        data = args or kwargs

    return current_app.response_class(
        str(dumps(data), "utf-8") + '\n',
        mimetype=current_app.config['JSONIFY_MIMETYPE']
    )