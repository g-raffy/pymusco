#!/usr/bin/env python3
import argparse
from pathlib import Path
from pymusco import Piece, load_piece_description
from pymusco import load_orchestra
from pymusco import Settings
from pymusco import load_musician_count
from pymusco import AutoTrackSelector
from pymusco import SingleTrackSelector
from pymusco import stub_to_print

import sys

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

    build_print_subparser = subparsers.add_parser("build-print", help="builds a print pdf file from a stub pdf of a musical score")
    build_print_subparser.add_argument('--stub-file-path', required=True, help="the location of the input stub file")
    build_print_subparser.add_argument('--print-file-path', required=True, help="the location of the output print file")

    track_selector_parsers = build_print_subparser.add_subparsers(dest='track_selector')
    ts_auto_parser = track_selector_parsers.add_parser("ts-auto", help="automatically works out what tracks to select based on the user provided musician headcount file")
    #build_print_subparser.add_('--track-selector', required=True, help="the location of the output print file")
    ts_auto_parser.add_argument('--headcount-file-path', required=True, help="the location of the input orchestra headcount file")

    ts_single_parser = track_selector_parsers.add_parser("ts-single", help="only the given single track is included in the print")
    #build_print_subparser.add_('--track-selector', required=True, help="the location of the output print file")
    ts_single_parser.add_argument('track_id', help="the identifier of the track to put in the print")

    try:
        namespace = parser.parse_args()
        print(namespace)
        settings = Settings()
        orchestra = load_orchestra(Path('./samples/harmony.orchestra'))
    except Exception as e:
        print(RED, str(e), RESET)
        sys.exit(1)

    if namespace.command == 'build-stub':

        for scan_desc_file_path in namespace.scan_desc_file_path:
            print(scan_desc_file_path)
            try:
                piece = load_piece_description(scan_desc_file_path, orchestra, settings)
                print("processing", BLUE, Path(scan_desc_file_path), RESET)
                piece.build_stub()
            except Exception as e:
                print(RED, "failed to process %s (%s)" % (scan_desc_file_path, str(e)), RESET)
                sys.exit(1)

    if namespace.command == 'build-print':

        try:
            track_selector = None
            if namespace.track_selector == 'ts-auto' :
                musician_count = load_musician_count(Path(namespace.headcount_file_path))
                track_selector = AutoTrackSelector(musician_count, orchestra)
            if namespace.track_selector == 'ts-single' :
                track_selector = SingleTrackSelector(namespace.track_id, orchestra)
            assert track_selector is not None
            stub_to_print(src_stub_file_path=Path(namespace.stub_file_path),
                dst_print_file_path=Path(namespace.print_file_path),
                track_selector=track_selector,
                orchestra=orchestra)
        except Exception as e:
            print(RED, str(e), RESET)
            sys.exit(1)
            raise

