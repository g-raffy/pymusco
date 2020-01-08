'''
Created on Sep 9, 2018

@author: graffy
'''

from .core import ITrackSelector
from .core import Track


class AutoTrackSelector(ITrackSelector):
    """
    a track selector that automatically works out the number of prints to generate for each track, by looking at the number of musicians by instrument type in the orchestra.
    """

    def __init__(self, musician_count, orchestra):
        """
        :param dict(str, int) musician_count:
        :param Orchestra orchestra: the inventory of musical instruments
        """
        self.musician_count = musician_count
        self.orchestra = orchestra

    def get_track_to_copy(self, stub_tracks):
        """
        computes for each stub_track the number of prints to do, given the musician count

        :param list(str) stub_tracks:
        :return dict(str, int): the number of prints to do for each stub_track
        """
        track_to_print_count = {}
        for musician_type_id, num_musicians in self.musician_count.iteritems():
            print('musician_type_id = %s' % musician_type_id)
            # collect the tracks than can be played by these musicians
            playable_tracks = []
            for track_id in stub_tracks:
                track = Track(track_id, self.orchestra)
                # print('processing track %s' % track.get_id())
                # print('track.instrument.get_player() = %s' % track.instrument.get_player())
                if not track.is_disabled:

                    if track.is_solo:
                        if track.get_id() not in track_to_print_count:
                            # solos are always wanted even if the orchestra doesn't have its player
                            print("info: 2 copies for solo track %s" % track.get_id())
                            track_to_print_count[track.get_id()] = 2

                    if track.instrument.is_single:
                        if track.get_id() not in track_to_print_count:
                            # force adding single instrument tracks such as harp or piano even if there's no player in the orchestra because these parts are often played by external musicians
                            print("info: 2 copies for single instrument %s" % track.get_id())
                            track_to_print_count[track.get_id()] = 2

                    if track.instrument.get_player() == musician_type_id:
                        # print('this is a track for %s' % musician_type_id)
                        # print('track.instrument', track.instrument.get_id())
                        if not track.is_rare:
                            if musician_type_id == 'percussionist':
                                # special case : each percussionist wants all tracks
                                track_to_print_count[track.get_id()] = num_musicians + 1
                            elif track.instrument.is_single():
                                # only print twice for tracks such as 'bb bass clarinet' or 'c piccolo', as they're not supposed to be more than one in an orchestra (one fore the player + 1 extra)
                                print("info: 2 copies for single instrument %s" % track.get_id())
                                track_to_print_count[track.get_id()] = 2
                            else:
                                playable_tracks.append(track)
            if len(playable_tracks) == 0:
                print("warning: no playable tracks found for player type %s" % musician_type_id)
            else:
                num_musicians_per_track = num_musicians / len(playable_tracks) + 1
                for track in playable_tracks:
                    print("info: %d copies of %s" % (num_musicians_per_track, track.get_id()))
                    track_to_print_count[track.get_id()] = num_musicians_per_track
        for track_id in stub_tracks:
            if track_id not in track_to_print_count.keys():
                track = Track(track_id, self.orchestra)
                count = 0
                if track.is_rare:
                    count = 0
                elif track.instrument.is_single():
                    # eg piano, string bass
                    count = 1
                track_to_print_count[track_id] = count
        return track_to_print_count
