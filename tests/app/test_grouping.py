# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.grouping module

Testing the Mark II Agent Grouping endpoints

"""
from keria.app import grouping, aiding


def test_load_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        grouping.loadEnds(app=app)
        assert app._router is not None

        res = app._router.find("/test")
        assert res is None

        (end, *_) = app._router.find("/identifiers/NAME/multisig/request")
        assert isinstance(end, grouping.MultisigRequestCollectionEnd)
        (end, *_) = app._router.find("/multisig/request/SAID")
        assert isinstance(end, grouping.MultisigRequestResourceEnd)


def test_multisig_request_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        grouping.loadEnds(app=app)

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)

        # First create participants (aid1, aid2) in a multisig AID
        salt0 = b'0123456789abcdef'
        op = helpers.createAid(client, "aid1", salt0)
        aid = op["response"]
        pre = aid['i']
        assert pre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        icp = {
            "v": "KERI10JSON0002c7_",
            "t": "dip",
            "d": "EAbkBt1AkiKskBb-SBACC07ioQ1sx9Q44SpKRZwKjMaU",
            "i": "EAbkBt1AkiKskBb-SBACC07ioQ1sx9Q44SpKRZwKjMaU",
            "s": "0",
            "kt": [
                "1/3",
                "1/3",
                "1/3"
            ],
            "k": [
                "DPmhSfdhCPxr3EqjxzEtF8TVy0YX7ATo0Uc8oo2cnmY9",
                "DM1XbVrBOpVRyXDCKlvMWNE_qkkGU4rVq-7_bHP7za8W",
                "DNwaetMMIMbt708EPsdCGHZpMe3gf1OZV-R7LTcJBLnK"
            ],
            "nt": [
                "1/3",
                "1/3",
                "1/3"
            ],
            "n": [
                "EAORnRtObOgNiOlMolji-KijC_isa3lRDpHCsol79cOc",
                "EPJy-TM6OHBJeAFTpb31YVrDSPXQTYmhvDc7DioakK8h",
                "EHUXA8lpGe1MObjP8RZs9WijzNsjKdoSql_zajgJGLQ6"
            ],
            "bt": "2",
            "b": [
                "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"
            ],
            "c": [],
            "a": [],
            "di": "EHpD0-CDWOdu5RJ8jHBSUkOqBZ3cXeDVHWNb_Ul89VI7"
        }



        client.simulate_post()

