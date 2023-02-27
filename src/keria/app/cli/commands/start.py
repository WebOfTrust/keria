# -*- encoding: utf-8 -*-
"""
KERIA
keria.cli.keria.commands module

Witness command line interface
"""
import argparse
import logging

from keri import __version__
from keri import help
from keri.app import directing

from keria.app import agenting

d = "Runs KERI Signify Agent\n"
d += "\tExample:\nkli ahab\n"
parser = argparse.ArgumentParser(description=d)
parser.set_defaults(handler=lambda args: launch(args))
parser.add_argument('-V', '--version',
                    action='version',
                    version=__version__,
                    help="Prints out version of script runner.")
parser.add_argument('-a', '--admin-http-port',
                    dest="admin",
                    action='store',
                    default=3901,
                    help="Admin port number the HTTP server listens on. Default is 5623.")
parser.add_argument('-H', '--http',
                    action='store',
                    default=3902,
                    help="Local port number the HTTP server listens on. Default is 5631.")
parser.add_argument('-c', '--controller', required=True,
                    help="Identifier prefix of the controller of this agent.")
parser.add_argument('-n', '--name',
                    action='store',
                    default="keria",
                    help="Name of controller. Default is agent.")
parser.add_argument('--base', '-b', help='additional optional prefix to file location of KERI keystore',
                    required=False, default="")
parser.add_argument('--passcode', '-p', help='22 character encryption passcode for keystore (is not saved)',
                    dest="bran", default=None)  # passcode => bran
parser.add_argument('--config-file',
                    dest="configFile",
                    action='store',
                    default="",
                    help="configuration filename")
parser.add_argument("--config-dir",
                    dest="configDir",
                    action="store",
                    default=None,
                    help="directory override for configuration data")


def launch(args):
    help.ogler.level = logging.CRITICAL
    help.ogler.reopen(name=args.name, temp=True, clear=True)

    logger = help.ogler.getLogger()

    logger.info("******* Starting Agent for %s listening: admin/%s, http/%s "
                ".******", args.name, args.admin, args.http)

    runAgent(args.controller, name=args.name,
             base=args.base,
             bran=args.bran,
             admin=args.admin,
             http=int(args.http),
             configFile=args.configFile,
             configDir=args.configDir)

    logger.info("******* Ended Agent for %s listening: admin/%s, http/%s"
                ".******", args.name, args.admin, args.http)


def runAgent(ctrlAid, *, name="ahab", base="", bran="", admin=5623, http=5632, configFile=None,
             configDir=None, expire=0.0):
    """
    Setup and run one witness
    """

    doers = []
    doers.extend(agenting.setup(name=name, base=base, bran=bran,
                                ctrlAid=ctrlAid,
                                adminPort=admin,
                                httpPort=http,
                                configFile=configFile,
                                configDir=configDir))

    directing.runController(doers=doers, expire=expire)
