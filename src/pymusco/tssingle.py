'''
Created on Sep 9, 2018

@author: graffy
'''

from .core import ITrackSelector
from .core import Track


class SingleTrackSelector(ITrackSelector):
    """
    a track selector that extracts the given track.
    """

    def __init__(self, selected_track_id, orchestra):
        """
        :param str selected_track:
        :param Orchestra orchestra: the inventory of musical instruments
        """
        self.selected_track = Track(selected_track_id, orchestra)
        self.orchestra = orchestra

    def get_track_to_copy(self, stub_tracks):
        assert self.selected_track.get_id() in stub_tracks, f"how can I select a track that is not in the stub : {self.selected_track.get_id()}"
        track_to_print_count = {self.selected_track.get_id(): 1}
        return track_to_print_count
