import falcon


def getRequiredParam(body, name):
    param = body.get(name)
    if param is None:
        raise falcon.HTTPBadRequest(title=f"required field '{name}' missing from request")

    return param
