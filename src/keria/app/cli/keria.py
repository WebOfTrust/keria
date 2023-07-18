# -*- encoding: utf-8 -*-
"""
KERIA
keria.cli.commands module

"""
import multicommand
from keri import help

from keri.app import directing
from keria.app.cli import commands

logger = help.ogler.getLogger()


def main():
    parser = multicommand.create_parser(commands)
    args = parser.parse_args()

    if not hasattr(args, 'handler'):
        parser.print_help()
        return

    try:
        doers = args.handler(args)
        directing.runController(doers=doers, expire=0.0)

    except Exception as ex:
        raise ex
        # print(f"ERR: {ex}")
        # return -1


if __name__ == "__main__":
    main()
