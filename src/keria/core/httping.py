# -*- encoding: utf-8 -*-
"""
KERIA
keria.core.httping module

HTTP utility
"""

from collections import namedtuple

from http_sfv import Dictionary
from keri.help import helping

DEFAULTHEADERS = ('(created)', '(request-target)')

Inputage = namedtuple("Inputage", "name fields created keyid alg expires nonce context")


def normalize(param):
    return param.strip()


def siginput(hab, name, method, path, headers, fields, expires=None, nonce=None, alg=None, keyid=None, context=None):
    """ Create an HTTP Signature-Input Header

    Returns:
        header (dict): {'Signature-Input': 'value'} where value is RFC8941 compliant
        (Structured Field Values for HTTP) formatted str of of Signature Input group.
        sigers (Unqualified): unqualified base64 encoded signature

    """
    items = []
    ifields = []

    # Create Signature Base, start with the fields and
    for field in fields:
        if field.startswith("@"):
            if field == "@method":
                items.append(f'"{field}": {method}')
                ifields.append(field)
            elif field == "@path":
                items.append(f'"{field}": {path}')
                ifields.append(field)

        else:
            field = field.lower()
            if field not in headers:
                continue

            ifields.append(field)
            value = normalize(headers[field])
            items.append(f'"{field}": {value}')

    sid = Dictionary()
    sid[name] = ifields
    now = helping.nowUTC()
    sid[name].params['created'] = int(now.timestamp())

    values = [f"({' '.join(ifields)})", f"created={int(now.timestamp())}"]
    if expires is not None:
        values.append(f"expires={expires}")
        sid[name].params['expires'] = expires
    if nonce is not None:
        values.append(f"nonce={nonce}")
        sid[name].params['nonce'] = nonce
    if keyid is not None:
        values.append(f"keyid={keyid}")
        sid[name].params['keyid'] = keyid
    if context is not None:
        values.append(f"context={context}")
        sid[name].params['context'] = context
    if alg is not None:
        values.append(f"alg={alg}")
        sid[name].params['alg'] = alg

    params = ';'.join(values)

    items.append(f'"@signature-params: {params}"')
    ser = "\n".join(items).encode("utf-8")
    sigers = hab.sign(ser=ser,
                      verfers=hab.kever.verfers,
                      indexed=False)

    return {'Signature-Input': f"{str(sid)}"}, sigers[0]  # join all signature input value strs


def desiginput(value):
    """ Verify the signature header based on values as identified in signature-input header

    Parameters:
        value (Request): falcon request object

    Returns:

    """
    sid = Dictionary()
    sid.parse(value)

    siginputs = []
    for name, svfields in sid.items():
        fields = [i.value for i in svfields]
        if "created" not in svfields.params:
            raise ValueError("missing required `created` field from signature input")
        created = svfields.params["created"]
        if "expires" in svfields.params:
            expires = svfields.params["expires"]
        else:
            expires = None
        if "nonce" in svfields.params:
            nonce = svfields.params["nonce"]
        else:
            nonce = None
        if "alg" in svfields.params:
            alg = svfields.params["alg"]
        else:
            alg = None
        if "keyid" in svfields.params:
            keyid = svfields.params["keyid"]
        else:
            keyid = None
        if "context" in svfields.params:
            context = svfields.params["context"]
        else:
            context = None

        siginputs.append(Inputage(name=name, fields=fields, created=created, expires=expires, nonce=nonce, alg=alg,
                                  keyid=keyid, context=context))
    return siginputs

