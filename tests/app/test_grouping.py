import json

import falcon
from falcon import testing
from keri.app import habbing
from keri.core import coring, eventing, parsing

from keria.app import grouping


def test_group_event_collection_end():
    salt = b'0123456789abcdef'
    salter = coring.Salter(raw=salt)

    with habbing.openHby(name="agent", salt=salter.qb64, temp=True) as agentHby, \
            habbing.openHby(name="p1", temp=True) as p1hby, \
            habbing.openHby(name="p2", temp=True) as p2hby:

        agent = agentHby.makeHab(name="agent")
        assert agent.pre == "EBErgFZoM3PBQNTpTuK9bax_U8HLJq1Re2RM1cdifaTJ"
        p1 = p1hby.makeHab(name="p1")
        assert p1.pre == "EBPtjiAY9ITdvScWFGeeCu3Pf6_CFFr57siQqffVt9Of"
        p2 = p2hby.makeHab(name="p2")
        assert p2.pre == "EMYBtOuBKVdp3KdW_QM__pi-UAWfrewlDyiqGcbIbopR"

        agentKvy = eventing.Kevery(db=agentHby.db)
        psr = parsing.Parser(kvy=agentKvy)
        psr.parseOne(p1.makeOwnInception())
        psr.parseOne(p2.makeOwnInception())

        assert p1.pre in agentHby.kevers
        assert p2.pre in agentHby.kevers

        app = falcon.App()
        grouping.loadEnds(app=app, agentHby=agentHby)

        client = testing.TestClient(app)

        body = dict(
            smids=[agent.pre, p1.pre, p2.pre],
            ssns=[0, 0, 0],
            nmids=[agent.pre, p1.pre, p2.pre],
            nsns=[0, 0, 0],
        )
        res = client.simulate_post("/groups/events", body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 200
        serder = eventing.Serder(ked=res.json)
        assert serder.pre == "ENH3nyg6QzVx3quj8Ecb3kAPYUOnG54LeJd1_NTwZ9LX"
        assert serder.raw == (b'{"v":"KERI10JSON0001e7_","t":"icp","d":"ENH3nyg6QzVx3quj8Ecb3kAPYUOnG54LeJd1'
                              b'_NTwZ9LX","i":"ENH3nyg6QzVx3quj8Ecb3kAPYUOnG54LeJd1_NTwZ9LX","s":"0","kt":"2'
                              b'","k":["DHh2g07Bl2UjV6DIOQZ4cu_82r1vuebMQTq-_waXI1ew","DAOF6DRwWDphP8F2r87ux'
                              b'TS9xwIehonmTBE1agJrPklA","DPZ-k6HXUhiS5dPy8awuitFpwojGOQJ6DMZiatPjhXKC"],"nt'
                              b'":"2","n":["EFcHDCGFRbFEagZcpfUjataQSdBykFAmyYRYrUJTgCN_","ECTS-VsMzox2NoMaL'
                              b'Iei9Gb6361Z3u0fFFWmjEjEeD64","ED7Jk3MscDy8IHtb2k1k6cs0Oe5rEb3_8XKD1Ut_gCo8"]'
                              b',"bt":"0","b":[],"c":[],"a":[]}')

        body = dict(
            smids=[agent.pre, p1.pre, p2.pre],
            ssns=[0, 0, 0],
            isith=["1/2", "1/2", "1/2"],
            nmids=[agent.pre, p1.pre, p2.pre],
            nsith=["1/2", "1/2", "1/2"],
            nsns=[0, 0, 0],
            toad="3",
            wits=["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                  "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                  "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"],
            estOnly=True,
            DnD=True,
            data=["ENH3nyg6QzVx3quj8Ecb3kAPYUOnG54LeJd1_NTwZ9LX"]

        )
        res = client.simulate_post("/groups/events", body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 200
        serder = eventing.Serder(ked=res.json)
        assert serder.pre == "EDLwiS86cWE3-9WobO73kUfoiU_yaQbGN5PHVTWURFK8"
        assert serder.raw == (b'{"v":"KERI10JSON0002cb_","t":"icp","d":"EDLwiS86cWE3-9WobO73kUfoiU_yaQbGN5PH'
                              b'VTWURFK8","i":"EDLwiS86cWE3-9WobO73kUfoiU_yaQbGN5PHVTWURFK8","s":"0","kt":["'
                              b'1/2","1/2","1/2"],"k":["DHh2g07Bl2UjV6DIOQZ4cu_82r1vuebMQTq-_waXI1ew","DAOF6'
                              b'DRwWDphP8F2r87uxTS9xwIehonmTBE1agJrPklA","DPZ-k6HXUhiS5dPy8awuitFpwojGOQJ6DM'
                              b'ZiatPjhXKC"],"nt":["1/2","1/2","1/2"],"n":["EFcHDCGFRbFEagZcpfUjataQSdBykFAm'
                              b'yYRYrUJTgCN_","ECTS-VsMzox2NoMaLIei9Gb6361Z3u0fFFWmjEjEeD64","ED7Jk3MscDy8IH'
                              b'tb2k1k6cs0Oe5rEb3_8XKD1Ut_gCo8"],"bt":"3","b":["BBilc4-L3tFUnfM_wJr4S4OJanAv'
                              b'_VmF_dJNN6vkf2Ha","BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM","BIKKuvBwpm'
                              b'DVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"],"c":["EO","DND"],"a":["ENH3nyg6QzVx3quj'
                              b'8Ecb3kAPYUOnG54LeJd1_NTwZ9LX"]}')




