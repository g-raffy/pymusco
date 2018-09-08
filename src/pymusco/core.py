"""

https://automatetheboringstuff.com/chapter13/
https://github.com/RussellLuo/pdfbookmarker/blob/master/add_bookmarks.py
"""
# sudo port install py27-pypdf2
import PyPDF2
# from PyPDF2 import PdfFileMerger, PdfFileReader
from PIL import Image


# from wand.image import Image
import re


# from enum import Enum


class Instrument(object):

    def __init__(self, uid, player, order, is_rare=False):
        """
        :param str uid: unique identififer of a musical instrument, eg 'eb alto clarinet'
        :para float order: value that is used to order instruments
        """
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
                              'eb baritone saxophone',
                              'c bass trombone',
                              'piano',
                              'string bass']
        return self.uid in single_instruments


class Orchestra(object):
    
    def __init__(self, instruments):
        self.instruments = instruments

    def get_instrument(self, instrument_id):
        for instrument in self.instruments:
            if instrument.get_id() == instrument_id:
                return instrument
        assert False, 'unknown instrument id : %s' % instrument_id
        return None


class Harmony(Orchestra):

    def __init__(self):
        instruments = [
            Instrument('c piccolo', player='flutist', order=1.000),
            Instrument('c flute', player='flutist', order=1.001),
            Instrument('oboe', player='oboeist', order=2.000),
            Instrument('english horn', player='oboeist', order=2.001),
            Instrument('bassoon', player='bassoonist', order=3.000),
            Instrument('eb clarinet', player='clarinetist', order=4.000),  # aka Eb sopranino clarinet
            Instrument('eb alto clarinet', player='clarinetist', order=4.001, is_rare=True),
            Instrument('bb clarinet', player='clarinetist', order=4.002),  # aka Bb soprano clarinet, most common clarinet
            Instrument('bb bass clarinet', player='clarinetist', order=4.003),
            Instrument('bb contrabass clarinet', player='clarinetist', order=4.004, is_rare=True),
            Instrument('eb contrabass clarinet', player='clarinetist', order=4.005, is_rare=True),

            Instrument('eb alto saxophone', player='saxophonist', order=5.000),
            Instrument('bb tenor saxophone', player='saxophonist', order=5.001),
            Instrument('eb baritone saxophone', player='saxophonist', order=5.002),

            Instrument('bb trumpet', player='trumpetist', order=6.000),
            Instrument('bb cornet', player='trumpetist', order=6.001),

            Instrument('f horn', player='hornist', order=7.000),
            Instrument('eb horn', player='hornist', order=7.001, is_rare=True),
            
            Instrument('c trombone', player='trombonist', order=8.000),
            Instrument('bb trombone', player='trombonist', order=8.001, is_rare=True),
            Instrument('c bass trombone', player='trombonist', order=8.002),

            Instrument('c baritone horn', player='euphonist', order=9.000),  # aka 'baritone' 'euphonium'
            Instrument('bb baritone horn', player='euphonist', order=9.001),  # aka 'baritone' 'euphonium'

            Instrument('c tuba', player='tubist', order=10.000),  # actually a f tuba but players read c parts
            Instrument('bb contrabass tuba', player='tubist', order=10.001),
            Instrument('c bass', player='tubist', order=10.002),
            Instrument('bb bass', player='tubist', order=10.003),
            Instrument('eb bass', player='tubist', order=10.004, is_rare=True),

            Instrument('drum set', player='percussionist', order=11.001),
            Instrument('crash cymbals', player='percussionist', order=11.002),
            Instrument('concert bass drum', player='percussionist', order=11.003),
            Instrument('suspended cymbal', player='percussionist', order=11.004),
            Instrument('bongos', player='percussionist', order=11.005),
            Instrument('shaker', player='percussionist', order=11.006),
            Instrument('snare drum', player='percussionist', order=11.007),
            Instrument('tambourine', player='percussionist', order=11.008),
            Instrument('small crash cymbals', player='percussionist', order=11.009),
            Instrument('ratchet', player='percussionist', order=11.010),
            Instrument('flexatone', player='percussionist', order=11.011),
            Instrument('temple blocks', player='percussionist', order=11.012),
            Instrument('wood block', player='percussionist', order=11.013),
            Instrument('cymbals', player='percussionist', order=11.014),  # TODO: check if they're not the same as crash cymbals
            Instrument('side drum', player='percussionist', order=11.015),
            Instrument('gong', player='percussionist', order=11.016),
            Instrument('castanets', player='percussionist', order=11.017),
            
            Instrument('bells', player='percussionist', order=11.100),  # mallet percussion
            Instrument('bell tree', player='percussionist', order=11.101),
            Instrument('chimes', player='percussionist', order=11.102),
            Instrument('wind chimes', player='percussionist', order=11.103),
            Instrument('triangle', player='percussionist', order=11.104),
            Instrument('sleigh bells', player='percussionist', order=11.105),
            Instrument('mallet percussion', player='percussionist', order=11.200),
            Instrument('xylophone', player='percussionist', order=11.201),
            Instrument('marimba', player='percussionist', order=11.202),
            Instrument('vibraphone', player='percussionist', order=11.203),
            Instrument('glockenspiel', player='percussionist', order=11.204),
            Instrument('timpani', player='percussionist', order=11.300),  # timbales

            Instrument('string bass', player='bassist', order=12.000, is_rare=True),
        
            Instrument('piano', player='pianist', order=13.000)]
        
        Orchestra.__init__(self, instruments)


"""
class Clef(Enum):
    TREBLE = 1
    BASS = 2
"""


class Track(object):
    
    def __init__(self, track_id, orchestra):
        """
        :param str track_id: the identifier of a track in the form "bb trombone 2 bc"
        :param Orchestra orchestra:
        """
        self.orchestra = orchestra
        self.instrument = None
        self.voice = None
        self.clef = None  # 'tc' for treble clef, 'bc' for bass clef
        parts = track_id.split(' ')
        instrument_first_part_index = 0
        instrument_last_part_index = len(parts) - 1
        # if len(parts[0]) <= 2:
        #    self.tone = parts[0]
        #   instrument_start_part_index = 1
        last_part = parts[-1]
        allowed_clefs = ['tc', 'bc']
        if last_part in allowed_clefs:
            self.clef = last_part
            instrument_last_part_index -= 1
        last_part = parts[instrument_last_part_index]
        if last_part.isdigit():
            self.voice = int(last_part)
            instrument_last_part_index -= 1
        instrument_id = ' '.join(parts[instrument_first_part_index:instrument_last_part_index + 1])
        self.instrument = orchestra.get_instrument(instrument_id)

    # def __init__(self, instrument, voice_number, clef):
    #    self.intrument = instrument
    #    self.voice_number = voice_number
    #    self.clef = clef
    
    def get_id(self):
        """
        :return str: the identifier of this track in the form "bb trombone 2 tc"
        """
        uid = self.instrument.get_id()
        if self.voice is not None:
            uid = '%s %d' % (uid, self.voice)
        if self.clef is not None:
            uid = '%s %s' % (uid, self.clef)
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


def get_bookmarks_tree(bookmarks_filename):
    """Get bookmarks tree from TEXT-format file
    Bookmarks tree structure:
        >>> get_bookmarks_tree('sample_bookmarks.txt')
        [(u'Foreword', 0, []), (u'Chapter 1: Introduction', 1, [(u'1.1 Python', 1, [(u'1.1.1 Basic syntax', 1, []), (u'1.1.2 Hello world', 2, [])]), (u'1.2 Exercises', 3, [])]), (u'Chapter 2: Conclusion', 4, [])]
    The above test result may be more readable in the following format:
        [
            (u'Foreword', 0, []),
            (u'Chapter 1: Introduction', 1,
                [
                    (u'1.1 Python', 1,
                        [
                            (u'1.1.1 Basic syntax', 1, []),
                            (u'1.1.2 Hello world', 2, [])
                        ]
                    ),
                    (u'1.2 Exercises', 3, [])
                ]
            ),
            (u'Chapter 2: Conclusion', 4, [])
        ]
    Thanks Stefan, who share us a perfect solution for Python tree.
    See http://stackoverflow.com/questions/3009935/looking-for-a-good-python-tree-data-structure
    Since dictionary in Python is unordered, I use list instead now.
    Also thanks Caicono, who inspiring me that it's not a bad idea to record bookmark titles and page numbers by hand.
    See here: http://www.caicono.cn/wordpress/2010/01/%E6%80%9D%E8%80%83%E5%85%85%E5%88%86%E5%86%8D%E8%A1%8C%E5%8A%A8-python%E8%AF%95%E6%B0%B4%E8%AE%B0.html
    And I think it's the only solution for scan version PDFs to be processed automatically.
    """

    # bookmarks tree
    tree = []

    # the latest nodes (the old node will be replaced by a new one if they have the same level)
    #
    # each item (key, value) in dictionary represents a node
    # `key`: the level of the node
    # `value`: the children list of the node
    latest_nodes = {0: tree}

    prev_level = 0
    for line in codecs.open(bookmarks_filename, 'r', encoding='utf-8'):
        res = re.match(r'(\+*)\s*?"([^"]+)"\s*\|\s*(\d+)', line.strip())
        if res:
            pluses, title, pagenum = res.groups()
            cur_level = len(pluses)  # plus count stands for level
            cur_node = (title, int(pagenum) - 1, [])

            if not (cur_level > 0 and cur_level <= prev_level + 1):
                raise Exception('plus (+) count is invalid here: %s' % line.strip())
            else:
                # append the current node into its parent node (with the level `cur_level` - 1)
                latest_nodes[cur_level - 1].append(cur_node)

            latest_nodes[cur_level] = cur_node[2]
            prev_level = cur_level

    return tree


class TableOfContents(object):
    
    def __init__(self, label_to_page):
        """
        :param dict(str, int) label_to_page:
        """
        self.label_to_page = label_to_page
    
    def add_toc_item(self, label, page_index):
        """
        :param str label:
        :param int page_index:
        """
        self.label_to_page[label] = page_index
    
    def get_labels(self):
        return self.label_to_page.keys()
    
    def get_label(self, page_index):
        for label, page in self.label_to_page.iteritems():
            if page == page_index:
                return label
        return None
    
    def get_label_first_page_index(self, label):
        return self.label_to_page[label]
    
    def get_label_last_page_index(self, label, num_pages):
        first_page_index = self.get_label_first_page_index(label)
        
        next_section_first_page_index = num_pages + 1
        for page_index in self.label_to_page.itervalues():
            if page_index > first_page_index:
                next_section_first_page_index = min(next_section_first_page_index, page_index)
        return next_section_first_page_index - 1
    
    def shift_page_indices(self, offset):
        """
        shifts the page numbers by a fixed value
        
        useful to adjust page numbers when a page is inserted or deleted
        """
        for label in self.label_to_page.iterkeys():
            self.label_to_page[label] += offset

    # def copy(self, page_number_offset=0 ):
    #    toc = TableOfContents()
    #    return toc.


def rotate_image(image_path, degrees_to_rotate, saved_location):
    """

    Rotate the given photo the amount of given degreesk, show it and save it

    @param image_path: The path to the image to edit
    @param degrees_to_rotate: The number of degrees to rotate the image
    @param saved_location: Path to save the cropped image

    """
    image_obj = Image.open(image_path)
    rotated_image = image_obj.rotate(degrees_to_rotate, expand=True)
    rotated_image.save(saved_location)
    # rotated_image.show()


def get_stub_tracks(src_stub_file_path):
    """
    :param str src_stub_file_path:
    :return TableOfContents:
    """
    with open(src_stub_file_path, 'rb') as stub_file:
        reader = PyPDF2.PdfFileReader(stub_file)

        toc = reader.outlines
        # print(toc)
        """
        [
            {'/Title': u'c piccolo', '/Left': 155.354, '/Type': '/XYZ', '/Top': 669.191, '/Zoom': <PyPDF2.generic.NullObject object at 0x1110b1a90>, '/Page': IndirectObject(29, 0)},
            {'/Title': u'c flute', '/Left': 155.354, '/Type': '/XYZ', '/Top': 669.191, '/Zoom': <PyPDF2.generic.NullObject object at 0x1110b1b10>, '/Page': IndirectObject(47, 0)}
        ]
        """
        stub_tracks = TableOfContents
        for toc_item in toc:
            assert False, 'the implementation of this function is not finished yet'
            track_page_number = 2  # TODO: find the proper page number
            stub_tracks.add_toc_item(toc_item['/Title'], track_page_number)

        return(stub_tracks)


def compute_track_count(stub_tracks, musician_count):
    """
    computes for each stub_track the number of prints to do, given the musician count
    
    :param list(str) stub_tracks:
    :param dict(str, int) musician_count:
    :return dict(str, int): the number of prints to do for each stub_track
    """
    orchestra = Harmony()
    track_to_print_count = {}
    for musician_type_id, num_musicians in musician_count.iteritems():
        print('musician_type_id = %s' % musician_type_id)
        # collect the tracks than can be played by these musicians
        playable_tracks = []
        for track_id in stub_tracks:
            track = Track(track_id, orchestra)
            # print('processing track %s' % track.get_id())
            # print('track.instrument.get_player() = %s' % track.instrument.get_player())
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
            track = Track(track_id, orchestra)
            count = 0
            if track.is_rare:
                count = 0
            elif track.instrument.is_single():
                # eg piano, string bass
                count = 1
            track_to_print_count[track_id] = count
    return track_to_print_count
