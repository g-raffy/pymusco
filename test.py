"""

https://automatetheboringstuff.com/chapter13/
https://github.com/RussellLuo/pdfbookmarker/blob/master/add_bookmarks.py
"""
import os
import copy
# sudo port install py27-pypdf2
import PyPDF2

import pymusco

# https://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python/34116472#34116472

# Extract images from pdf: http://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python
# Extract images coded with CCITTFaxDecode in .net: http://stackoverflow.com/questions/2641770/extracting-image-from-pdf-with-ccittfaxdecode-filter
# TIFF format and tags: http://www.awaresystems.be/imaging/tiff/faq.html


def process_neonlight_serenade(src_pdf_file_path, dst_pdf_file_path):

    tmp_pdf_file_path = '/tmp/tmp1.pdf'
    pymusco.add_stamp(src_pdf_file_path, tmp_pdf_file_path, os.getenv('HOME') + '/data/Perso/MeltingNotes_work.git/partitions/mno-stamp.pdf')
    # https://github.com/RussellLuo/pdfbookmarker/blob/master/add_bookmarks.py

    # print(reader.outline)
    # [{'/Title': '1 Introduction', '/Left': 99.213, '/Type': '/XYZ', '/Top': 742.911, '/Zoom': ..., '/Page': IndirectObject(513, 0)},
    #  {'/Title': '2 Convolutional Neural Networks', '/Left': 99.213, '/Type': '/XYZ', '/Top': 742.911, '/Zoom': ..., '/Page': IndirectObject(554, 0)}, [{'/Title': '2.1 Linear Image Filters', '/Left': 99.213, '/Type': '/XYZ', '/Top': 486.791, '/Zoom': ..., '/Page': IndirectObject(554, 0)},
    #  {'/Title': '2.2 CNN Layer Types', '/Left': 70.866, '/Type': '/XYZ', '/Top': 316.852, '/Zoom': ..., '/Page': IndirectObject(580, 0)},
    # [{'/Title': '2.2.1 Convolutional Layers', '/Left': 99.213, '/Type': '/XYZ', '/Top': 562.722, '/Zoom': ..., '/Page': IndirectObject(608, 0)},
    #  {'/Title': '2.2.2 Pooling Layers', '/Left': 99.213, '/Type': '/XYZ', '/Top': 299.817, '/Zoom': ..., '/Page': IndirectObject(654, 0)},
    #  {'/Title': '2.2.3 Dropout', '/Left': 99.213, '/Type': '/XYZ', '/Top': 742.911, '/Zoom': ..., '/Page': IndirectObject(689, 0)},
    #  {'/Title': '2.2.4 Normalization Layers', '/Left': 99.213, '/Type': '/XYZ', '/Top': 193.779, '/Zoom': <PyPDF2.generic.NullObject object at 0x7fbe49d14350>, '/Page': IndirectObject(689, 0)}]

    pages_labels = [
        'c piccolo',
        'c flute',
        'oboe',
        'bassoon',
        'eb alto clarinet',
        'bb clarinet 1',
        'bb clarinet 2',
        'bb clarinet 3',
        'bb bass clarinet',
        'eb alto saxophone 1',
        'eb alto saxophone 2',
        'bb tenor saxophone',
        'eb baritone saxophone',
        'bb trumpet 1',
        'bb trumpet 2',
        'bb trumpet 3',
        'f horn 1',
        'f horn 2',
        'f horn 3',
        'eb horn 1',
        'eb horn 2',
        'eb horn 3',
        'c trombone 1'
        'c trombone 2'
        'bb trombone 1 tc'
        'bb trombone 1 bc'
        'bb trombone 2 tc'
        'bb trombone 2 bc'
        'c baritone horn bc'  # aka 'baritone'
        'c baritone horn tc'
        'bb baritone horn bc'
        'c tuba'
        'bb bass tc'
        'bb bass bc'
        'eb bass tc'
        'eb bass bc'
        'drum set'
        'clash cymbals'
        'concert bass drum'
        'suspended cymbal'
        'bongos'
        'shaker'
        'mallet percussion'
        'timpani'  # timbales

    ]
    bookmarks_tree = []
    page_index = 0
    for label in pages_labels:
        bookmarks_tree.append((label, page_index, []))
        page_index += 1
    #     bookmarks_tree = [
    #         (u'Piccolo', 0, []),
    #         (u'Flute', 1, []),
    #         (u'Oboe', 2, []),
    #         (u'Bassoon', 3, []),
    #         (u'Eb Clarinet', 4, []),
    #         (u'Bb Clarinet 1', 5, []),
    #         (u'Bb Clarinet 2', 5, []),
    #         (u'Bb Clarinet 3', 5, []),
    #         ]
    pymusco.addBookmarks(tmp_pdf_file_path, bookmarks_tree, dst_pdf_file_path)


def test(src_pdf_file_path, dst_pdf_file_path):
    writer = PyPDF2.PdfWriter()  # open output
    reader = PyPDF2.PdfReader(open(src_pdf_file_path, 'rb'))  # open input
    writer.add_page(reader.pages[0])  # insert page
    writer.addBookmark('Hello, World Bookmark', 0, parent=None)  # add bookmark
    outputStream = open(dst_pdf_file_path, 'wb')  # creating result pdf JCT
    writer.write(outputStream)  # writing to result pdf JCT
    outputStream.close()  # closing result JCT


# test(os.getenv('HOME')+'/Google Drive/partitions/talons/neonlight serenade.pdf', os.getenv('HOME')+'/toto/serenade.pdf')
# process_neonlight_serenade(os.getenv('HOME')+'/Google Drive/partitions/talons/neonlight serenade.pdf', os.getenv('HOME')+'/toto/serenade.pdf')

musician_count = {
    'flutist': 7,
    'clarinetist': 10,
    'hornist': 4,
    'oboeist': 1,
    'bassoonist': 2,
    'saxophonist': 10,
    'trombonist': 3,
    'trumpetist': 8,
    'euphonist': 3,
    'tubist': 1,
    'percussionist': 3
}

orchestra = pymusco.Harmony()

track_selector = pymusco.AutoTrackSelector(musician_count, orchestra)

scan_toc = pymusco.TableOfContents(orchestra, {
    'c piccolo': 1,
    'c flute': 3,
    'oboe': 5,
    'bassoon': 7,
    'bb clarinet 1': 9,
    'bb clarinet 2': 11,
    'bb clarinet 3': 13,
    'eb alto clarinet': 15,
    'bb bass clarinet': 17,
    'eb alto saxophone 1': 19,
    'eb alto saxophone 2': 21,
    'bb tenor saxophone': 23,
    'eb baritone saxophone': 25,
    'bb trumpet 1': 27,
    'bb trumpet 2': 29,
    'bb trumpet 3': 31,
    'f horn 1': 33,
    'f horn 2': 35,
    'c trombone 1': 37,
    'c trombone 2': 39,
    'c baritone horn bc': 41,
    'c baritone horn tc': 43,
    'bb baritone horn bc': 45,
    'c tuba': 47,
    'drum set': 49,
    'clash cymbals': 51,
    'concert bass drum': 51,
    'suspended cymbal': 51,
    'bongos': 51,
    'shaker': 51,
    'bells': 52,
    'xylophone': 52,
    'timpani': 53,
    'eb horn 1': 54,
    'eb horn 2': 56,
    'bb trombone 1 tc': 58,
    'bb trombone 1 bc': 60,
    'bb trombone 2 tc': 62,
    'bb trombone 2 bc': 64,
    'bb bass tc': 66,
    'bb bass bc': 68,
    'eb bass tc': 70,
    'eb bass bc': 72,
    })


pymusco.scan_to_stub(os.getcwd() + '/samples/666-japanese-tango.pdf', './results/stubs/666-japanese-tango.pdf',
                     scan_toc,
                     title='Japanese Tango',
                     orchestra=orchestra,
                     stamp_file_path= os.getcwd() + '/samples/stamp.pdf',
                     scale=0.5,
                     tx=14.0,
                     ty=4.0,
                     rotate_images=True)


stub_toc = copy.deepcopy(scan_toc)
NUM_TOC_PAGES = 2
stub_toc.shift_page_indices(NUM_TOC_PAGES)

pymusco.stub_to_print(os.getcwd() + '/results/stubs/666-japanese-tango.pdf', os.getcwd() + '/results/prints/666-japanese-tango.pdf', track_selector, orchestra, stub_toc=stub_toc)

