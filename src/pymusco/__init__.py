"""

https://automatetheboringstuff.com/chapter13/
https://github.com/RussellLuo/pdfbookmarker/blob/master/add_bookmarks.py
"""
# sudo port install py27-pypdf2
import PyPDF2
from PyPDF2 import PdfFileMerger, PdfFileReader

"""
how to install tesseract on osx:
- install macports
- install py27-tesser. We choose python 2.7 because:
        1. python 2.6 misses py26-pypdf2
        2. the python scripts inside py26-tesser are not compatible with python 3
        3. python 2.7 misses py27-tesser in macports but it's not too hard to create one
    - mkdir -p $HOME/owncloud/macports/localports
    - sudo vi /opt/local/etc/macports/sources.conf
        - replace
             rsync://rsync.macports.org/release/tarballs/ports.tar [default]
          with
             file://$HOME/owncloud/macports/localports
             rsync://rsync.macports.org/release/tarballs/ports.tar [default]
    - mkdir -p $HOME/owncloud/macports/localports/python/py27-tesser/files
    - cat /opt/local/var/macports/sources/rsync.macports.org/release/tarballs/ports/python/py-tesser/Portfile | sed 's/26/27/' > $HOME/owncloud/macports/localports/python/py27-tesser/Portfile
    - cp /opt/local/var/macports/sources/rsync.macports.org/release/tarballs/ports/python/py-tesser/files/patch-pillow-compat.diff $HOME/owncloud/macports/localports/python/py27-tesser/files/
    - cp /opt/local/var/macports/software/py26-tesser/py26-tesser-0.0.1_1.darwin_17.noarch.tbz2 $HOME/owncloud/macports/localports/python/py27-tesser/files/py27-tesser-0.0.1_1.darwin_17.noarch.tbz2
    - cd $HOME/owncloud/macports/localports
    - portindex
    - sudo port install py27-tesser
- fix the error "No such file or directory: 'tesseract.log'"
    - error message :
        File "./neonlightserenade.py", line 347, in <module>
            process_neonlight_serenade('$HOME/Google Drive/partitions/talons/neonlight serenade.pdf', '$HOME/toto/serenade.pdf')
          File "./neonlightserenade.py", line 290, in process_neonlight_serenade
            text = tesseract.image_to_string(Image.open('/tmp/titi.png'))
          File "/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/tesseract/__init__.py", line 31, in image_to_string
            call_tesseract(scratch_image_name, scratch_text_name_root)
          File "/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/tesseract/__init__.py", line 24, in call_tesseract
            errors.check_for_errors()
          File "/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/tesseract/errors.py", line 10, in check_for_errors
            inf = file(logfile)
        IOError: [Errno 2] No such file or directory: 'tesseract.log'
    - in /opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/tesseract/errors.py replace:
            def check_for_errors(logfile = "tesseract.log"):
        with:
            def check_for_errors(logfile = "/tmp/tesseract.log"):
- fix the error : Tesseract couldn't load any languages!
    - error message :
        Error opening data file ./tessdata/eng.traineddata
        Please make sure the TESSDATA_PREFIX environment variable is set to the parent directory of your "tessdata" directory.
        Failed loading language 'eng'
        Tesseract couldn't load any languages!
    - sudo port install tesseract-eng
    - sudo port install tesseract-deu
    - export TESSDATA_PREFIX=/opt/local/share
"""
import tesseract

# from wand.image import Image
import re
import io
import os
import cv2
from PIL import Image
import struct
import subprocess

# https://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python/34116472#34116472

"""
Extract images from pdf: http://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python
Extract images coded with CCITTFaxDecode in .net: http://stackoverflow.com/questions/2641770/extracting-image-from-pdf-with-ccittfaxdecode-filter
TIFF format and tags: http://www.awaresystems.be/imaging/tiff/faq.html
"""


def tiff_header_for_CCITT(width, height, img_size, CCITT_group=4):
    tiff_header_struct = '<' + '2s' + 'h' + 'l' + 'h' + 'hhll' * 8 + 'h'
    return struct.pack(tiff_header_struct,
                       b'II',  # Byte order indication: Little indian
                       42,  # Version number (always 42)
                       8,  # Offset to first IFD
                       8,  # Number of tags in IFD
                       256, 4, 1, width,  # ImageWidth, LONG, 1, width
                       257, 4, 1, height,  # ImageLength, LONG, 1, lenght
                       258, 3, 1, 1,  # BitsPerSample, SHORT, 1, 1
                       259, 3, 1, CCITT_group,  # Compression, SHORT, 1, 4 = CCITT Group 4 fax encoding
                       262, 3, 1, 0,  # Threshholding, SHORT, 1, 0 = WhiteIsZero
                       273, 4, 1, struct.calcsize(tiff_header_struct),  # StripOffsets, LONG, 1, len of header
                       278, 4, 1, height,  # RowsPerStrip, LONG, 1, lenght
                       279, 4, 1, img_size,  # StripByteCounts, LONG, 1, size of image
                       0  # last IFD
                       )


def extract_pdf_page_images(pdf_page, image_folder='/tmp'):
    """
    :param PyPDF2.pdf.PageObject pdf_page:
    :param str image_folder:
    """
    xObject = pdf_page['/Resources']['/XObject'].getObject()

    for obj in xObject:
        if xObject[obj]['/Subtype'] == '/Image':
            (width, height) = (xObject[obj]['/Width'], xObject[obj]['/Height'])
            print('filter = %s' % xObject[obj]['/Filter'])
            if xObject[obj]['/Filter'] == '/CCITTFaxDecode':
                # File "/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/PyPDF2/filters.py", line 361, in decodeStreamData
                # raise NotImplementedError("unsupported filter %s" % filterType)
                # NotImplementedError: unsupported filter /CCITTFaxDecode
                """
                The  CCITTFaxDecode filter decodes image data that has been encoded using
                either Group 3 or Group 4 CCITT facsimile (fax) encoding. CCITT encoding is
                designed to achieve efficient compression of monochrome (1 bit per pixel) image
                data at relatively low resolutions, and so is useful only for bitmap image data, not
                for color images, grayscale images, or general data.

                K < 0 --- Pure two-dimensional encoding (Group 4)
                K = 0 --- Pure one-dimensional encoding (Group 3, 1-D)
                K > 0 --- Mixed one- and two-dimensional encoding (Group 3, 2-D)
                """
                if xObject[obj]['/DecodeParms']['/K'] == -1:
                    CCITT_group = 4
                else:
                    CCITT_group = 3
                data = xObject[obj]._data  # sorry, getData() does not work for CCITTFaxDecode
                img_size = len(data)
                tiff_header = tiff_header_for_CCITT(width, height, img_size, CCITT_group)
                img_name = image_folder + '/' + obj[1:] + '.tiff'
                with open(img_name, 'wb') as img_file:
                    img_file.write(tiff_header + data)
            else:
                data = xObject[obj].getData()
                print('data length : %d' % len(data))
                num_pixels = width * height
                print(width, height, num_pixels)
                color_space, indirect_object = xObject[obj]['/ColorSpace']
                print("color_space :", color_space)
                # print("indirect_object :", indirect_object)
                # :param PyPDF2.generic.IndirectObject indirect_object:
                
                # print(type(indirect_object))
                # print(dir(indirect_object))
                
                # ['/ICCBased', IndirectObject(13, 0)]
                
                # indObj, isIndirect := obj.(*PdfIndirectObject); isIndirect {
                """
                // TraceToDirectObject traces a PdfObject to a direct object.  For example direct objects contained
                // in indirect objects (can be double referenced even).
                //
                // Note: This function does not trace/resolve references. That needs to be done beforehand.
                func TraceToDirectObject(obj PdfObject) PdfObject {
                    iobj, isIndirectObj := obj.(*PdfIndirectObject)
                    depth := 0
                    for isIndirectObj == true {
                        obj = iobj.PdfObject
                        iobj, isIndirectObj = obj.(*PdfIndirectObject)
                        depth++
                        if depth > TraceMaxDepth {
                            common.Log.Error("Trace depth level beyond 20 - error!")
                            return nil
                        }
                    }
                    return obj
                }
                """
                if color_space == '/DeviceRGB':
                    mode = "RGB"
                elif color_space == '/ICCBased':
                    one_bit_per_pixel = False
                    # guess if the image is stored as one bit per pixel
                    # ICCBased decoding code written in go here : https://github.com/unidoc/unidoc/blob/master/pdf/model/colorspace.go
                    assert xObject[obj]['/Filter'] == '/FlateDecode', "don't know how to guess if data is 1 bits per pixel when filter is %s" % xObject[obj]['/Filter']
                    expected_packed_image_data_size = num_pixels / 8 + 1  # rough packed image size supposing image is stored as 1 bit per pixel
                    if len(data) > expected_packed_image_data_size:
                        # estimate the header data size, supposing image is stored as 1 bit per pixel in a flat way
                        header_data_size = len(data) - expected_packed_image_data_size
                        GUESSED_MAX_1_BIT_IMAGE_HEADER_SIZE = 1000  # a test shows that the measured extra data size was 620
                        if header_data_size < GUESSED_MAX_1_BIT_IMAGE_HEADER_SIZE:
                            one_bit_per_pixel = True
                    
                    if one_bit_per_pixel:
                        mode = "1"  # (1-bit pixels, black and white, stored with one pixel per byte)
                    else:
                        mode = "P"  # (8-bit pixels, mapped to any other mode using a color palette)
                else:
                    mode = "P"  # (8-bit pixels, mapped to any other mode using a color palette)
                if xObject[obj]['/Filter'] == '/FlateDecode':
                    img = Image.frombytes(mode, (width, height), data)
                    img.save(image_folder + '/' + obj[1:] + ".png")
                elif xObject[obj]['/Filter'] == '/DCTDecode':
                    img = open(image_folder + '/' + obj[1:] + ".jpg", "wb")
                    img.write(data)
                    img.close()
                elif xObject[obj]['/Filter'] == '/JPXDecode':
                    img = open(image_folder + '/' + obj[1:] + ".jp2", "wb")
                    img.write(data)
                    img.close()

# def pdf_page_to_png(pdf_page, resolution = 72,):
#     """
#     Returns specified PDF page as wand.image.Image png.
#     :param PyPDF2.PdfPage pdf_page: PDF from which to take pages.
#     :param int resolution: Resolution for resulting png in DPI.
#     """
#     dst_pdf = PyPDF2.PdfFileWriter()
#     dst_pdf.addPage(pdf_page)
#
#     pdf_bytes = io.BytesIO()
#     tmp_pdf_file_path = '/tmp/toto.pdf'
#     with open(tmp_pdf_file_path, "wb") as tmp_pdf:
#         dst_pdf.write(pdf_bytes)
#     pdf_bytes.seek(0)
#
#     #image = cv2.imread(tmp_pdf_file_path)
#     #print(type(image))
#     #gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#
#     img = Image(file = pdf_bytes, resolution = resolution)
#     img.convert("png")
#     img.write('/tmp/toto.png')
#     image = cv2.imread('/tmp/toto.png')
#     print(type(image))
#
#     return image


def pdf_page_to_png(pdf_page, resolution=72):
    """
    :param  pdf_page:
    """
    dst_pdf = PyPDF2.PdfFileWriter()
    dst_pdf.addPage(pdf_page)
 
    tmp_pdf_file_path = '/tmp/toto.pdf'
    with open(tmp_pdf_file_path, "wb") as tmp_pdf:
        dst_pdf.write(tmp_pdf)

    tmp_png_file_path = '/tmp/toto.png'
    cmd = '/opt/local/bin/convert -density 300 ' + tmp_pdf_file_path + ' ' + tmp_png_file_path  # uses imagemagick' convert
    subprocess.Popen(cmd.split(), stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    image = cv2.imread(tmp_png_file_path)
    print(type(image))
     
    return image


def addBookmarks(pdf_in_filename, bookmarks_tree, pdf_out_filename=None):
    """Add bookmarks to existing PDF files
    Home:
        https://github.com/RussellLuo/pdfbookmarker
    Some useful references:
        [1] http://pybrary.net/pyPdf/
        [2] http://stackoverflow.com/questions/18855907/adding-bookmarks-using-pypdf2
        [3] http://stackoverflow.com/questions/3009935/looking-for-a-good-python-tree-data-structure
    """
    pdf_out = PdfFileMerger()

    # read `pdf_in` into `pdf_out`, using PyPDF2.PdfFileMerger()
    # with open(pdf_in_filename, 'rb') as inputStream:
    inputStream = open(pdf_in_filename, 'rb')
    pdf_out.append(inputStream, import_bookmarks=False)

    # copy/preserve existing metainfo
    pdf_in = PdfFileReader(pdf_in_filename)
    metaInfo = pdf_in.getDocumentInfo()
    if metaInfo:
        pdf_out.addMetadata(metaInfo)

    def crawl_tree(tree, parent):
        for title, pagenum, subtree in tree:
            current = pdf_out.addBookmark(title, pagenum, parent)  # add parent bookmark
            if subtree:
                crawl_tree(subtree, current)

    # add bookmarks into `pdf_out` by crawling `bookmarks_tree`
    crawl_tree(bookmarks_tree, None)

    # get `pdf_out_filename` if it's not specified
    if not pdf_out_filename:
        name_parts = os.path.splitext(pdf_in_filename)
        pdf_out_filename = name_parts[0] + '-new' + name_parts[1]

    # wrie `pdf_out`
    with open(pdf_out_filename, 'wb') as outputStream:
        pdf_out.write(outputStream)


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


def add_watermark(src_pdf_file_path, dst_pdf_file_path, watermark_file_path):
    """
    :param str watermark_file_path: location of the pdf file containing the stamp used for watermarking
    """
    pdf_watermark_reader = PyPDF2.PdfFileReader(open(watermark_file_path, 'rb'))
    watermark = pdf_watermark_reader.getPage(0)

    pdf_writer = PyPDF2.PdfFileWriter()
    with open(src_pdf_file_path, 'rb') as src_pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(src_pdf_file)
        # pdfReader.numPages
        # 19
        for page_index in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_index)
            # page.mergePage(watermark)
            page.mergeScaledTranslatedPage(watermark, scale=1.0, tx=500.0, ty=770.0)
            # pdf_writer.addBookmark(title='toto %s' % page_index, pagenum=page_index, parent=None, color=None, bold=False, italic=False, fit='/Fit')
            
            pdf_writer.addPage(page)
        # pdf_writer.addBookmark('Hello, World Bookmark', 0, parent=None)
        # pdf_writer.addBookmark(title='toto', pagenum=2, parent=None, color=None, bold=False, italic=False, fit='/Fit')
        # pdf_writer.setPageMode("/UseOutlines")
        
        with open(dst_pdf_file_path, 'wb') as dst_pdf_file:
            pdf_writer.write(dst_pdf_file)
            dst_pdf_file.close()
