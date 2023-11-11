#!/usr/bin/env python3.8
import struct
import subprocess
import os
import shutil
import sys
import traceback
from pathlib import Path
from PIL import Image
import cv2
import PyPDF2
from .core import rotate_image

# Extract images from pdf: http://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python
# Extract images coded with CCITTFaxDecode in .net: http://stackoverflow.com/questions/2641770/extracting-image-from-pdf-with-ccittfaxdecode-filter
# TIFF format and tags: http://www.awaresystems.be/imaging/tiff/faq.html
# https://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python/34116472#34116472


def tiff_header_for_ccitt(width, height, img_size, ccitt_group=4):
    tiff_header_struct = '<' + '2s' + 'h' + 'l' + 'h' + 'hhll' * 8 + 'h'
    return struct.pack(tiff_header_struct,
                       b'II',  # Byte order indication: Little indian
                       42,  # Version number (always 42)
                       8,  # Offset to first IFD
                       8,  # Number of tags in IFD
                       256, 4, 1, width,  # ImageWidth, LONG, 1, width
                       257, 4, 1, height,  # ImageLength, LONG, 1, lenght
                       258, 3, 1, 1,  # BitsPerSample, SHORT, 1, 1
                       259, 3, 1, ccitt_group,  # Compression, SHORT, 1, 4 = CCITT Group 4 fax encoding
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
    print(f'filter = {pdf_stream["/Filter"]}')
    if pdf_stream['/Filter'] == '/CCITTFaxDecode':
        # File "/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/PyPDF2/filters.py", line 361, in decodeStreamData
        # raise NotImplementedError("unsupported filter %s" % filterType)
        # NotImplementedError: unsupported filter /CCITTFaxDecode

        # The  CCITTFaxDecode filter decodes image data that has been encoded using
        # either Group 3 or Group 4 CCITT facsimile (fax) encoding. CCITT encoding is
        # designed to achieve efficient compression of monochrome (1 bit per pixel) image
        # data at relatively low resolutions, and so is useful only for bitmap image data, not
        # for color images, grayscale images, or general data.

        # K < 0 --- Pure two-dimensional encoding (Group 4)
        # K = 0 --- Pure one-dimensional encoding (Group 3, 1-D)
        # K > 0 --- Mixed one- and two-dimensional encoding (Group 3, 2-D)
        if pdf_stream['/DecodeParms']['/K'] == -1:
            ccitt_group = 4
        else:
            ccitt_group = 3
        data = pdf_stream._data  # sorry, getData() does not work for CCITTFaxDecode pylint: disable=protected-access
        img_size = len(data)
        tiff_header = tiff_header_for_ccitt(width, height, img_size, ccitt_group)
        saved_image_file_path = (image_dir / image_name).with_suffix('.tiff')
        with open(saved_image_file_path, 'wb') as img_file:
            img_file.write(tiff_header + data)
    else:
        data = pdf_stream.getData()
        print(f'data length : {len(data)}')
        num_pixels = width * height
        print(width, height, num_pixels)
        print(pdf_stream.keys())
        print(pdf_stream['/Type'])
        print(pdf_stream['/BitsPerComponent'])
        if pdf_stream['/BitsPerComponent'] == 1:
            mode = "1"
        else:
            color_space, indirect_object = pdf_stream['/ColorSpace']  # pylint: disable=unused-variable
            print("color_space :", color_space)
            # print("indirect_object :", indirect_object)
            # :param PyPDF2.generic.IndirectObject indirect_object:

            # print(type(indirect_object))
            # print(dir(indirect_object))

            # ['/ICCBased', IndirectObject(13, 0)]

            # indObj, isIndirect := obj.(*PdfIndirectObject); isIndirect {
            # // TraceToDirectObject traces a PdfObject to a direct object.  For example direct objects contained
            # // in indirect objects (can be double referenced even).
            # //
            # // Note: This function does not trace/resolve references. That needs to be done beforehand.
            # func TraceToDirectObject(obj PdfObject) PdfObject {
            #     iobj, isIndirectObj := obj.(*PdfIndirectObject)
            #     depth := 0
            #     for isIndirectObj == true {
            #         obj = iobj.PdfObject
            #         iobj, isIndirectObj = obj.(*PdfIndirectObject)
            #         depth++
            #         if depth > TraceMaxDepth {
            #             common.Log.Error("Trace depth level beyond 20 - error!")
            #             return nil
            #         }
            #     }
            #     return obj
            # }

            if color_space == '/DeviceRGB':
                mode = "RGB"
            elif color_space == '/ICCBased':
                one_bit_per_pixel = False
                # guess if the image is stored as one bit per pixel
                # ICCBased decoding code written in go here : https://github.com/unidoc/unidoc/blob/master/pdf/model/colorspace.go
                assert pdf_stream['/Filter'] == '/FlateDecode', f"don't know how to guess if data is 1 bits per pixel when filter is {pdf_stream['/Filter']}"
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


def find_pdf_page_raster_image(pdf_page):
    """
    finds the first raster image in this page

    :param PyPDF2.pdf.PageObject pdf_page:
    :return PyPDF2.generic.EncodedStreamObject: a pdf node which is supposed to contain an image
    """
    if '/XObject' in pdf_page['/Resources']:
        x_object = pdf_page['/Resources']['/XObject'].getObject()
        for obj in x_object:
            if x_object[obj]['/Subtype'] == '/Image':
                return x_object[obj]
    return None


def extract_pdf_page_main_image(pdf_page: PyPDF2.PageObject, image_dir: Path, image_name: str):
    """
    :param PyPDF2.pdf.PageObject pdf_page:
    :param str image_dir: where to save the image of the given name_object
    :param str image_name: the name of the saved file image, without file extension
    :return str: the saved image file path with file extension
    """
    pdf_stream = find_pdf_page_raster_image(pdf_page)

    if pdf_stream is not None:
        # this pdf page contains a raster image; we deduce from that that it has been scanned
        try:
            saved_image_file_path = extract_pdf_stream_image(pdf_stream=pdf_stream, image_dir=image_dir, image_name=image_name)
        except NotImplementedError as e:
            print(f"warning : NotImplementedError({str(e)}). Maybe pypdf2 is unable to decode this stream. Falling back to a resampling method.")
            image = pdf_page_to_png(pdf_page, resolution=300)
            saved_image_file_path = (image_dir / image_name).with_suffix('png')
            cv2.imwrite(saved_image_file_path, image)
            print(f"resampled image saved to {saved_image_file_path}")

        if '/Rotate' in pdf_page.keys() and pdf_page['/Rotate'] != 0:
            # some extracted images are not in portrait mode as we would expect, so rotate them

            # non rotated page contents
            #     {
            #         '/Parent': IndirectObject(3, 0),
            #         '/Contents': IndirectObject(29, 0),
            #         '/Type': '/Page',
            #         '/Resources': IndirectObject(31, 0),
            #         '/Rotate': 0,
            #         '/MediaBox': [0, 0, 595.32, 841.92]
            #     }

            # rotated_page_contents:
            #     {
            #         '/Parent': IndirectObject(3, 0),
            #         '/Contents': IndirectObject(33, 0),
            #         '/Type': '/Page',
            #         '/Resources': IndirectObject(35, 0),
            #         '/Rotate': 270,
            #         '/MediaBox': [0, 0, 841.8, 595.2]
            #     }
            print(f"rotating image {saved_image_file_path} by {-pdf_page['/Rotate']:f} degrees")
            rotate_image(saved_image_file_path, -pdf_page['/Rotate'], saved_image_file_path)
    else:
        # this page doesn't contain a raster image, so we keep it in its original vectorial form
        saved_image_file_path = (image_dir / image_name).with_suffix('pdf')
        with open(saved_image_file_path, 'wb') as pdf_file:
            dst_pdf = PyPDF2.PdfWriter()
            dst_pdf.add_page(pdf_page)
            dst_pdf.write(pdf_file)
    return saved_image_file_path


def extract_pdf_page(pdf_page: PyPDF2.PageObject, image_dir: Path, image_name: str):
    """
    :param PyPDF2.pdf.PageObject pdf_page:
    :param str image_dir: where to save the image of the given name_object
    :param str image_name: the name of the saved file image, without file extension
    :return str: the saved image file path with file extension
    """
    saved_image_file_path = (image_dir / image_name).with_suffix('pdf')
    with open(saved_image_file_path, 'wb') as pdf_file:
        dst_pdf = PyPDF2.PdfWriter()
        dst_pdf.add_page(pdf_page)
        dst_pdf.write(pdf_file)
    return saved_image_file_path


def extract_pdf_page_images(pdf_page, image_folder='/tmp'):
    """
    :param PyPDF2.pdf.PageObject pdf_page:
    :param str image_folder:
    """
    x_object = pdf_page['/Resources']['/XObject'].getObject()

    for obj in x_object:
        print(type(obj))
        print(type(x_object[obj]))

        if x_object[obj]['/Subtype'] == '/Image':
            saved_image_file_path = extract_pdf_stream_image(pdf_stream=x_object[obj], image_dir=image_folder, image_name=obj[1:])
            print(f'extracted image : {saved_image_file_path}')


def pdf_page_to_png(pdf_page: PyPDF2.PageObject, resolution=72) -> cv2.Mat:
    """
    :param  pdf_page:
    """
    dst_pdf = PyPDF2.PdfWriter()
    dst_pdf.add_page(pdf_page)

    tmp_dir = Path('/tmp/pymusco')
    tmp_dir.mkdir(parents=True, exist_ok=True)

    tmp_pdf_file_path = tmp_dir / 'toto.pdf'
    with open(tmp_pdf_file_path, "wb") as tmp_pdf:
        dst_pdf.write(tmp_pdf)

    tmp_png_file_path = tmp_dir / '/toto.png'
    subprocess.check_call(['/opt/local/bin/convert', '-density', f'{resolution:d}', tmp_pdf_file_path, tmp_png_file_path])
    image = cv2.imread(tmp_png_file_path)
    print(type(image))

    return image


def add_bookmarks(pdf_in_filename, bookmarks_tree, pdf_out_filename=None):
    """Add bookmarks to existing PDF files
    Home:
        https://github.com/RussellLuo/pdfbookmarker
    Some useful references:
        [1] http://pybrary.net/pyPdf/
        [2] http://stackoverflow.com/questions/18855907/adding-bookmarks-using-pypdf2
        [3] http://stackoverflow.com/questions/3009935/looking-for-a-good-python-tree-data-structure
    """
    pdf_out = PyPDF2.PdfMerger()

    # read `pdf_in` into `pdf_out`, using PyPDF2.PdfMerger()
    # with open(pdf_in_filename, 'rb') as inputStream:
    input_stream = open(pdf_in_filename, 'rb')
    pdf_out.append(input_stream, import_outline=False)

    # copy/preserve existing metainfo
    pdf_in = PyPDF2.PdfReader(pdf_in_filename)
    meta_info = pdf_in.getDocumentInfo()
    if meta_info:
        pdf_out.addMetadata(meta_info)

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
    with open(pdf_out_filename, 'wb') as output_stream:
        pdf_out.write(output_stream)


def add_stamp(src_pdf_file_path, dst_pdf_file_path, stamp_file_path, scale=1.0, tx=500.0, ty=770.0):
    """

    warning! this function has a side effect : it removes the bookmark!

    :param str stamp_file_path: location of the pdf file containing the stamp used
    """
    pdf_watermark_reader = PyPDF2.PdfReader(open(stamp_file_path, 'rb'))
    watermark = pdf_watermark_reader.pages[0]

    use_tmp_output_file = False
    if dst_pdf_file_path == src_pdf_file_path:
        use_tmp_output_file = True
    if use_tmp_output_file:
        tmp_dst_pdf_file_path = dst_pdf_file_path + ".tmp"
    else:
        tmp_dst_pdf_file_path = dst_pdf_file_path

    pdf_writer = PyPDF2.PdfWriter()
    with open(src_pdf_file_path, 'rb') as src_pdf_file:
        pdf_reader = PyPDF2.PdfReader(src_pdf_file)
        # pdfReader.numPages
        # 19
        for page_index in range(pdf_reader.numPages):
            page = pdf_reader.pages[page_index]
            # page.mergePage(watermark)
            page.mergeScaledTranslatedPage(watermark, scale=scale, tx=tx, ty=ty)
            # pdf_writer.addBookmark(title='toto %s' % page_index, pagenum=page_index, parent=None, color=None, bold=False, italic=False, fit='/Fit')

            pdf_writer.add_page(page)
        # pdf_writer.addBookmark('Hello, World Bookmark', 0, parent=None)
        # pdf_writer.addBookmark(title='toto', pagenum=2, parent=None, color=None, bold=False, italic=False, fit='/Fit')
        # pdf_writer.setPageMode("/UseOutlines")

        with open(tmp_dst_pdf_file_path, 'wb') as dst_pdf_file:
            pdf_writer.write(dst_pdf_file)
            dst_pdf_file.close()

        if use_tmp_output_file:
            shutil.copyfile(tmp_dst_pdf_file_path, dst_pdf_file_path)


def check_pdf(src_pdf_file_path):
    """
    the purpose of this function is to detect inconsistencies in the given pdf file
    an exception is raised if the pdf is malformed
    please note that all maformations are not detected yet
    """
    with open(src_pdf_file_path, 'rb') as src_pdf_file:
        pdf_reader = PyPDF2.PdfReader(src_pdf_file)
        for page_index in range(pdf_reader.numPages):
            print(f'page_index = {page_index}')
            pdf_page = pdf_reader.pages[page_index]
            if '/XObject' in pdf_page['/Resources']:
                x_object = pdf_page['/Resources']['/XObject'].getObject()
                for obj in x_object:
                    if x_object[obj]['/Subtype'] == '/Image':
                        pdf_stream = x_object[obj]
                        assert pdf_stream['/Subtype'] == '/Image', "this function expects the subtype of this encoded_stream_object to be an image"
                        (width, height) = (pdf_stream['/Width'], pdf_stream['/Height'])
                        print(f"filter = {pdf_stream['/Filter']}")
                        if pdf_stream['/Filter'] == '/CCITTFaxDecode':
                            # File "/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/PyPDF2/filters.py", line 361, in decodeStreamData
                            # raise NotImplementedError("unsupported filter %s" % filterType)
                            # NotImplementedError: unsupported filter /CCITTFaxDecode

                            # The  CCITTFaxDecode filter decodes image data that has been encoded using
                            # either Group 3 or Group 4 CCITT facsimile (fax) encoding. CCITT encoding is
                            # designed to achieve efficient compression of monochrome (1 bit per pixel) image
                            # data at relatively low resolutions, and so is useful only for bitmap image data, not
                            # for color images, grayscale images, or general data.

                            # K < 0 --- Pure two-dimensional encoding (Group 4)
                            # K = 0 --- Pure one-dimensional encoding (Group 3, 1-D)
                            # K > 0 --- Mixed one- and two-dimensional encoding (Group 3, 2-D)
                            if pdf_stream['/DecodeParms']['/K'] == -1:
                                ccitt_group = 4
                            else:
                                ccitt_group = 3
                            data = pdf_stream._data  # sorry, getData() does not work for CCITTFaxDecode  pylint: disable=protected-access
                            img_size = len(data)
                            tiff_header = tiff_header_for_ccitt(width, height, img_size, ccitt_group)  # pylint: disable=unused-variable
                        else:
                            try:
                                data = pdf_stream.getData()
                                # on corrupt file, gives : raise utils.PdfReadError("Unable to find 'endstream' marker after stream at byte %s." % utils.hexStr(stream.tell()))
                            except NotImplementedError as e:  # pylint: disable=unused-variable
                                continue
                            except AssertionError as e:
                                _, _, tb = sys.exc_info()
                                # traceback.print_tb(tb) # Fixed format
                                tb_info = traceback.extract_tb(tb)
                                filename, line, func, text = tb_info[-1]  # pylint: disable=unused-variable
                                # print('assert error on file {} line {} in statement {}'.format(filename, line, text))
                                if text == 'assert len(data) % rowlength == 0':
                                    # this seems to be a zealous assert that fails even on legitimate pdf output of pdflatex, so ignore it
                                    continue
                                else:
                                    raise e
                            print(f'data length : {len(data)}')
                            num_pixels = width * height
                            print(width, height, num_pixels)
                            color_space, indirect_object = pdf_stream['/ColorSpace']  # pylint: disable=unused-variable
                            print("color_space :", color_space)
                            if color_space == '/DeviceRGB':
                                mode = "RGB"
                            elif color_space == '/ICCBased':
                                one_bit_per_pixel = False
                                # guess if the image is stored as one bit per pixel
                                # ICCBased decoding code written in go here : https://github.com/unidoc/unidoc/blob/master/pdf/model/colorspace.go
                                assert pdf_stream['/Filter'] == '/FlateDecode', f"don't know how to guess if data is 1 bits per pixel when filter is {pdf_stream['/Filter']}"
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
                                img = Image.frombytes(mode, (width, height), data)  # noqa:F841 pylint: disable=unused-variable
                            elif pdf_stream['/Filter'] == '/DCTDecode':
                                pass
                            elif pdf_stream['/Filter'] == '/JPXDecode':
                                pass
