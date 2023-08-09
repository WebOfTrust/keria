# -*- encoding: utf-8 -*-
"""
KERIA
keria.core.httping module

"""

import falcon
from falcon.http_status import HTTPStatus

class HandleCORS(object):
    def process_request(self, req, resp):
        resp.set_header('Access-Control-Allow-Origin', '*')
        resp.set_header('Access-Control-Allow-Methods', '*')
        resp.set_header('Access-Control-Allow-Headers', '*')
        resp.set_header('Access-Control-Max-Age', 1728000)  # 20 days
        if req.method == 'OPTIONS':
            raise HTTPStatus(falcon.HTTP_200, body='\n')


def getRequiredParam(body, name):
    param = body.get(name)
    if param is None:
        raise falcon.HTTPBadRequest(description=f"required field '{name}' missing from request")

    return param


def parseRangeHeader(header, name, start=0, end=9):
    """ Parse the start and end requested range values, defaults are 0, 9

    Parameters:
        header(str):  HTTP Range header value
        name (str): range name to look for
        start (int): default start index
        end(int): default end index

    Returns:
        (start, end): tuple of start index and end index

    """

    if not header.startswith(f"{name}="):
        return start, end

    header = header.strip(f"{name}=")
    try:
        if header.startswith("-"):
            return start, int(header[1:])

        if header.endswith("-"):
            return int(header[:-1]), end

        vals = header.split("-")
        if not len(vals) == 2:
            return start, end

        return int(vals[0]), int(vals[1])
    except ValueError:
        return start, end


