from pathlib import Path
import os
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
    # check that the keys used in this dictionary are known
    for key in toc_as_dict.keys():
        if key not in ['format', 'track_id_to_page']:
            raise KeyError('unexpected key in toc dictionary : %s' % (key))

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
    allowed_image_suffixes = ['.pdf', '.png']
    if stamp_file_path.is_absolute():
        abs_stamp_file_path = stamp_file_path
    else:
        abs_stamp_file_path = piece_desc_file_path.parent.resolve() / stamp_file_path
    if not abs_stamp_file_path.exists():
        raise Exception("The stamp file '%s' is missing (file not found)." % (abs_stamp_file_path))
    if abs_stamp_file_path.suffix not in allowed_image_suffixes:
        raise Exception("Unsupported image format for stamp '%s' (allowed formats : %s) " % (abs_stamp_file_path, str(allowed_image_suffixes)))
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
    missing_tracks = None
    if 'missing_tracks' in piece_as_dict:
        missing_tracks = piece_as_dict['missing_tracks']
    stamp_descs = []
    if 'stamp_descs' in piece_as_dict.keys():
        for stamp_desc_as_dict in piece_as_dict['stamp_descs']:
            stamp_descs.append(dict_to_stamp_desc(stamp_desc_as_dict, piece_desc_file_path))
    page_info_line_y_pos = 1.0  # in centimeters, relative to the bottom of the page
    if 'page_info_line_y_pos' in piece_as_dict.keys():
        page_info_line_y_pos = piece_as_dict['page_info_line_y_pos']

    piece = Piece(uid=uid, title=title, orchestra=orchestra, scan_toc=scan_toc, missing_tracks=missing_tracks, stamp_descs=stamp_descs, page_info_line_y_pos=page_info_line_y_pos)
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

    def __init__(self, uid, title, orchestra, scan_toc, missing_tracks={}, stamp_descs=[], page_info_line_y_pos=1.0):
        """
        Parameters
        ----------
        uid : int
            unique number identifying a track

        :param pymusco.Orchestra orchestra: the inventory of musical instruments
        :param dict(str, str): for each missing track, the reason why it's missing
        :param list(StampDesc): stamp_descs
        :param float page_info_line_y_pos: y position of the status line relative to the bottom of the page
        """
        assert len(scan_toc.tracks) > 0
        self.uid = uid  # match.group('uid')
        self.title = title  # match.group('title')
        self.orchestra = orchestra
        self.scan_toc = scan_toc
        self.missing_tracks = missing_tracks
        self.stamp_descs = stamp_descs
        self.page_info_line_y_pos = page_info_line_y_pos
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


class CatalogPiece(object):

    def __init__(self, piece, catalog):
        self.piece = piece
        self.catalog = catalog

    @property
    def uid(self):
        return self.piece.uid

    def build_stub(self):

        scan_to_stub(
            src_scanned_pdf_file_path=(self.catalog.scans_dir / self.piece.label).with_suffix('.pdf'),
            dst_stub_pdf_file_path=(self.catalog.stubs_dir / self.piece.label).with_suffix('.pdf'),
            toc=self.piece.scan_toc,
            title=self.piece.label,
            orchestra=self.catalog.orchestra,
            stamp_descs=self.piece.stamp_descs,
            page_info_line_y_pos=self.piece.page_info_line_y_pos
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
            prints_dir = self.catalog.prints_dir

        stub_to_print(
            src_stub_file_path=self.catalog.stubs_dir / (self.piece.label + '.pdf'),
            dst_print_file_path=prints_dir / (self.piece.label + '.pdf'),
            track_selector=track_selector,
            orchestra=self.catalog.orchestra)

    def extract_single_track(self, track_id, output_dir=None):
        """
        :param str track_id: eg 'bb trumpet 3'
        """
        track_selector = SingleTrackSelector(track_id, self.catalog.orchestra)
        if output_dir is None:
            dst_dir = self.catalog.prints_dir
        else:
            dst_dir = output_dir
        stub_to_print(
            src_stub_file_path=self.catalog.stubs_dir / (self.piece.label + '.pdf'),
            dst_print_file_path=dst_dir / (self.piece.label + '.' + track_id + '.pdf'),
            track_selector=track_selector,
            orchestra=self.catalog.orchestra)

    def build_all(self, musician_count):
        self.build_stub()
        self.build_print(musician_count)


class Catalog(object):
    """ a collection of pieces that share the same locations, same orchestra, etc...
    """
    def __init__(self, piece_desc_dir, scans_dir, stubs_dir, prints_dir, orchestra):
        """
        Parammeters
        -----------
        piece_desc_dir : Path
            the directory that contains the piece description files
        scans_dir : Path
            the directory that contains the scan pdf files
        stubs_dir : Path
            the directory that contains the stub pdf files
        prints_dir : Path
            the directory that contains the prints pdf files
        orchestra : Orchestra
            the instruments database that this catalog uses
        """
        self.piece_desc_dir = piece_desc_dir
        self.scans_dir = scans_dir
        self.stubs_dir = stubs_dir
        self.prints_dir = prints_dir
        self.orchestra = orchestra

        self.pieces = {}
        for file in os.listdir(self.piece_desc_dir):
            if file.endswith(".desc"):
                desc_file_path = self.piece_desc_dir / file
                piece = load_piece_description(desc_file_path, orchestra)
                self.add(CatalogPiece(piece, self))

    def add(self, piece):
        self.pieces[piece.uid] = piece

    def get(self, uid):
        return self.pieces[uid]
