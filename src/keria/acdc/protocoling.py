# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.agenting module

"""

import json

import falcon
from keri.core import coring, eventing

from keria.core import httping


def loadEnds(app):
    exnColEnd = IpexCollectionEnd()
    app.add_route("/identifiers/{name}/ipex", exnColEnd)


class IpexCollectionEnd:

    @staticmethod
    def on_get(req, rep):
        """ Ipex exchange message collection list endpoint

        Parameters:
            req (Request): falcon HTTP request object
            rep (Response): falcon HTTP response object


        """
        agent = req.context.agent

        notes = []
        for keys, notice in agent.notifier.noter.notes.getItemIter():
            if notice.pad['a']['r'].startswith("/exn/ipex"):
                notes.append(notice)

        for note in self.notes:
            attrs = note.attrs
            said = attrs['d']
            exn, pathed = exchanging.cloneMessage(self.hby, said)

            sender = exn.ked['i']
            if (sender in self.hby.habs and not self.sent) or (sender not in self.hby.habs and self.sent):
                continue

            if self.said:
                print(exn.said)
            else:
                print()
                match exn.ked['r']:
                    case "/ipex/agree":
                        self.agree(note, exn, attrs)
                    case "/ipex/apply":
                        self.apply(note, exn, attrs)
                    case "/ipex/offer":
                        self.offer(note, exn, attrs)
                    case "/ipex/grant":
                        self.grant(exn)
                    case "/ipex/admit":
                        self.admit(note, exn, attrs)
                    case "/ipex/spurn":
                        self.spurn(note, exn, attrs)
                    case _:
                        print("Unknown Type")
                print()
