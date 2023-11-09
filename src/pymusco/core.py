#!/usr/bin/env python3.8
"""

https://automatetheboringstuff.com/chapter13/
https://github.com/RussellLuo/pdfbookmarker/blob/master/add_bookmarks.py
"""
from typing import Dict, Any, List
import abc
import json
import re
from pathlib import Path
import PyPDF2  # sudo port install py27-pypdf2
from PIL import Image


# from enum import Enum

def dict_raise_on_duplicates(ordered_pairs):
    """Reject duplicate keys."""
    d = {}
    for k, v in ordered_pairs:
        if k in d:
            raise ValueError(f"duplicate key: {k!r}")
        else:
            d[k] = v
    return d


def load_commented_json(commented_json_file_path: Path):
    uncommented_json_contents = ''
    with open(commented_json_file_path, 'rt', encoding='utf-8') as file:

        for line in file.readlines():
            uncommented_line = re.sub('//.*$', '', line)
            # print("line : %s" % line[:-1])
            # print("uncommented_line : %s" % uncommented_line[:-1])
            uncommented_json_contents += uncommented_line
            # exit()
    # print(uncommented_json_contents)
    json_as_dict = json.loads(uncommented_json_contents, object_pairs_hook=dict_raise_on_duplicates)
    return json_as_dict


class InstrumentNotFound(Exception):
    """This exception means that the given instrument id is not known (it hasn't been registered in the instruments list)
    """

    def __init__(self, instrument_id):
        """
        instrument_id : str
            an instrument identifier (eg 'c piccolo')
        """
        self.instrument_id = instrument_id

    def __str__(self):
        return f"unknown instrument ('{self.instrument_id}'). Make sure this instrument has been registered in the instruments catalog."


def dict_to_instrument(instrument_as_dict):
    """
    Returns
    -------
    instrument : Instrument
        a musical instrument
    """
    # assert instrument_as_dict['format'] == 'pymusco.instrument.v1'
    is_rare = False
    if 'is_rare' in instrument_as_dict:
        is_rare = instrument_as_dict['is_rare']
    instrument = Instrument(uid=instrument_as_dict['uid'], player=instrument_as_dict['player'], order=instrument_as_dict['order'], is_rare=is_rare)
    return instrument


def instrument_to_dict(instrument):
    """
    Parameters
    ----------
    instrument : Instrument
        the instrument
    """
    instrument_as_dict = {}
    # instrument_as_dict['format'] = 'pymusco.instrument.v1'
    instrument_as_dict['uid'] = instrument.get_id()
    instrument_as_dict['player'] = instrument.player
    instrument_as_dict['order'] = instrument.order
    if instrument.is_rare:
        instrument_as_dict['is_rare'] = True

    return instrument_as_dict


class Instrument(object):

    def __init__(self, uid, player, order, is_rare=False):
        """ Constructor

        Parameters
        ----------
        uid : str
            unique identifier of a musical instrument, eg 'eb alto clarinet'
        player : str
            unique identifier of a musical instrument player, eg 'bassoonist'
        order : float
            value that is used to order instruments
        is_rare : bool
            defines if the instrument is rare (so rare its sheet music are never included in the prints)
        """
        assert isinstance(uid, str)
        assert isinstance(player, str)
        assert isinstance(order, float)

        self.uid = uid
        self.player = player
        self.order = order
        self.is_rare = is_rare
        self.tone = None

    def get_id(self):
        return self.uid

    def get_player(self):
        """
        :return str: the type of musician that can play this instrument
        """
        return self.player

    def is_single(self):
        single_instruments = ['c piccolo',
                              'english horn',
                              'bb bass clarinet',
                              'eb clarinet',
                              'bb soprano saxophone',
                              'eb baritone saxophone',
                              'c bass trombone',
                              'harp',
                              'piano',
                              'string bass',
                              'double bass',
                              'voice']
        return self.uid in single_instruments


def dict_to_orchestra(orchestra_as_dict):
    """
    Returns
    -------
    orchestra : Orchestra
        an instruments database
    """
    assert orchestra_as_dict['format'] == 'pymusco.orchestra.v1'
    instruments_list = orchestra_as_dict['instruments']
    instruments = []
    for instrument_dict in instruments_list:
        instruments.append(dict_to_instrument(instrument_dict))
    orchestra = Orchestra(instruments=instruments)
    return orchestra


def orchestra_to_dict(orchestra):
    """
    Parameters
    ----------
    orchestra : Orchestra
        the instruments database
    """
    orchestra_as_dict = {}
    orchestra_as_dict['format'] = 'pymusco.orchestra.v1'
    instruments_list = []
    orchestra_as_dict['instruments'] = instruments_list
    for instrument in orchestra.instruments:
        instruments_list.append(instrument_to_dict(instrument))
    return orchestra_as_dict


class Orchestra(object):
    """ Set of known instruments
    """
    def __init__(self, instruments):
        """ Constructor

        Parameters
        ----------
        instruments : list(Instrument)

        """
        assert isinstance(instruments, list)
        for instrument in instruments:
            assert isinstance(instrument, Instrument)
        self.instruments = instruments

    def get_instrument(self, instrument_id):
        """
        Parameters
        ----------
        instrument_id : str
            unique identifier of a musical instrument, eg 'eb alto clarinet'

        raises
        ------
            InstrumentNotFound
        """
        assert isinstance(instrument_id, str)
        if instrument_id == 'oboe':
            instrument_id = 'c oboe'
        if instrument_id == 'bassoon':
            instrument_id = 'c bassoon'
        if instrument_id == 'english horn':
            instrument_id = 'c english horn'
        for instrument in self.instruments:
            if instrument.get_id() == instrument_id:
                return instrument
        raise InstrumentNotFound(instrument_id)


def load_orchestra(orchestra_file_path: Path):
    """

    Parameters
    ----------
    orchestra_file_path : Path
        the path to the file describing the set of instruments in the orchestra

    Returns
    -------
    ochestra : Orchestra
    """
    return dict_to_orchestra(load_commented_json(orchestra_file_path))


# class Clef(Enum):
#     TREBLE = 1
#     BASS = 2


class Track(object):

    def __init__(self, track_id, orchestra):
        """
        :param str track_id: the identifier of a track in the form "bb trombone 2 bc"
        :param Orchestra orchestra:
        """
        assert isinstance(track_id, str)
        self.orchestra = orchestra
        self.instrument = None
        self.voice = None
        self.clef = None  # 'tc' for treble clef, 'bc' for bass clef
        self.is_solo = False
        self.is_disabled = False  # for tracks that we want to ignore (eg a track that is present in a stub more than once)
        parts = track_id.split(' ')
        instrument_first_part_index = 0
        instrument_last_part_index = len(parts) - 1
        # if len(parts[0]) <= 2:
        #    self.tone = parts[0]
        #   instrument_start_part_index = 1
        last_part = parts[-1]
        if last_part == 'disabled':
            self.is_disabled = True
            instrument_last_part_index -= 1
        last_part = parts[instrument_last_part_index]
        allowed_clefs = ['tc', 'bc']
        if last_part in allowed_clefs:
            self.clef = last_part
            instrument_last_part_index -= 1
        last_part = parts[instrument_last_part_index]
        if last_part.isdigit():
            self.voice = int(last_part)
            instrument_last_part_index -= 1
        last_part = parts[instrument_last_part_index]
        if last_part == 'solo':
            self.is_solo = True
            instrument_last_part_index -= 1
        instrument_id = ' '.join(parts[instrument_first_part_index:instrument_last_part_index + 1])
        self.instrument = orchestra.get_instrument(instrument_id)

    # def __init__(self, instrument, voice_number, clef):
    #    self.intrument = instrument
    #    self.voice_number = voice_number
    #    self.clef = clef

#    def __repr__(self):
#        return str(self.__dict__)

    def __str__(self):
        return self.id

    @property
    def id(self):
        return self.get_id()

    def __hash__(self):
        """ for use as dictionary key
        """
        return hash(self.get_id())

    def __eq__(self, other):
        """ for use as dictionary key
        """
        return hash(self.get_id()) == hash(other.get_id())

    def get_id(self):
        """
        :return str: the identifier of this track in the form "bb trombone 2 tc"
        """
        uid = self.instrument.get_id()
        if self.is_solo:
            uid = f'{uid:s} solo'
        if self.voice is not None:
            uid = f'{uid:s} {self.voice:d}'
        if self.clef is not None:
            uid = f'{uid:s} {self.clef:s}'
        if self.is_disabled:
            uid = f'{uid:s} disabled'
        return uid

    def __lt__(self, other):
        if self.instrument.order == other.instrument.order:
            if self.voice == other.voice:
                if self.clef == other.clef:
                    return False  # self and other are equal
                else:
                    if self.clef is None:
                        return True
                    elif other.clef is None:
                        return False
                    else:
                        return self.clef < other.clef
            else:
                if self.voice is None:
                    return True
                elif other.voice is None:
                    return False
                else:
                    return self.voice < other.voice
        else:
            return self.instrument.order < other.instrument.order

    @property
    def is_rare(self):
        if self.instrument.is_rare:
            return True
        else:
            if self.instrument.get_id() in ['c baritone horn', 'c bass']:
                if self.clef == 'tc':
                    # c basses are usually used by tubists, which on play bass clef
                    return True
            else:
                return False


class TableOfContents(object):
    orchestra: Orchestra
    track_to_page: Dict[Track, Any]

    def __init__(self, orchestra, track_id_to_page=None):
        """ Constructor

        Args
        ----

        orchestra: Orchestra
            the catalog of all possible instruments
        track_id_to_page: dict(str, int) or None
            a dictionary describing the tracks in this table of contents, and their associated page. A given track can only have at most one page while a page can have multiple tracks (typical example is percussion tracks)
        """
        # beware default mutable arguments such as dict, see https://docs.python-guide.org/writing/gotchas/
        assert isinstance(orchestra, Orchestra)
        self.orchestra = orchestra
        self.track_to_page = {}
        if track_id_to_page:
            for track_id, page in track_id_to_page.iteritems():
                track = Track(track_id, orchestra)
                self.track_to_page[track] = page

    def __repr__(self):
        return "{%s}" % ', '.join([f"{str(key)}: {value:d}" for key, value in self.track_to_page.items()])

    def __str__(self):
        return "[%s]" % ', '.join([f'"{str(key)}"' for key in self.track_to_page.keys()])  # pylint: disable=consider-iterating-dictionary, consider-using-f-string

    @property
    def tracks(self):
        return self.track_to_page.keys()

    def add_toc_item(self, track_id, page_index):
        """
        :param str track_id:
        :param int page_index:
        """
        assert isinstance(track_id, str)
        track = Track(track_id, self.orchestra)
        self.track_to_page[track] = page_index

    def get_track_ids(self):
        return [track.id for track in self.track_to_page.keys()]  # pylint: disable=consider-iterating-dictionary

    def get_tracks_for_page(self, page_index):
        tracks = []
        for track, page in self.track_to_page.items():
            if page == page_index:
                tracks.append(track)
        return tracks

    def get_tracks_first_page_index(self, tracks: List[Track]):
        """
        Parameters
        ----------

        tracks : list(Tracks)
            list of tracks

        Returns
        -------
        page_index : int
            the first page index for the given tracks
        """
        assert isinstance(tracks, list)
        assert len(tracks) > 0
        assert isinstance(tracks[0], Track)
        first_track = tracks[0]
        assert first_track in self.track_to_page.keys(), f"key '{str(first_track)}' not found in track_to_page dict {str(self)}"  # pylint: disable=consider-iterating-dictionary
        first_track_page_index = self.track_to_page[first_track]
        for track in tracks:
            assert isinstance(track, Track)
            assert self.track_to_page[track] == first_track_page_index
        return first_track_page_index

    def get_tracks_last_page_index(self, tracks, num_pages):
        """
        Parameters
        ----------

        tracks : list(Tracks)
            list of tracks

        Returns
        -------
        page_index : int
            the last page index for the given tracks
        """
        assert len(tracks) > 0
        for track in tracks:
            assert isinstance(track, Track)

        first_page_index = self.get_tracks_first_page_index(tracks)

        next_section_first_page_index = num_pages + 1
        for page_index in self.track_to_page.values():
            if page_index > first_page_index:
                next_section_first_page_index = min(next_section_first_page_index, page_index)
        # assert next_section_first_page_index <= num_pages, 'next_section_first_page_index = %d, num_pages=%d' % (next_section_first_page_index, num_pages)
        return next_section_first_page_index - 1

    def shift_page_indices(self, offset):
        """
        shifts the page numbers by a fixed value

        useful to adjust page numbers when a page is inserted or deleted
        """
        for track in self.track_to_page.keys():  # pylint: disable=consider-iterating-dictionary
            self.track_to_page[track] += offset

    # def copy(self, page_number_offset=0 ):
    #    toc = TableOfContents()
    #    return toc.


class ITrackSelector(object):
    """
    abstract class for the mechanism of track selection, which can vary.

    its main purpose is to compute for each track in the stub how many copies are wanted in the print
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_track_to_copy(self, stub_tracks):
        """
        computes for each stub_track the number of prints to do

        :param list(str) stub_tracks:
        :return dict(str, int): the number of prints to do for each stub_track
        """
        raise NotImplementedError('this classe is incomplete (missing get_track_to_copy method)')


def rotate_image(image_path, degrees_to_rotate, saved_location):
    """

    Rotate the given photo the amount of given degreesk, show it and save it

    @param image_path: The path to the image to edit
    @param degrees_to_rotate: The number of degrees to rotate the image
    @param saved_location: Path to save the cropped image

    """
    image_obj = Image.open(image_path)
    rotated_image = image_obj.rotate(degrees_to_rotate, expand=True)
    rotated_image.save(str(saved_location))
    # rotated_image.show()


def get_stub_tracks(src_stub_file_path, orchestra):
    """reads and returns the table of contents of the given stub pdf file.

    Parameters
    ----------
    src_stub_file_path : str
        the path to the input pdf stub file we want to extract the table of contents from
    orchestra : Orchestra
        the set of allowed instruments in the stub

    Returns
    -------
    table_of_contents : TableOfContents
    """
    # note: this function was implemented using trial & error. There must be cleaner and easier ways to do this.
    def find_page_number(page_contents_id: int, pdf_reader: PyPDF2.PdfReader):
        """Finds in the input pdf the page number for the given page contents id

        :param int page_contents_id:
        :param PyPDF2.PdfReader pdf_reader: the input pdf file
        """
        # print('looking for page with id %d' % page_contents_id)
        page_index = 0
        for page_object in pdf_reader.pages:
            assert isinstance(page_object, PyPDF2._page.PageObject)  # pylint: disable=protected-access
            # at this point, a page_object of the table of contents (with 23 links) looks like :
            # {'/Contents': IndirectObject(196, 0), '/Parent': IndirectObject(203, 0), '/Type': '/Page', '/Resources': IndirectObject(195, 0), '/MediaBox': [0, 0, 612, 792], '/Annots': [IndirectObject(171, 0), IndirectObject(172, 0), IndirectObject(173, 0), IndirectObject(174, 0), IndirectObject(175, 0), IndirectObject(176, 0), IndirectObject(177, 0), IndirectObject(178, 0), IndirectObject(179, 0), IndirectObject(180, 0), IndirectObject(181, 0), IndirectObject(182, 0), IndirectObject(183, 0), IndirectObject(184, 0), IndirectObject(185, 0), IndirectObject(186, 0), IndirectObject(187, 0), IndirectObject(188, 0), IndirectObject(189, 0), IndirectObject(190, 0), IndirectObject(191, 0), IndirectObject(192, 0), IndirectObject(193, 0)]}
            # while a normal page_object looks like
            # {'/Contents': IndirectObject(229, 0), '/Parent': IndirectObject(203, 0), '/Type': '/Page', '/Resources': IndirectObject(227, 0), '/MediaBox': [0, 0, 612, 792]}
            page_contents_indirect_obj = page_object.get("/Contents")
            assert isinstance(page_contents_indirect_obj, PyPDF2.generic.IndirectObject)
            # at this point, page_contents_indirect_obj has a value such as:
            # IndirectObject(229, 0)

            if page_contents_indirect_obj.idnum == page_contents_id:
                return page_index + 1  # converts 0 based index to 1-based index
            page_index += 1

        assert False, f"failed to find in the given input pdf file, a page whose contents id is {page_contents_id}"

    def get_pdf_toc_item_page(pdf_toc_item: Dict[str, Any], pdf_reader: PyPDF2.PdfReader) -> int:
        """
        :param dict(str, object) pdf_toc_item: an item of the pdf table of contents, such as
            {
              '/Title': u'c piccolo',
              '/Left': 155.354,
              '/Type': '/XYZ',
              '/Top': 669.191,
              '/Zoom': <PyPDF2.generic.NullObject object at 0x1110b1a90>,
              '/Page': IndirectObject(228, 0)
            }
        :param PyPDF2.PdfReader pdf_reader:
        :return int: the page number which is the target of the given pdf toc item.

        """
        # print('getting page number for table of contents item %s' % pdf_toc_item['/Title'])
        list(pdf_reader.pages)
        # print('number of pages : ', len(list(pdf_reader.pages)))
        linked_page_indirect_object = pdf_toc_item.get('/Page')  # pdf_toc_item['/Page'] would return a PyPDF2.generic.DictionaryObject instead of PyPDF2.generic.IndirectObject, probably because it would dereference the IndirectObject
        assert isinstance(linked_page_indirect_object, PyPDF2.generic.IndirectObject)

        # at this point, linked_page_indirect_object is of type PyPDF2.generic.IndirectObject, with a value such as:
        # IndirectObject(228, 0)
        print(dir(pdf_reader))
        linked_page_object = pdf_reader.resolved_objects[(0, linked_page_indirect_object.idnum)]
        # at this point, linked_page_object is of type PyPDF2.generic.DictionaryObject with a value such as :
        # {
        #   '/Contents': IndirectObject(229, 0),
        #   '/Parent': IndirectObject(203, 0),
        #   '/Type': '/Page',
        #   '/Resources': IndirectObject(227, 0),
        #   '/MediaBox': [0, 0, 612, 792]
        # }
        linked_page_content_id = linked_page_object.get('/Contents').idnum
        return find_page_number(linked_page_content_id, pdf_reader)

    with open(src_stub_file_path, 'rb') as stub_file:
        reader = PyPDF2.PdfReader(stub_file)
        pdf_toc = reader.outline
        # pdf_toc is a list of toc items like the following example :
        # [
        #     {'/Title': u'c piccolo', '/Left': 155.354, '/Type': '/XYZ', '/Top': 669.191, '/Zoom': <PyPDF2.generic.NullObject object at 0x1110b1a90>, '/Page': IndirectObject(29, 0)},
        #     {'/Title': u'c flute', '/Left': 155.354, '/Type': '/XYZ', '/Top': 669.191, '/Zoom': <PyPDF2.generic.NullObject object at 0x1110b1b10>, '/Page': IndirectObject(47, 0)}
        # ]

        stub_tracks = TableOfContents(orchestra)
        assert len(stub_tracks.get_track_ids()) == 0
        for pdf_toc_item in pdf_toc:
            track_page_number = get_pdf_toc_item_page(pdf_toc_item, reader)
            # assert False, 'the implementation of this function is not finished yet'
            track_ids = pdf_toc_item['/Title'].split('/')
            for track_id in track_ids:
                assert isinstance(track_id, str), f"unexpected type for track_id ({type(track_id)})"
                stub_tracks.add_toc_item(track_id, track_page_number)
        assert len(stub_tracks.tracks) > 0, f'no track found in {src_stub_file_path}'
        return stub_tracks
