# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.core.httping module

Testing httping utils
"""

from hio.help import Hict
from keri.app import habbing
from keri.end import ending

from keria.core import httping


def test_siginput(mockHelpingNowUTC):
    print()
    with habbing.openHab(name="test", base="test", temp=True) as (hby, hab):
        headers = Hict([
            ("Content-Type", "application/json"),
            ("Content-Length", "256"),
            ("Connection", "close"),
            ("Signify-Resource", "EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs"),
            ("Signify-Timestamp", "2022-09-24T00:05:48.196795+00:00"),
        ])

        header, sig = httping.siginput(hab, "sig0", "POST", "/signify", headers,
                                       fields=["Signify-Resource", "@method",
                                               "@path",
                                               "Signify-Timestamp"],
                                       alg="ed25519", keyid=hab.pre)

        headers.extend(header)
        signage = ending.Signage(markers=dict(sig0=sig), indexed=False, signer=None, ordinal=None, digest=None,
                                 kind=None)
        headers.extend(ending.signature([signage]))

        assert dict(headers) == {'Connection': 'close',
                                 'Content-Length': '256',
                                 'Content-Type': 'application/json',
                                 'Signify-Resource': 'EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs',
                                 'Signify-Timestamp': '2022-09-24T00:05:48.196795+00:00',
                                 'Signature': 'indexed="?0";sig0="0BCF-Qc9q1YrNOP5Np4fy9mz0o8HQALANKP8ZjvItfjjmpYKYL_FS'
                                              'j4bcLZKFSd81bo9SeQn36bLt3dpbEzt2GgN"',
                                 'Signature-Input': 'sig0=("signify-resource" "@method" "@path" '
                                                    '"signify-timestamp");created=1609459200;keyid="EIaGMMWJFPmtXznY1II'
                                                    'iKDIrg-vIyge6mBl2QV8dDjI3";alg="ed25519"'}

        siginput = headers["Signature-Input"]
        signature = headers["Signature"]

        inputs = httping.desiginput(siginput.encode("utf-8"))
        assert len(inputs) == 1
        inputage = inputs[0]

        assert inputage.name == 'sig0'
        assert inputage.fields == ['signify-resource', "@method", "@path", "signify-timestamp"]
        assert inputage.created == 1609459200
        assert inputage.alg == "ed25519"
        assert inputage.keyid == hab.pre
        assert inputage.expires is None
        assert inputage.nonce is None
        assert inputage.context is None

        items = []
        for field in inputage.fields:
            if field.startswith("@"):
                if field == "@method":
                    items.append(f'"{field}": POST')
                elif field == "@path":
                    items.append(f'"{field}": /signify')

            else:
                field = field.lower()
                if field not in headers:
                    continue

                value = httping.normalize(headers[field])
                items.append(f'"{field}": {value}')

        values = [f"({' '.join(inputage.fields)})", f"created={inputage.created}"]
        if inputage.expires is not None:
            values.append(f"expires={inputage.expires}")
        if inputage.nonce is not None:
            values.append(f"nonce={inputage.nonce}")
        if inputage.keyid is not None:
            values.append(f"keyid={inputage.keyid}")
        if inputage.context is not None:
            values.append(f"context={inputage.context}")
        if inputage.alg is not None:
            values.append(f"alg={inputage.alg}")

        params = ';'.join(values)

        items.append(f'"@signature-params: {params}"')
        ser = "\n".join(items).encode("utf-8")

        signages = ending.designature(signature)
        assert len(signages) == 1
        assert signages[0].indexed is False
        assert "sig0" in signages[0].markers

        cig = signages[0].markers["sig0"]
        assert hab.kever.verfers[0].verify(sig=cig.raw, ser=ser) is True
