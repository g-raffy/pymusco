from pathlib import Path
import re
import json
from .main import StampDesc
from .main import scan_to_stub
from .main import stub_to_print
from .core import TableOfContents
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


def dict_to_piece(piece_as_dict, orchestra, settings):
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
    stamp_file_path = None
    if 'stamp_path' in piece_as_dict.keys():
        stamp_file_path = settings.stamps_root + '/' + piece_as_dict['stamp_path']

    piece = Piece(uid=uid, title=title, orchestra=orchestra, scan_toc=scan_toc, scans_dir=settings.scans_dir, stubs_dir=settings.stubs_dir, prints_dir=settings.prints_dir, missing_tracks=missing_tracks, stamp_file_path=stamp_file_path)
    return piece


def piece_to_dict(piece, settings):
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
        piece_as_dict['stamp_path'] = piece.stamp_file_path.relative_to(settings.stamps_root)
    return piece_as_dict
    

def load_piece_description(piece_desc_file_path, orchestra, settings):
    """

    Parameters
    ----------
    piece_desc_file_path : Path
        the path to the file describing the scanned pdf sheet music

    Returns
    -------
    scan_description : Piece
    """
    uncommented_json_contents = ''
    with open(piece_desc_file_path, 'rt') as file:

        for line in file.readlines():
            uncommented_line = re.sub('//.*$', '', line)
            # print("line : %s" % line[:-1])
            # print("uncommented_line : %s" % uncommented_line[:-1])
            uncommented_json_contents += uncommented_line
            # exit()
    # print(uncommented_json_contents)
    piece_as_dict = json.loads(uncommented_json_contents)
    return dict_to_piece(piece_as_dict, orchestra, settings)

def save_piece_description(piece, piece_desc_file_path, settings):
    """
    Parameters
    ----------
    piece : Piece
        the pice description to save 
    piece_desc_file_path : Path
        the path to the file describing the scanned pdf sheet music
    """
    piece_as_dict = piece_to_dict(piece, settings)
    with open(piece_desc_file_path, 'w') as file:
        json.dump(piece_as_dict, file)

class Vector2(object):

    def __init__(self, x, y):
        assert isinstance(x, float)
        assert isinstance(y, float)
        self.x = x
        self.y = y

class Piece(object):

    def __init__(self, uid, title, orchestra, scan_toc, scans_dir, stubs_dir, prints_dir, missing_tracks={}, stamp_file_path=None):
        """
        Parameters
        ----------
        uid : int
            unique number identifying a track

        :param pymusco.Orchestra orchestra: the inventory of musical instruments
        :param dict(str, str): for each missing track, the reason why it's missing
        """
        assert len(scan_toc.tracks) > 0
        assert isinstance(scans_dir, Path)
        assert isinstance(stubs_dir, Path)
        assert isinstance(prints_dir, Path)
        self.uid = uid  # match.group('uid')
        self.title = title  # match.group('title')
        self.orchestra = orchestra
        self.scan_toc = scan_toc
        self.scans_dir = scans_dir
        self.stubs_dir = stubs_dir
        self.prints_dir = prints_dir
        self.missing_tracks = missing_tracks
        self.stamp_file_path = stamp_file_path
        self.stamp_scale = 0.5
        self.stamp_pos = Vector2(14.0, 4.0)
    @property
    def label(self):
        return '%03d-%s' % (self.uid, self.title.replace(' ', '-'))

    def build_stub(self):

        stamp_desc = None
        if self.stamp_file_path is not None:
            stamp_desc = StampDesc(
                file_path=self.stamp_file_path,
                scale=0.5,
                tx=14.0,
                ty=4.0)

        scan_to_stub(
            src_scanned_pdf_file_path=(self.scans_dir / self.label).with_suffix('.pdf'),
            dst_stub_pdf_file_path=(self.stubs_dir / self.label).with_suffix('.pdf'),
            toc=self.scan_toc,
            title=self.label,
            orchestra=self.orchestra,
            stamp_desc=stamp_desc
        )

    # def get_stub_toc(self):
    #     """
    #     :return pymusco.TableOfContents:
    #     """
    #     stub_toc = copy.deepcopy(self.scan_toc)
    #     num_toc_pages = 1  # TODO: remove hardcoded value
    #     stub_toc.shift_page_indices(num_toc_pages)
    #     return stub_toc

    def build_print(self, track_selector, prints_dir=None):
        if prints_dir is None:
            prints_dir = self.prints_dir

        stub_to_print(
            src_stub_file_path=self.stubs_dir + '/' + self.label + '.pdf',
            dst_print_file_path=prints_dir + '/' + self.label + '.pdf',
            track_selector=track_selector,
            orchestra=self.orchestra)

    def extract_single_track(self, track_id, output_dir=None):
        """
        :param str track_id: eg 'bb trumpet 3'
        """
        track_selector = SingleTrackSelector(track_id, self.orchestra)
        if output_dir is None:
            dst_dir = self.prints_dir
        else:
            dst_dir = output_dir
        stub_to_print(
            src_stub_file_path=self.stubs_dir + '/' + self.label + '.pdf',
            dst_print_file_path=dst_dir + '/' + self.label + '.' + track_id + '.pdf',
            track_selector=track_selector,
            orchestra=self.orchestra)

    def build_all(self, musician_count):
        self.build_stub()
        self.build_print(musician_count)


class Pieces(object):

    def __init__(self):
        self.pieces = {}

    def add(self, piece):
        self.pieces[piece.uid] = piece

    def get(self, uid):
        return self.pieces[uid]

