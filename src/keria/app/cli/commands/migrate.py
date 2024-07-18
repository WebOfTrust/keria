# -*- encoding: utf-8 -*-
"""
KERIA
keria.cli.keria.commands module

"""
import argparse

from hio.base import doing
from keri.app.cli.commands.migrate import run
from keria.db import basing


def handler(args):
    """
    Migrate KERIA agents

    Args:
        args(Namespace): arguments object from command line
    """
    migrator = MigrateDoDoer(args)
    return [migrator]


parser = argparse.ArgumentParser(description='Runs outstanding migrations for all agents')
parser.set_defaults(handler=handler,
                    transferable=True)
parser.add_argument('--base', '-b', help='additional optional prefix to file location of KERI keystore',
                    required=False, default="")


class MigrateDoDoer(doing.DoDoer):
    def __init__(self, args):
        self.args = args
        self.adb = basing.AgencyBaser(name="TheAgency", base=args.base, reopen=True, temp=False)
        doers = [doing.doify(self.migrateAgentsDo)]

        super(MigrateDoDoer, self).__init__(doers=doers)

    def migrateAgentsDo(self, tymth, tock=0.0):
        """ For each agent in the agency, add a migrate doer

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        for ((caid,), _) in self.adb.agnt.getItemIter():
            args = run.parser.parse_args(['--name', caid, '--base', self.args.base, '--temp', False])
            self.extend([run.MigrateDoer(args)])
        return True
