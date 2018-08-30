"""

https://automatetheboringstuff.com/chapter13/
https://github.com/RussellLuo/pdfbookmarker/blob/master/add_bookmarks.py
"""
# sudo port install py27-pypdf2
import PyPDF2
from PyPDF2 import PdfFileMerger, PdfFileReader

import tesseract

#from wand.image import Image
import io
import os
import cv2
from PIL import Image
import struct
import subprocess
import pymusco
import sys

# https://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python/34116472#34116472

"""
Extract images from pdf: http://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python
Extract images coded with CCITTFaxDecode in .net: http://stackoverflow.com/questions/2641770/extracting-image-from-pdf-with-ccittfaxdecode-filter
TIFF format and tags: http://www.awaresystems.be/imaging/tiff/faq.html
"""


os.environ["TESSDATA_PREFIX"] = '/opt/local/share'  # this is required otherwise tesseract complains about file permissions

#sys.path.append('/opt/local/bin')  # make sure /opt/local/bin/tesseract is found
#actually, this has no effect on subprocess.Popen(['/opt/local/bin/tesseract']) https://stackoverflow.com/questions/5658622/python-subprocess-popen-environment-path
#

def process_neonlight_serenade(src_pdf_file_path, dst_pdf_file_path):

    tmp_pdf_file_path='/tmp/tmp1.pdf'
    pymusco.add_watermark(src_pdf_file_path, tmp_pdf_file_path, os.getenv('HOME')+'/data/Perso/MeltingNotes_work.git/partitions/mno-stamp.pdf')
    #https://github.com/RussellLuo/pdfbookmarker/blob/master/add_bookmarks.py

    # print(reader.outlines)
    # [{'/Title': '1 Introduction', '/Left': 99.213, '/Type': '/XYZ', '/Top': 742.911, '/Zoom': ..., '/Page': IndirectObject(513, 0)},
    #  {'/Title': '2 Convolutional Neural Networks', '/Left': 99.213, '/Type': '/XYZ', '/Top': 742.911, '/Zoom': ..., '/Page': IndirectObject(554, 0)}, [{'/Title': '2.1 Linear Image Filters', '/Left': 99.213, '/Type': '/XYZ', '/Top': 486.791, '/Zoom': ..., '/Page': IndirectObject(554, 0)},
    #  {'/Title': '2.2 CNN Layer Types', '/Left': 70.866, '/Type': '/XYZ', '/Top': 316.852, '/Zoom': ..., '/Page': IndirectObject(580, 0)},
    # [{'/Title': '2.2.1 Convolutional Layers', '/Left': 99.213, '/Type': '/XYZ', '/Top': 562.722, '/Zoom': ..., '/Page': IndirectObject(608, 0)},
    #  {'/Title': '2.2.2 Pooling Layers', '/Left': 99.213, '/Type': '/XYZ', '/Top': 299.817, '/Zoom': ..., '/Page': IndirectObject(654, 0)},
    #  {'/Title': '2.2.3 Dropout', '/Left': 99.213, '/Type': '/XYZ', '/Top': 742.911, '/Zoom': ..., '/Page': IndirectObject(689, 0)},
    #  {'/Title': '2.2.4 Normalization Layers', '/Left': 99.213, '/Type': '/XYZ', '/Top': 193.779, '/Zoom': <PyPDF2.generic.NullObject object at 0x7fbe49d14350>, '/Page': IndirectObject(689, 0)}]

    with open(src_pdf_file_path, 'rb') as src_pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(src_pdf_file)
        # pdfReader.numPages
        # 19
        for page_index in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_index)

            image = pymusco.pdf_page_to_png(page, resolution=72)
            #extract_pdf_page_images(page)
            
            tmp_img_path = '/tmp/titi.png'
            cv2.imwrite(tmp_img_path, image)
            text = pymusco.tesseract.image_to_string(Image.open(tmp_img_path)) #, lang='deu')
            print(text)
            

    pages_labels = [
        'piccolo',
        'flute',
        'oboe',
        'bassoon',
        'eb clarinet',
        'bb clarinet 1',
        'bb clarinet 2',
        'bb clarinet 3',
        'bb bass clarinet',
        'eb alto saxophon',
        'bb tenor saxophon',
        'eb baryton saxophon',
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
    ]
    bookmarks_tree = []
    page_index = 0
    for label in pages_labels:
        bookmarks_tree.append( (label, page_index, []) )
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


def process_japanese_tango(src_pdf_file_path, dst_pdf_file_path):

    with open(src_pdf_file_path, 'rb') as src_pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(src_pdf_file)
        # pdfReader.numPages
        # 19
        for page_index in range(pdf_reader.numPages):
            print('page_index = %d' % page_index)
            page = pdf_reader.getPage(page_index)
            pymusco.extract_pdf_page_images(page, image_folder='./tmp')


def test(src_pdf_file_path, dst_pdf_file_path):
    output = PyPDF2.PdfFileWriter() # open output
    input = PyPDF2.PdfFileReader(open(src_pdf_file_path, 'rb')) # open input
    output.addPage(input.getPage(0)) # insert page
    output.addBookmark('Hello, World Bookmark', 0, parent=None) # add bookmark
    outputStream = open(dst_pdf_file_path,'wb') #creating result pdf JCT
    output.write(outputStream) #writing to result pdf JCT
    outputStream.close() #closing result JCT


# test(os.getenv('HOME')+'/Google Drive/partitions/talons/neonlight serenade.pdf', os.getenv('HOME')+'/toto/serenade.pdf')
# process_neonlight_serenade(os.getenv('HOME')+'/Google Drive/partitions/talons/neonlight serenade.pdf', os.getenv('HOME')+'/toto/serenade.pdf')
process_japanese_tango('./samples/666-japanese-tango.pdf', './tmp/result.pdf')

