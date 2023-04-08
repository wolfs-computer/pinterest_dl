#!/usr/bin/env python3

import sys
from pinterest_dl import config_parser
from pinterest_dl import arg_parser
from pinterest_dl import arg_manager


# get CLI arguments

parser = arg_parser.create_parser()

# if no options were given display help and exit
if len(sys.argv) == 1:
    parser.print_help(sys.stderr)
    sys.exit(1)

args = parser.parse_args()


# get config
config = config_parser.read_config(args.config_path)


if __name__ == "__main__":
    try:
        arg_manager.main(args, config)
    except KeyboardInterrupt:
        sys.exit('\nERROR: Interrupted by user')
