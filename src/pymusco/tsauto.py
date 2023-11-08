'''
Created on Sep 9, 2018

@author: graffy
'''

from .core import ITrackSelector
from .core import Track
from .core import load_commented_json


def load_musician_count(musician_count_file_path):
    return load_commented_json(musician_count_file_path)


class AutoTrackSelector(ITrackSelector):
    """
    a track selector that automatically works out the number of prints to generate for each track, by looking at the number of musicians by instrument type in the orchestra.
    """

    def __init__(self, musician_count, orchestra, include_tracks_for_external_players=True, num_extra_prints=0):
        """
        :param dict(str, int) musician_count:
        :param Orchestra orchestra: the inventory of musical instruments
        :param int include_tracks_for_external_players: if True, the tracks for musicians that are not in musician_count are ignored
        :param int num_extra_prints: number of extra prints per track (could be negative). Typically used with value -1 to have a print complementing an already printed stub
        """
        self.musician_count = musician_count
        self.orchestra = orchestra
        self.include_tracks_for_external_players = include_tracks_for_external_players
        self.num_extra_prints = num_extra_prints

    @staticmethod
    def add_extra_prints(track_to_print_count, num_extra_prints):
        new_track_to_print_count = {}
        for track_id, num_prints in track_to_print_count.items():
            if num_prints + num_extra_prints > 0:
                new_track_to_print_count[track_id] = num_prints + num_extra_prints
        return new_track_to_print_count

    def get_track_to_copy(self, stub_tracks):
        """
        computes for each stub_track the number of prints to do, given the musician count

        :param list(str) stub_tracks:
        :return dict(str, int): the number of prints to do for each stub_track
        """
        track_to_print_count = {}
        for musician_type_id, num_musicians in self.musician_count.items():
            print(f'musician_type_id = {musician_type_id}')
            # collect the tracks than can be played by these musicians
            playable_tracks = []
            dispatch_tracks_between_musicians = True
            for track_id in stub_tracks:
                track = Track(track_id, self.orchestra)
                # print('processing track %s' % track.get_id())
                # print('track.instrument.get_player() = %s' % track.instrument.get_player())
                if not track.is_disabled:
                    # print('processing enabled track %s' % track.get_id())

                    if track.instrument.get_player() == musician_type_id:
                        print(f'this is a track for {musician_type_id}')
                        print('track.instrument', track.instrument.get_id())
                        if not track.is_rare:
                            if musician_type_id == 'percussionist':
                                # special case : each percussionist wants all tracks
                                dispatch_tracks_between_musicians = False
                                track_to_print_count[track.get_id()] = num_musicians + 1
                            elif track.is_solo:
                                # solos are always wanted even if the orchestra doesn't have its player
                                print(f"info: 2 copies for solo track {track.get_id()}")
                                track_to_print_count[track.get_id()] = 2
                            elif track.instrument.is_single():
                                # only print twice for tracks such as 'bb bass clarinet' or 'c piccolo', as they're not supposed to be more than one in an orchestra (one fore the player + 1 extra)
                                print(f"info: 2 copies for single instrument {track.get_id()}")
                                track_to_print_count[track.get_id()] = 2
                            else:
                                playable_tracks.append(track)
            if dispatch_tracks_between_musicians:
                if len(playable_tracks) == 0:
                    print(f"warning: no playable tracks found to dispatch for player type {musician_type_id}")
                else:
                    num_musicians_per_track = num_musicians // len(playable_tracks) + 1
                    for track in playable_tracks:
                        print(f"info: {num_musicians_per_track} copies of {track.get_id()}")
                        track_to_print_count[track.get_id()] = num_musicians_per_track
        if self.include_tracks_for_external_players:
            for track_id in stub_tracks:
                if track_id not in track_to_print_count.keys():  # pylint: disable=consider-iterating-dictionary
                    track = Track(track_id, self.orchestra)
                    if not track.is_disabled:
                        count = 0
                        if track.is_rare:
                            count = 0
                        elif track.instrument.is_single():
                            # eg piano, string bass
                            count = 1

                        if track.instrument.is_single():
                            if track.get_id() not in track_to_print_count:
                                # force adding single instrument tracks such as harp or piano even if there's no player in the orchestra because these parts are often played by external musicians
                                print(f"info: 2 copies for single instrument {track.get_id()}")
                                track_to_print_count[track.get_id()] = 2

                        track_to_print_count[track_id] = count
        print(track_to_print_count)
        return AutoTrackSelector.add_extra_prints(track_to_print_count, self.num_extra_prints)
