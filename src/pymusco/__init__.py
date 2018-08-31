"""

https://automatetheboringstuff.com/chapter13/
https://github.com/RussellLuo/pdfbookmarker/blob/master/add_bookmarks.py
"""
import tempfile
import shutil
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


def extract_pdf_stream_image(pdf_stream, image_dir, image_name):
    """
    :param PyPDF2.generic.EncodedStreamObject pdf_stream: a pdf node which is supposed to contain an image
    :param str image_dir: where to save the image of the given name_object
    :param str image_name: the name of the saved file image, without file extension
    :return str: the saved image file path with file extension
    """
    assert pdf_stream['/Subtype'] == '/Image', "this function expects the subtype of this encoded_stream_object to be an image"
    saved_image_file_path = None
    (width, height) = (pdf_stream['/Width'], pdf_stream['/Height'])
    print('filter = %s' % pdf_stream['/Filter'])
    if pdf_stream['/Filter'] == '/CCITTFaxDecode':
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
        if pdf_stream['/DecodeParms']['/K'] == -1:
            CCITT_group = 4
        else:
            CCITT_group = 3
        data = pdf_stream._data  # sorry, getData() does not work for CCITTFaxDecode
        img_size = len(data)
        tiff_header = tiff_header_for_CCITT(width, height, img_size, CCITT_group)
        saved_image_file_path = image_dir + '/' + image_name + '.tiff'
        with open(saved_image_file_path, 'wb') as img_file:
            img_file.write(tiff_header + data)
    else:
        data = pdf_stream.getData()
        print('data length : %d' % len(data))
        num_pixels = width * height
        print(width, height, num_pixels)
        color_space, indirect_object = pdf_stream['/ColorSpace']
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
            assert pdf_stream['/Filter'] == '/FlateDecode', "don't know how to guess if data is 1 bits per pixel when filter is %s" % pdf_stream['/Filter']
            bytes_per_line = width / 8
            if (width % 8) > 0:
                bytes_per_line += 1
            expected_packed_image_data_size = bytes_per_line * height  # packed image size supposing image is stored as 1 bit per pixel
            if len(data) == expected_packed_image_data_size:
                one_bit_per_pixel = True
            
            if one_bit_per_pixel:
                mode = "1"  # (1-bit pixels, black and white, stored with one pixel per byte)
            else:
                mode = "P"  # (8-bit pixels, mapped to any other mode using a color palette)
        else:
            mode = "P"  # (8-bit pixels, mapped to any other mode using a color palette)
        if pdf_stream['/Filter'] == '/FlateDecode':
            saved_image_file_path = image_dir + '/' + image_name + ".png"
            img = Image.frombytes(mode, (width, height), data)
            img.save(saved_image_file_path)
        elif pdf_stream['/Filter'] == '/DCTDecode':
            saved_image_file_path = image_dir + '/' + image_name + ".jpg"
            img = open(saved_image_file_path, "wb")
            img.write(data)
            img.close()
        elif pdf_stream['/Filter'] == '/JPXDecode':
            saved_image_file_path = image_dir + '/' + image_name + ".jp2"
            img = open(saved_image_file_path, "wb")
            img.write(data)
            img.close()
    assert saved_image_file_path is not None
    return saved_image_file_path
    

def extract_pdf_page_main_image(pdf_page, image_dir, image_name):
    """
    :param PyPDF2.pdf.PageObject pdf_page:
    :param str image_dir: where to save the image of the given name_object
    :param str image_name: the name of the saved file image, without file extension
    :return str: the saved image file path with file extension
    """
    xObject = pdf_page['/Resources']['/XObject'].getObject()

    for obj in xObject:
        if xObject[obj]['/Subtype'] == '/Image':
            return extract_pdf_stream_image(pdf_stream=xObject[obj], image_dir=image_dir, image_name=image_name)


def extract_pdf_page_images(pdf_page, image_folder='/tmp'):
    """
    :param PyPDF2.pdf.PageObject pdf_page:
    :param str image_folder:
    """
    xObject = pdf_page['/Resources']['/XObject'].getObject()

    for obj in xObject:
        print(type(obj))
        print(type(xObject[obj]))
        
        if xObject[obj]['/Subtype'] == '/Image':
            saved_image_file_path = extract_pdf_stream_image(pdf_stream=xObject[obj], image_dir=image_folder, image_name=obj[1:])
            print('extracted image : %s' % saved_image_file_path)


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


def add_stamp(src_pdf_file_path, dst_pdf_file_path, stamp_file_path, scale=1.0, tx=500.0, ty=770.0):
    """
    
    warning! this function has a side effect : it removes the bookmark!
    
    :param str stamp_file_path: location of the pdf file containing the stamp used
    """
    pdf_watermark_reader = PyPDF2.PdfFileReader(open(stamp_file_path, 'rb'))
    watermark = pdf_watermark_reader.getPage(0)

    use_tmp_output_file = False
    if dst_pdf_file_path == src_pdf_file_path:
        use_tmp_output_file = True
    if use_tmp_output_file:
        tmp_dst_pdf_file_path = dst_pdf_file_path + ".tmp"
    else:
        tmp_dst_pdf_file_path = dst_pdf_file_path

    pdf_writer = PyPDF2.PdfFileWriter()
    with open(src_pdf_file_path, 'rb') as src_pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(src_pdf_file)
        # pdfReader.numPages
        # 19
        for page_index in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_index)
            # page.mergePage(watermark)
            page.mergeScaledTranslatedPage(watermark, scale=scale, tx=tx, ty=ty)
            # pdf_writer.addBookmark(title='toto %s' % page_index, pagenum=page_index, parent=None, color=None, bold=False, italic=False, fit='/Fit')
            
            pdf_writer.addPage(page)
        # pdf_writer.addBookmark('Hello, World Bookmark', 0, parent=None)
        # pdf_writer.addBookmark(title='toto', pagenum=2, parent=None, color=None, bold=False, italic=False, fit='/Fit')
        # pdf_writer.setPageMode("/UseOutlines")
        
        with open(tmp_dst_pdf_file_path, 'wb') as dst_pdf_file:
            pdf_writer.write(dst_pdf_file)
            dst_pdf_file.close()

        if use_tmp_output_file:
            shutil.copyfile(tmp_dst_pdf_file_path, dst_pdf_file_path)


class TableOfContents(object):
    
    def __init__(self, label_to_page):
        """
        :param dict(str, int) label_to_page:
        """
        self.label_to_page = label_to_page
    
    def get_label(self, page_index):
        for label, page in self.label_to_page.iteritems():
            if page == page_index:
                return label
        return None


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
    rotated_image.show()


def scan_to_stub(src_scanned_pdf_file_path, dst_stub_pdf_file_path, toc, stamp_file_path=None, scale=1.0, tx=500.0, ty=770.0):
    """
    creates musical score stub from a musical score raw scan :
    - adds a table of contents
    - adds a stamp
    - numbers the pages
    
    :param str src_scanned_pdf_file_path: the source file that is expected to contain the scanned musical scores
    :param str dst_stub_pdf_file_path: the destination file that is expected to contain the stub of musical scores
    :param TableOfContents toc:
    :param str or None stamp_file_path:
    """

    # tmp_dir = tempfile.mkdtemp()
    tmp_dir = os.getcwd() + '/tmp'

    scanned_image_file_paths = []
    with open(src_scanned_pdf_file_path, 'rb') as src_pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(src_pdf_file)
        # pdfReader.numPages
        # 19
        for page_index in range(3):  # range(pdf_reader.numPages):
            print('page_index = %d' % page_index)
            page = pdf_reader.getPage(page_index)
            image_file_path = extract_pdf_page_main_image(page, image_dir=tmp_dir, image_name=('page%03d' % page_index))
            
            # some extracted images are not in portrait mode as we would expect, so rotate them
            # TODO: automatically detect when rotation is needed
            rotate_image(image_file_path, 90.0, image_file_path)
            
            scanned_image_file_paths.append(image_file_path)
            # break
    
    latex_file_path = tmp_dir + '/stub.tex'
    with open(latex_file_path, 'w') as latex_file:
        latex_file.write(r'\documentclass{article}' + '\n')
        
        latex_file.write(r'% tikz package is used to use scanned images as background' + '\n')
        latex_file.write(r'\usepackage{tikz}' + '\n')
        
        latex_file.write(r'% hyperref package is used to create a clickable table of contents' + '\n')
        latex_file.write(r'\usepackage{hyperref}' + '\n')
        latex_file.write(r'\hypersetup{' + '\n')
        latex_file.write(r'   colorlinks,' + '\n')
        latex_file.write(r'   citecolor=black,' + '\n')
        latex_file.write(r'   filecolor=black,' + '\n')
        latex_file.write(r'   urlcolor=black' + '\n')
        latex_file.write(r'}')
        
        latex_file.write(r'% command to declare invisible sections (sections that appear in the table of contents but not in the text itself)' + '\n')
        latex_file.write(r'\newcommand\invisiblesection[1]{%' + '\n')
        latex_file.write(r'  \refstepcounter{section}%' + '\n')
        latex_file.write(r'  \addcontentsline{toc}{section}{\protect\numberline{\thesection}#1}%' + '\n')
        latex_file.write(r'  \sectionmark{#1}}' + '\n')
        
        latex_file.write(r'\newcommand*{\PageBackground}[1]{' + '\n')
        latex_file.write(r'    \tikz[remember picture,overlay] \node[opacity=0.3,inner sep=0pt] at (current page.center){\includegraphics[width=\paperwidth,height=\paperheight]{#1}};')
        latex_file.write(r'}')
        latex_file.write(r'\begin{document}' + '\n')
        
        latex_file.write(r'  \tableofcontents' + '\n')
        
        page_index = 1
        for scanned_image_file_path in scanned_image_file_paths:
            latex_file.write(r'\newpage' + '\n')
            latex_file.write(r'\PageBackground{%s}' % scanned_image_file_path + '\n')
            
            if stamp_file_path is not None:
                latex_file.write(r'\begin{tikzpicture}[overlay]')
                latex_file.write(r'\node at (%f,%f) {\includegraphics[scale=%f]{%s}};' % (tx, ty, scale, stamp_file_path))
                latex_file.write(r'\end{tikzpicture}')

            page_label = toc.get_label(page_index)
            if page_label is not None:
                latex_file.write(r'\invisiblesection{%s}' % page_label + '\n')
            else:
                latex_file.write(r'\null' + '\n')

            page_index += 1
        latex_file.write(r'\end{document}' + '\n')

    # compile stub.tex document into stub.pdf
    subprocess.check_call(["pdflatex", "-halt-on-error", "./stub.tex"], cwd=tmp_dir)
    subprocess.check_call(["pdflatex", "-halt-on-error", "./stub.tex"], cwd=tmp_dir)  # compilation of latex document takes 2 passes
    
    os.rename(tmp_dir + '/stub.pdf', dst_stub_pdf_file_path)
