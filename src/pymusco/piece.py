from pathlib import Path
import re
import json
from .main import StampDesc
from .main import scan_to_stub
from .main import stub_to_print
from .core import TableOfContents
from .core import load_commented_json
from .tssingle import SingleTrackSelector

def dict_to_toc(toc_as_dict, orchestra):
    """
    Parameters
    ----------
    orchestra : Orchestra
        the instruments database
    """
    assert toc_as_dict['format'] == 'pymusco.toc.v1'
    toc = TableOfContents(orchestra=orchestra, track_id_to_page=None)
    for track_id, page_index in toc_as_dict['track_id_to_page'].items():
        toc.add_toc_item(track_id, page_index)
    return toc


def toc_to_dict(toc):
    """
    Parameters
    ----------
    toc : TableOfContents
        the table of contents to export as dict
    """
    toc_as_dict = {}
    toc_as_dict['format'] = 'pymusco.toc.v1'
    toc_as_dict['track_id_to_page'] = {}
    for track, page_index in toc.track_id_to_page:
        toc_as_dict['track_id_to_page'][track.id] = page_index
    return toc_as_dict


def dict_to_stamp_desc(stamp_desc_as_dict, piece_desc_file_path):
    """
    """
    abs_stamp_file_path = None
    stamp_file_path = Path(stamp_desc_as_dict['stamp_image_path'])
    allowed_image_suffixes = [ '.pdf', '.png' ]
    if stamp_file_path.is_absolute():
        abs_stamp_file_path = stamp_file_path
    else:
        abs_stamp_file_path = piece_desc_file_path.parent.resolve() / stamp_file_path
    if not abs_stamp_file_path.exists():
        raise Exception("The stamp file '%s' is missing (file not found)." % (abs_stamp_file_path) )
    if abs_stamp_file_path.suffix not in allowed_image_suffixes:
        raise Exception("Unsupported image format for stamp '%s' (allowed formats : %s) " % (abs_stamp_file_path, str(allowed_image_suffixes)) )
    return StampDesc(file_path=abs_stamp_file_path,
        scale=stamp_desc_as_dict['scale'],
        tx=stamp_desc_as_dict['tx'],
        ty=stamp_desc_as_dict['ty'])

def dict_to_piece(piece_as_dict, orchestra, piece_desc_file_path):
    """
    Parameters
    ----------
    orchestra : Orchestra
        the instruments database
    """
    assert piece_as_dict['format'] == 'pymusco.piece_description.v1'
    uid = piece_as_dict['uid']
    title = piece_as_dict['title']
    scan_toc = dict_to_toc(piece_as_dict['scan_toc'], orchestra)
    missing_tracks = piece_as_dict['missing_tracks']
    stamp_descs = []
    if 'stamp_descs' in piece_as_dict.keys():
        for stamp_desc_as_dict in piece_as_dict['stamp_descs']:
            stamp_descs.append(dict_to_stamp_desc(stamp_desc_as_dict, piece_desc_file_path))

    piece = Piece(uid=uid, title=title, orchestra=orchestra, scan_toc=scan_toc, missing_tracks=missing_tracks, stamp_descs=stamp_descs)
    return piece


def piece_to_dict(piece):
    """
    Parameters
    ----------
    piece : Piece
        the piece description to export as dict
    """
    piece_as_dict = {}
    piece_as_dict['format'] = 'pymusco.piece_description.v1'
    piece_as_dict['uid'] = piece.uid
    piece_as_dict['title'] = piece.title
    piece_as_dict['scan_toc'] = toc_to_dict(piece.scan_toc)
    piece_as_dict['missing_tracks'] = piece.missing_tracks
    if piece.stamp_file_path:
        piece_as_dict['stamp_path'] = piece.stamp_file_path
    return piece_as_dict
    

def load_piece_description(piece_desc_file_path, orchestra):
    """

    Parameters
    ----------
    piece_desc_file_path : Path
        the path to the file describing the scanned pdf sheet music

    Returns
    -------
    scan_description : Piece
    """
    return dict_to_piece(load_commented_json(piece_desc_file_path), orchestra, piece_desc_file_path)

def save_piece_description(piece, piece_desc_file_path):
    """
    Parameters
    ----------
    piece : Piece
        the pice description to save 
    piece_desc_file_path : Path
        the path to the file describing the scanned pdf sheet music
    """
    piece_as_dict = piece_to_dict(piece)
    with open(piece_desc_file_path, 'w') as file:
        json.dump(piece_as_dict, file)

class Vector2(object):

    def __init__(self, x, y):
        assert isinstance(x, float)
        assert isinstance(y, float)
        self.x = x
        self.y = y

class Piece(object):

    def __init__(self, uid, title, orchestra, scan_toc, missing_tracks={}, stamp_descs=[]):
        """
        Parameters
        ----------
        uid : int
            unique number identifying a track

        :param pymusco.Orchestra orchestra: the inventory of musical instruments
        :param dict(str, str): for each missing track, the reason why it's missing
        :param list(StampDesc): stamp_descs
        """
        assert len(scan_toc.tracks) > 0
        self.uid = uid  # match.group('uid')
        self.title = title  # match.group('title')
        self.orchestra = orchestra
        self.scan_toc = scan_toc
        self.missing_tracks = missing_tracks
        self.stamp_descs = stamp_descs
        # self.stamp_scale = 0.5
        # self.stamp_pos = Vector2(14.0, 4.0)
    @property
    def label(self):
        return '%03d-%s' % (self.uid, self.title.replace(' ', '-'))

    # def get_stub_toc(self):
    #     """
    #     :return pymusco.TableOfContents:
    #     """
    #     stub_toc = copy.deepcopy(self.scan_toc)
    #     num_toc_pages = 1  # TODO: remove hardcoded value
    #     stub_toc.shift_page_indices(num_toc_pages)
    #     return stub_toc


class Pieces(object):

    def __init__(self):
        self.pieces = {}

    def add(self, piece):
        self.pieces[piece.uid] = piece

    def get(self, uid):
        return self.pieces[uid]

