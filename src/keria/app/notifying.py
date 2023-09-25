# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.notifying module

"""
import json

import falcon
from keri.peer import exchanging

from keria.core import httping


def loadEnds(app):
    noteCol = NotificationCollectionEnd()
    app.add_route("/notifications", noteCol)
    noteRes = NotificationResourceEnd()
    app.add_route("/notifications/{said}", noteRes)


class NotificationCollectionEnd:

    @staticmethod
    def on_get(req, rep):
        """ Notification GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
        ---
        summary:  Get list of notifcations for the controller of the agent
        description:  Get list of notifcations for the controller of the agent.  Notifications will
                       be sorted by creation date/time
        parameters:
          - in: header
            name: Range
            schema:
              type: string
            required: false
            description: HTTP Range header syntax
            description: size of the result list.  Defaults to 25
        tags:
           - Notifications

        responses:
           200:
              description: List of contact information for remote identifiers
        """
        agent = req.context.agent

        rng = req.get_header("Range")
        if rng is None:
            rep.status = falcon.HTTP_200
            start = 0
            end = 24
        else:
            rep.status = falcon.HTTP_206
            start, end = httping.parseRangeHeader(rng, "notes")

        count = agent.notifier.getNoteCnt()
        notes = agent.notifier.getNotes(start=start, end=end)
        out = []
        for note in notes:
            attrs = note.attrs
            route = attrs['r']

            match route:
                case '/multisig/icp':
                    out.append(attrs)
                case '/multisig/ixn':
                    pass
                case '/multisig/rot':
                    pass
                case '/multisig/rpy':
                    pass
                case '/multisig/vcp':
                    out.append(NotificationCollectionEnd.vcp(agent.hby, agent.org, attrs))
                case '/multisig/iss':
                    pass
                case '/multisig/rev':
                    pass
                case '/multisig/exn':
                    pass
                case _:
                    continue

        end = start + (len(out) - 1) if len(out) > 0 else 0
        rep.set_header("Accept-Ranges", "notes")
        rep.set_header("Content-Range", f"notes {start}-{end}/{count}")
        rep.status = falcon.HTTP_200
        rep.data = json.dumps(out).encode("utf-8")

    @staticmethod
    def vcp(hby, org, attrs):

        said = attrs["d"]
        exn, pathed = exchanging.cloneMessage(hby, said=said)

        sender = exn.ked['i']
        payload = exn.ked['a']
        gid = payload["gid"]
        hab = hby.habs[gid] if gid in hby.habs else None
        if hab is None:
            raise ValueError(f"credential issuer not a valid AID={gid}")

        contact = org.get(sender)
        senderAlias = contact['alias']

        return dict(
            r=attrs['r'],
            d=said,
            exn=exn.ked,
            senderAllias=senderAlias
        )


class NotificationResourceEnd:

    @staticmethod
    def on_put(req, rep, said):
        """ Notification PUT endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            said: qb64 SAID of notification to mark as read

        ---
        summary:  Mark notification as read
        description:  Mark notification as read
        tags:
           - Notifications
        parameters:
          - in: path
            name: said
            schema:
              type: string
            required: true
            description: qb64 said of note to mark as read
        responses:
           202:
              description: Notification successfully marked as read for prefix
           404:
              description: No notification information found for SAID
        """
        agent = req.context.agent
        mared = agent.notifier.mar(said)
        if not mared:
            rep.status = falcon.HTTP_404
            rep.data = json.dumps(dict(msg=f"no notification to mark as read for {said}")).encode("utf-8")
            return

        rep.status = falcon.HTTP_202

    @staticmethod
    def on_delete(req, rep, said):
        """ Notification DELETE endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            said: qb64 SAID of notification to delete

        ---
        summary:  Delete notification
        description:  Delete notification
        tags:
           - Notifications
        parameters:
          - in: path
            name: said
            schema:
              type: string
            required: true
            description: qb64 said of note to delete
        responses:
           202:
              description: Notification successfully deleted for prefix
           404:
              description: No notification information found for prefix
        """
        agent = req.context.agent
        deleted = agent.notifier.noter.rem(said)
        if not deleted:
            rep.status = falcon.HTTP_404
            rep.text = f"no notification to delete for {said}"
            return

        rep.status = falcon.HTTP_202
