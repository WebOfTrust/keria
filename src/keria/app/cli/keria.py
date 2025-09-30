# -*- encoding: utf-8 -*-
"""
KERIA
keria.cli.commands module

"""

import multicommand

from keria.app.cli import commands


def main():
    parser = multicommand.create_parser(commands)
    args = parser.parse_args()

    if not hasattr(args, "handler"):
        parser.print_help()
        return

    try:
        args.handler(args)

    except Exception as ex:
        # print(f"ERR: {ex}")
        # return -1
        raise ex


if __name__ == "__main__":
    main()
