# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.notifying module

"""
import json

import falcon


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
          - in: query
            name: last
            schema:
              type: string
            required: false
            description: qb64 SAID of last notification seen
          - in: query
            name: limit
            schema:
              type: integer
            required: false
            description: size of the result list.  Defaults to 25
        tags:
           - Notifications

        responses:
           200:
              description: List of contact information for remote identifiers
        """
        agent = req.context.agent
        last = req.params.get("last")
        limit = req.params.get("limit")

        limit = int(limit) if limit is not None else 25

        if last is not None:
            val = agent.notifier.noter.get(last)
            if val is not None:
                lastNote, _ = val
                start = lastNote.datetime
            else:
                start = ""
        else:
            start = ""

        notes = agent.notifier.getNotes(start=start, limit=limit)
        out = [note.pad for note in notes]

        rep.status = falcon.HTTP_200
        rep.data = json.dumps(out).encode("utf-8")


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
