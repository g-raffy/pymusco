#!/usr/bin/env python3
import argparse
from pathlib import Path
from pymusco import Piece, load_piece_description
from pymusco import Harmony
from pymusco import Settings

RED   = "\033[1;31m"  
BLUE  = "\033[1;34m"
CYAN  = "\033[1;36m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
BOLD    = "\033[;1m"
REVERSE = "\033[;7m"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='python musical score sheet music processor')
    subparsers = parser.add_subparsers()
    subparsers.required = True
    subparsers.dest = 'command'

    build_stub_subparser = subparsers.add_parser("build-stub", help="builds a stub pdf file from a scanned pdf of a musical score and a desription of its table of contents")
    build_stub_subparser.add_argument('--scan-desc-file-path', required=True, nargs='+', help="the scan desciption files path")

    namespace = parser.parse_args()
    print(namespace)
    settings = Settings()
    orchestra = Harmony()

    if namespace.command == 'build-stub':

        for scan_desc_file_path in namespace.scan_desc_file_path:
            print(scan_desc_file_path)
            try:
                piece = load_piece_description(scan_desc_file_path, orchestra, settings)
                piece.build_stub()
                print(BLUE, Path(scan_desc_file_path), RESET)
            except:
                print(RED, "failed to process %s" % scan_desc_file_path, RESET)
                raise
