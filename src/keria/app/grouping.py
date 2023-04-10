# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.grouping module

"""


def loadEnds(app, agentHby):
    groupsEnd = GroupEventCollectionEnd(agentHby)
    app.add_route("/groups", groupsEnd)
    groupsEventsEnd = GroupEventCollectionEnd(agentHby)
    app.add_route("/groups/events", groupsEventsEnd)


class GroupCollectionEnd:

    def __init__(self, hby):
        self.hby = hby
        pass


class GroupEventCollectionEnd:

    def __init__(self, hby):
        self.hby = hby
        pass

