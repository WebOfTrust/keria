# -*- encoding: utf-8 -*-
"""
KERIA
keria.cli.keria.commands.start module

KERIA Agent server start command line interface (CLI) command
"""
import argparse
import os


from keri import __version__
from keri import help

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
                    type=int,
                    default=os.getenv("KERIA_ADMIN_PORT", "3901"),
                    help="Admin port number the HTTP server listens on. Default is 3901.")
parser.add_argument('-H', '--http',
                    action='store',
                    type=int,
                    default=os.getenv("KERIA_HTTP_PORT", "3902"),
                    help="Local port number the HTTP server listens on. Default is 3902.")
parser.add_argument('-B', '--boot',
                    action='store',
                    type=int,
                    default=os.getenv("KERIA_BOOT_PORT", "3903"),
                    help="Boot port number the Boot HTTP server listens on.  This port needs to be secured."
                         " Default is 3903.")
parser.add_argument('-n', '--name',
                    action='store',
                    default="keria",
                    help="Name of controller. Default is 'keria'.")
parser.add_argument('--base', '-b', help='additional optional prefix to file location of KERI keystore',
                    required=False, default="")
parser.add_argument('--passcode', '-p', help='22 character encryption passcode for keystore (is not saved)',
                    dest="bran",
                    default=os.getenv("KERIA_PASSCODE"))  # passcode => bran
parser.add_argument('--config-file',
                    dest="configFile",
                    action='store',
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
parser.add_argument("--loglevel", action="store", required=False, default=os.getenv("KERIA_LOG_LEVEL", "CRITICAL"),
                    help="Set log level to DEBUG | INFO | WARNING | ERROR | CRITICAL. Default is CRITICAL")
parser.add_argument("--logfile", action="store", required=False, default=None,
                    help="path of the log file. If not defined, logs will not be written to the file.")
parser.add_argument("--experimental-boot-password",
                    help="Experimental password for boot endpoint. Enables HTTP Basic Authentication for the boot endpoint. Only meant to be used for testing purposes.",
                    dest="bootPassword",
                    default=os.getenv("KERIA_EXPERIMENTAL_BOOT_PASSWORD"))
parser.add_argument("--experimental-boot-username",
                    help="Experimental username for boot endpoint. Enables HTTP Basic Authentication for the boot endpoint. Only meant to be used for testing purposes.",
                    dest="bootUsername",
                    default=os.getenv("KERIA_EXPERIMENTAL_BOOT_USERNAME"))


logger = help.ogler.getLogger()


def launch(args):
    agenting.runAgency(agenting.KERIAServerConfig(
        name=args.name or "ahab",
        base=args.base or "",
        bran=args.bran,
        adminPort=args.admin,
        httpPort=args.http,
        bootPort=args.boot,
        configFile=args.configFile,
        configDir=args.configDir,
        keyPath=args.keypath,
        certPath=args.certpath,
        caFilePath=args.cafilepath,
        logLevel=args.loglevel,
        logFile=args.logfile,
        cors=os.getenv("KERI_AGENT_CORS", "false").lower() in ("true", "1"),
        releaseTimeout=int(os.getenv("KERIA_RELEASER_TIMEOUT", "86400")),
        curls=getListVariable("KERIA_CURLS"),
        iurls=getListVariable("KERIA_IURLS"),
        durls=getListVariable("KERIA_DURLS"),
        bootPassword=args.bootPassword,
        bootUsername=args.bootUsername
    ))
    logger.info("Agent %s gracefully stopped", args.name)

def getListVariable(name):
    value = os.getenv(name)
    return value.split(";") if value else None