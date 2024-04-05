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
                    help="Admin port number the HTTP server listens on. Default is 3901.")
parser.add_argument('-H', '--http',
                    action='store',
                    default=3902,
                    help="Local port number the HTTP server listens on. Default is 3902.")
parser.add_argument('-B', '--boot',
                    action='store',
                    default=3903,
                    help="Boot port number the Boot HTTP server listens on.  This port needs to be secured."
                         " Default is 3903.")
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
parser.add_argument("--keypath", action="store", required=False, default=None,
                    help="TLS server private key file")
parser.add_argument("--certpath", action="store", required=False, default=None,
                    help="TLS server signed certificate (public key) file")
parser.add_argument("--cafilepath", action="store", required=False, default=None,
                    help="TLS server CA certificate chain")
parser.add_argument("--loglevel", action="store", required=False, default="CRITICAL",
                    help="Set log level to DEBUG | INFO | WARNING | ERROR | CRITICAL. Default is CRITICAL")
parser.add_argument("--logfile", action="store", required=False, default=None,
                    help="path of the log file. If not defined, logs will not be written to the file.")


def launch(args):
    help.ogler.level = logging.getLevelName(args.loglevel)
    if(args.logfile != None):
        help.ogler.headDirPath = args.logfile
        help.ogler.reopen(name=args.name, temp=False, clear=True)

    logger = help.ogler.getLogger()

    logger.info("******* Starting Agent for %s listening: admin/%s, http/%s "
                ".******", args.name, args.admin, args.http)

    runAgent(name=args.name,
             base=args.base,
             bran=args.bran,
             admin=int(args.admin),
             http=int(args.http),
             boot=int(args.boot),
             configFile=args.configFile,
             configDir=args.configDir,
             keypath=args.keypath,
             certpath=args.certpath,
             cafilepath=args.cafilepath)

    logger.info("******* Ended Agent for %s listening: admin/%s, http/%s"
                ".******", args.name, args.admin, args.http)


def runAgent(name="ahab", base="", bran="", admin=3901, http=3902, boot=3903, configFile=None,
             configDir=None, keypath=None, certpath=None, cafilepath=None, expire=0.0):
    """
    Setup and run a KERIA Agency
    """

    doers = []
    doers.extend(agenting.setup(name=name, base=base, bran=bran,
                                adminPort=admin,
                                httpPort=http,
                                bootPort=boot,
                                configFile=configFile,
                                configDir=configDir,
                                keypath=keypath,
                                certpath=certpath,
                                cafilepath=cafilepath))

    directing.runController(doers=doers, expire=expire)
