# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.messaging module

"""
import json

import falcon.errors
from keri import kering

from keria.core import httping


def loadEnds(app):
    msgCol = MessageCollectionEnd()
    app.add_route("/messages", msgCol)


class MessageCollectionEnd:

    @staticmethod
    def on_get(req, rep):
        """ Messages GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
        ---
        summary:  Get list of message exns for the controller of the agent
        description:  Get list of message exns for the controller of the agent.  Messages will
                       be sorted by received date/time
        parameters:
          - in: query
            name: sender
            schema:
              type: string
            required: false
            description: qb64 SAID of sender of message to use as a filter
          - in: query
            name: recipient
            schema:
              type: string
            required: false
            description: qb64 SAID of recipient of message to use as a filter
        tags:
           - Messages

        responses:
           200:
              description: list of message exns for the controller of the agent
        """
        agent = req.context.agent

        sender = req.params.get("sender")
        recipient = req.params.get("recipient")

        rng = req.get_header("Range")
        if rng is None:
            rep.status = falcon.HTTP_200
            start = 0
            end = 9
        else:
            rep.status = falcon.HTTP_206
            start, end = httping.parseRangeHeader(rng, "messages")

        try:
            exns = agent.messanger.list(start=start, end=end, sender=sender, recipient=recipient)
        except kering.MissingSignatureError:
            raise falcon.errors.HTTPServiceUnavailable(description="stored message exn data failed verification")

        rep.status = falcon.HTTP_200
        rep.data = json.dumps(exns).encode("utf-8")



