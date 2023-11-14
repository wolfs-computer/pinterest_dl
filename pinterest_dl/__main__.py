#!/usr/bin/env python3

import sys
from pinterest_dl import config_functions
from pinterest_dl import cli_parser
from pinterest_dl import cli_functions


def main():
    """
    main pinterest_dl function
    """

    # get CLI arguments:
    parser = cli_parser.create_parser()

    # if no options were given display help and exit
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    # get config:
    config = config_functions.read_config(args.config_path)

    # start application:
    try:
        cli_functions.arg_execute(args, config)
    except KeyboardInterrupt:
        sys.exit('\nERROR: Interrupted by user')


if __name__ == "__main__":
    main()
