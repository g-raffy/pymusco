
from .core import ITrackSelector
from .core import Track


class ManualTrackSelector(ITrackSelector):
    """
    a track selector that extracts the given track.
    """

    def __init__(self, track_to_print_count, orchestra, percussion_count):
        """
        :param dict(str, int) track_to_print_count:
        """
        self.track_to_print_count = track_to_print_count
        self.orchestra = orchestra
        self.percussion_count = percussion_count

    def get_track_to_copy(self, stub_tracks):
        track_to_print_count = dict.copy(self.track_to_print_count)
        for track_id in stub_tracks:
            track = Track(track_id, self.orchestra)
            if not track.is_disabled:
                if track.instrument.get_player() == 'percussionist':
                    track_to_print_count[track.get_id()] = self.percussion_count
        return track_to_print_count