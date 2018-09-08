from PIL import Image
import struct
import cv2
import PyPDF2
import subprocess
import os
import shutil

"""
Extract images from pdf: http://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python
Extract images coded with CCITTFaxDecode in .net: http://stackoverflow.com/questions/2641770/extracting-image-from-pdf-with-ccittfaxdecode-filter
TIFF format and tags: http://www.awaresystems.be/imaging/tiff/faq.html
"""
# https://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python/34116472#34116472


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
        color_space, indirect_object = pdf_stream['/ColorSpace']  # @UnusedVariable
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
    saved_image_file_path = None
    for obj in xObject:
        if xObject[obj]['/Subtype'] == '/Image':
            try:
                saved_image_file_path = extract_pdf_stream_image(pdf_stream=xObject[obj], image_dir=image_dir, image_name=image_name)
            except NotImplementedError as e:
                print("warning : NotImplementedError(%s). Maybe pypdf2 is unable to decode this stream. Falling back to a resampling method." % e.message)
                image = pdf_page_to_png(pdf_page, resolution=300)
                saved_image_file_path = "%s/%s.png" % (image_dir, image_name)
                cv2.imwrite(saved_image_file_path, image)
                print("resampled image saved to %s" % saved_image_file_path)
    return saved_image_file_path


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
    subprocess.check_call(['/opt/local/bin/convert', '-density', '%d' % resolution, tmp_pdf_file_path, tmp_png_file_path])
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
    pdf_out = PyPDF2.PdfFileMerger()

    # read `pdf_in` into `pdf_out`, using PyPDF2.PdfFileMerger()
    # with open(pdf_in_filename, 'rb') as inputStream:
    inputStream = open(pdf_in_filename, 'rb')
    pdf_out.append(inputStream, import_bookmarks=False)

    # copy/preserve existing metainfo
    pdf_in = PyPDF2.PdfFileReader(pdf_in_filename)
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
