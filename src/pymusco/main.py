'''
Created on Sep 8, 2018

@author: graffy
'''
import os
import datetime
import subprocess
import hashlib
import time
import PyPDF2
from .core import Track
from .pdf import extract_pdf_page_main_image
from .pdf import extract_pdf_page
from .core import get_stub_tracks
from .pdf import check_pdf
import cv2
import abc


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def is_locked(filepath):
    """Checks if a file is locked by opening it in append mode.
    If no exception thrown, then the file is not locked.
    """
    locked = None
    file_object = None
    if os.path.exists(filepath):
        try:
            print "Trying to open %s." % filepath
            buffer_size = 8
            # Opening file in append mode and read the first 8 characters.
            file_object = open(filepath, 'a', buffer_size)
            if file_object:
                print "%s is not locked." % filepath
                locked = False
        except IOError, message:
            print "File is locked (unable to open in append mode). %s." % \
                  message
            locked = True
        finally:
            if file_object:
                file_object.close()
                print "%s closed." % filepath
    else:
        print "%s not found." % filepath
    return locked


def wait_for_files(filepaths):
    """Checks if the files are ready.

    For a file to be ready it must exist and can be opened in append
    mode.
    """
    wait_time = 5
    for filepath in filepaths:
        # If the file doesn't exist, wait wait_time seconds and try again
        # until it's found.
        while not os.path.exists(filepath):
            print "%s hasn't arrived. Waiting %s seconds." % \
                  (filepath, wait_time)
            time.sleep(wait_time)
        # If the file exists but locked, wait wait_time seconds and check
        # again until it's no longer locked by another process.
        while is_locked(filepath):
            print "%s is currently in use. Waiting %s seconds." % \
                  (filepath, wait_time)
            time.sleep(wait_time)


class StampDesc(object):

    def __init__(self, file_path, scale=1.0, tx=500.0, ty=770.0):
        self.file_path = file_path
        self.scale = scale
        self.tx = tx
        self.ty = ty


class PdfContents(object):

    def __init__(self):
        pass

    @abc.abstractmethod
    def get_image_file_paths(self):
        pass

    @property
    def title(self):
        return None

    @property
    def stamp_desc(self):
        return None

    def get_page_footers(self):
        return {}

    def get_sections(self):
        return {}


class SimplePdfDescription(PdfContents):
    def __init__(self, image_file_paths):
        """
        :param list(str) image_file_paths: the file path for each image
        """
        self.image_file_paths = image_file_paths

    def get_image_file_paths(self):
        return self.image_file_paths


class StubContents(PdfContents):
    def __init__(self, image_file_paths, toc, title, stamp_desc=None):
        """
        creates a pdf file from a set of pages (either)

        :param list(str) image_file_paths: the file path for each image
        :param TableOfContents or None toc:
        :param str title: the title
        :param StampDesc or None stamp_desc: the image to overlay on each page
        """
        self.image_file_paths = image_file_paths
        self.toc = toc
        self._title = title
        self._stamp_desc = stamp_desc
        self.page_footers = {}
        self.page_to_section = {}
        current_tracks = None
        current_track_page_number = 0
        current_track_num_pages = 0
        date_as_string = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        for page_index in range(1, len(self.image_file_paths) + 1):

            if self.toc and len(self.toc.get_labels_for_page(page_index)) > 0:
                toc = self.toc
                current_tracks = '/'.join(toc.get_labels_for_page(page_index))
                print('current tracks :', current_tracks)
                current_track_page_number = 1
                current_track_num_pages = toc.get_tracks_last_page_index(current_tracks, len(self.image_file_paths)) - toc.get_tracks_first_page_index(current_tracks) + 1
                self.page_to_section[page_index] = current_tracks

            self.page_footers[page_index] = r'%s on %s - page %d/%d : %s - page %d/%d' % (self.title, date_as_string, page_index, len(self.image_file_paths), current_tracks, current_track_page_number, current_track_num_pages)

            current_track_page_number += 1

    def get_image_file_paths(self):
        return self.image_file_paths

    @property
    def stamp_desc(self):
        return self._stamp_desc

    @property
    def title(self):
        return self._title

    def get_page_footers(self):
        return self.page_footers

    def get_sections(self):
        return self.page_to_section


def images_to_pdf(pdf_contents, dst_pdf_file_path):
    """
    creates a pdf file from a set of pages (either)

    :param PdfContents pdf_contents:
    :param list(str) image_file_paths: the file path for each image
    :param str dst_pdf_file_path: the destination pdf file path
    :param TableOfContents or None toc:
    :param str title: the title
    :param str or None stamp_file_path: the image to overlay on each page
    """
    tmp_dir = os.getcwd() + '/tmp'

    latex_file_path = tmp_dir + '/stub.tex'
    with open(latex_file_path, 'w') as latex_file:
        page_to_footers = pdf_contents.get_page_footers()
        page_to_section = pdf_contents.get_sections()
        has_toc = len(page_to_section) > 0
        latex_file.write(r'\documentclass{article}' + '\n')

        latex_file.write(r'% tikz package is used to use scanned images as background' + '\n')
        latex_file.write(r'\usepackage{tikz}' + '\n')

        if has_toc:
            latex_file.write(r'% hyperref package is used to create a clickable table of contents' + '\n')
            latex_file.write(r'\usepackage{hyperref}' + '\n')
            latex_file.write(r'\hypersetup{' + '\n')
            latex_file.write(r'   colorlinks,' + '\n')
            latex_file.write(r'   citecolor=black,' + '\n')
            latex_file.write(r'   filecolor=black,' + '\n')
            latex_file.write(r'   urlcolor=black' + '\n')
            latex_file.write(r'}')

        latex_file.write(r'% textpos package is used to position text at a specific position in the page (eg page number)' + '\n')
        latex_file.write(r'\usepackage[absolute,overlay]{textpos}')

        if has_toc:
            latex_file.write(r'% setspace package is used to to reduce the spacing between table of contents items' + '\n')
            latex_file.write(r'\usepackage{setspace}')
            latex_file.write(r'\renewcommand{\contentsname}{}' + '\n')  # remove the title of the table of contents ("contents")

        latex_file.write(r'% command to declare invisible sections (sections that appear in the table of contents but not in the text itself)' + '\n')
        latex_file.write(r'\newcommand\invisiblesection[1]{%' + '\n')
        latex_file.write(r'  \refstepcounter{section}%' + '\n')
        latex_file.write(r'  \addcontentsline{toc}{section}{\protect\numberline{\thesection}#1}%' + '\n')
        latex_file.write(r'  \sectionmark{#1}}' + '\n')

        latex_file.write(r'\newcommand*{\PageBackground}[1]{' + '\n')
        latex_file.write(r'    \tikz[remember picture,overlay] \node[opacity=1.0,inner sep=0pt] at (current page.center){\includegraphics[width=\paperwidth,height=\paperheight]{#1}};')

        latex_file.write(r'% remove page numbers as default' + '\n')
        latex_file.write(r'\thispagestyle{empty}' + '\n')

        latex_file.write(r'}')
        latex_file.write(r'\begin{document}' + '\n')

        if pdf_contents.title:

            latex_file.write(r'  \title{%s}' % pdf_contents.title + '\n')
            latex_file.write(r'  \date{}' + '\n')  # remove the date from the title

            latex_file.write(r'  \maketitle' + '\n')

        if has_toc:
            latex_file.write(r'  \begin{spacing}{0.1}' + '\n')

            latex_file.write(r'  \tableofcontents' + '\n')
            latex_file.write(r'  \end{spacing}' + '\n')

        page_index = 1
        for scanned_image_file_path in pdf_contents.get_image_file_paths():
            latex_file.write(r'\newpage' + '\n')
            latex_file.write(r'\PageBackground{%s}' % scanned_image_file_path + '\n')

            if pdf_contents.stamp_desc:
                stamp_desc = pdf_contents.stamp_desc
                latex_file.write(r'\begin{tikzpicture}[overlay]' + '\n')
                latex_file.write(r'\node at (%f,%f) {\includegraphics[scale=%f]{%s}};' % (stamp_desc.tx, stamp_desc.ty, stamp_desc.scale, stamp_desc.file_path) + '\n')
                latex_file.write(r'\end{tikzpicture}' + '\n')

            if page_index in page_to_section:
                latex_file.write(r'\invisiblesection{%s}' % page_to_section[page_index] + '\n')
            else:
                latex_file.write(r'\null' + '\n')

            if page_index in page_to_footers:
                latex_file.write(r'\begin{textblock*}{20cm}(0.2cm,27cm) % {block width} (coords)' + '\n')
                latex_file.write(page_to_footers[page_index] + '\n')
                latex_file.write(r'\end{textblock*}' + '\n')

            page_index += 1
        latex_file.write(r'\end{document}' + '\n')

    bug1_is_alive = False  # True  # https://github.com/g-raffy/pymusco/issues/1

    # compile stub.tex document into stub.pdf
    for pass_index in range(2):  # the compilation of latex files require 2 passes to get correct table of contents.
        # note : we use subprocess.Popen instead of subprocess.check_call because for some unexplained reasons, subprocess.check_call doesn't wait for the call to complete before ending. This resulted in currupted pdf files (see https://github.com/g-raffy/pymusco/issues/1)
        command = ["pdflatex", "-halt-on-error", "./stub.tex"]
        p = subprocess.Popen(command, cwd=tmp_dir)
        return_code = p.wait()
        assert return_code == 0, "pass %d the command '%s' failed with return code %d" % (pass_index, str(command), return_code)
        if bug1_is_alive:
            assert not is_locked(tmp_dir + '/stub.pdf')
            time.sleep(10)  # this seems to prevent the file corruption

    stub_hash = 0
    if bug1_is_alive:
        stub_hash = md5(tmp_dir + '/stub.pdf')
        print("stub hash of %s : %s" % (tmp_dir + '/stub.pdf', str(stub_hash)))
        check_pdf(tmp_dir + '/stub.pdf')

    os.rename(tmp_dir + '/stub.pdf', dst_pdf_file_path)
    if bug1_is_alive:
        stub_hash_after_move = md5(dst_pdf_file_path)
        print("stub hash of %s : %s" % (dst_pdf_file_path, str(stub_hash_after_move)))
        assert stub_hash == stub_hash_after_move
        check_pdf(dst_pdf_file_path)


def scan_to_stub(src_scanned_pdf_file_path, dst_stub_pdf_file_path, toc, title, orchestra, stamp_desc=None):
    """
    creates musical score stub from a musical score raw scan :
    - adds a table of contents
    - adds a stamp
    - numbers the pages

    :param str src_scanned_pdf_file_path: the source file that is expected to contain the scanned musical scores
    :param str dst_stub_pdf_file_path: the destination file that is expected to contain the stub of musical scores
    :param TableOfContents toc:
    :param str title: musical piece title
    :param Orchestra orchestra: the inventory of musical instruments
    :param StampDesc or None stamp_desc: desctiption of the stamp to overlay on each page
    """

    # check that the track_ids in the toc are known
    for track_id in toc.get_labels():
        try:
            track = Track(track_id, orchestra)  # @UnusedVariable  pylint: disable=unused-variable
        except KeyError as e:
            raise Exception("Failed to identify track id '%s'. Either its syntax is incorrect or the related instrument (%s) in not yet registered in the orchestra." % (track_id, e.message))

    # tmp_dir = tempfile.mkdtemp()
    tmp_dir = os.getcwd() + '/tmp'

    scanned_image_file_paths = []
    with open(src_scanned_pdf_file_path, 'rb') as src_pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(src_pdf_file)
        # pdfReader.numPages
        # 19
        for page_index in range(pdf_reader.numPages):
            print('page_index = %d' % page_index)
            page = pdf_reader.getPage(page_index)
            # image_file_path = extract_pdf_page_main_image(page, image_dir=tmp_dir, image_name=('page%03d' % page_index))
            image_file_path = extract_pdf_page(page, image_dir=tmp_dir, image_name=('page%03d' % page_index))

            scanned_image_file_paths.append(image_file_path)
            # break

    images_to_pdf(StubContents(image_file_paths=scanned_image_file_paths, toc=toc, title=title, stamp_desc=stamp_desc), dst_stub_pdf_file_path)


def stub_to_print(src_stub_file_path, dst_print_file_path, track_selector, orchestra):
    """
    :param str src_stub_file_path:
    :param str dst_print_file_path:
    :param ITrackSelector track_selector: the mechanism that computes the number of copies to do for each track
    :param Orchestra orchestra:
    :param dict(str, int) musician_count: gets the number of musicians for each musical intrument family
    :param TableOfContents or None stub_toc: if defined, gets the start page number for each track in the stub
    """
    stub_toc = get_stub_tracks(src_stub_file_path)
    print(stub_toc)

    track_to_print_count = track_selector.get_track_to_copy(stub_toc.get_labels())
    print(track_to_print_count)

    with open(dst_print_file_path, 'wb') as print_file, open(dst_print_file_path.replace('.pdf', '.log'), 'wb') as log_file:
        print_pdf = PyPDF2.PdfFileWriter()
        log_file.write("contents of print file %s :\n\n" % dst_print_file_path)
        with open(src_stub_file_path, 'rb') as stub_file:
            stub_pdf = PyPDF2.PdfFileReader(stub_file)

            sorted_tracks = [Track(track_id, orchestra) for track_id in track_to_print_count.iterkeys()]
            sorted_tracks.sort()
            ranges = []
            range_to_num_copies = {}
            range_to_tracks = {}
            for track in sorted_tracks:
                # for track_id, num_copies in track_to_print_count.iteritems().sorted():
                track_id = track.get_id()
                num_copies = track_to_print_count[track_id]
                if num_copies > 0:
                    first_page_index = stub_toc.get_tracks_first_page_index(track_id)
                    last_page_index = stub_toc.get_tracks_last_page_index(track_id, stub_pdf.getNumPages())
                    print('adding %d copies of %s (pages %d-%d)' % (num_copies, track_id, first_page_index, last_page_index))
                    assert first_page_index <= last_page_index
                    assert last_page_index <= stub_pdf.getNumPages()
                    page_range = (first_page_index, last_page_index)
                    if page_range in ranges:
                        # this page range has already been encountered. This can happen when multiple tracks share the same pages (eg crash cymbals are on the same pages as suspended cybal)
                        if track.instrument.get_player() == 'percussionist':
                            # we don't want to duplicate these shared pages for each track so
                            # we make as many copies as the track that asks for the most
                            range_to_num_copies[page_range] = max(range_to_num_copies[page_range], num_copies)
                            range_to_tracks[page_range].append(track_id)
                        else:
                            # here we're in the case of a page that contains 2 non percussion tracks (eg bassoon 1,2)
                            # these must be not be merged, but be treated as 2 separate copies :
                            # if we request 2 copies of bassoon 1 and 2 copies of bassoon 2, we want 4 copies of bassoon 1,2, not 2
                            range_to_num_copies[page_range] += num_copies
                            range_to_tracks[page_range].append(track_id)
                    else:
                        ranges.append(page_range)
                        range_to_num_copies[page_range] = num_copies
                        range_to_tracks[page_range] = [track_id]
            for page_range in ranges:
                (first_page_index, last_page_index) = page_range
                num_copies = range_to_num_copies[page_range]
                log_file.write("%d copies of %s\n" % (num_copies, '/'.join(range_to_tracks[page_range])))
                # print(page_range, num_copies)
                for copy_index in range(num_copies):  # @UnusedVariable pylint: disable=unused-variable
                    for page_index in range(first_page_index, last_page_index + 1):
                        track_page = stub_pdf.getPage(page_index - 1)  # -1 to convert 1-based index into 0-based index
                        # print('adding page %d' % page_index)
                        print_pdf.addPage(track_page)

            log_file.write("\nunprinted tracks :\n\n")
            for label in stub_toc.get_labels():
                label_is_printed = False
                for tracks in range_to_tracks.itervalues():
                    for track in tracks:
                        # print(track, label)
                        if track == label:
                            label_is_printed = True
                            break
                    if label_is_printed:
                        break
                if not label_is_printed:
                    log_file.write("no copies of %s\n" % label)
            print_pdf.write(print_file)


def split_double_pages(src_scanned_pdf_file_path, dst_scanned_pdf_file_path, split_pos=[0.5]):
    """
    :param list(float) split_pos: where to split the pages (ratio of the width of the double page). If this list contains more than one element, the positions are used sequencially and in a cyclic way
    """
    tmp_dir = os.getcwd() + '/tmp'
    scanned_image_file_paths = []
    with open(src_scanned_pdf_file_path, 'rb') as src_pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(src_pdf_file)
        for page_index in range(pdf_reader.numPages):
            print('page_index = %d' % page_index)
            double_page = pdf_reader.getPage(page_index)
            image_name = ('page%03d' % page_index)
            double_image_file_path = extract_pdf_page_main_image(double_page, image_dir=tmp_dir, image_name=image_name)
            double_png_file_path = "%s.png" % double_image_file_path
            # convert to png because opencv doesn't handle 1-bit tiff images
            subprocess.Popen(['convert', double_image_file_path, double_png_file_path]).communicate()
            # double_image_file_path='/Users/graffy/data/Perso/pymusco/tmp/page177.png'
            print(double_png_file_path)
            double_page = cv2.imread(double_png_file_path, cv2.IMREAD_GRAYSCALE)
            assert double_page is not None
            x_split_pos = int(double_page.shape[1] * split_pos[page_index % len(split_pos)])

            single_image_file_path = '%s/%s_left.png' % (tmp_dir, image_name)
            cv2.imwrite(single_image_file_path, double_page[:, :x_split_pos])
            scanned_image_file_paths.append(single_image_file_path)

            single_image_file_path = '%s/%s_right.png' % (tmp_dir, image_name)
            cv2.imwrite(single_image_file_path, double_page[:, x_split_pos:])
            scanned_image_file_paths.append(single_image_file_path)

    images_to_pdf(SimplePdfDescription(image_file_paths=scanned_image_file_paths), dst_scanned_pdf_file_path)


def crop_pdf(src_scanned_pdf_file_path, dst_scanned_pdf_file_path, x_scale, y_scale):
    tmp_dir = os.getcwd() + '/tmp'
    scanned_image_file_paths = []
    with open(src_scanned_pdf_file_path, 'rb') as src_pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(src_pdf_file)
        for page_index in range(pdf_reader.numPages):
            print('page_index = %d' % page_index)
            page = pdf_reader.getPage(page_index)
            image_name = ('page%03d' % page_index)
            image_file_path = extract_pdf_page_main_image(page, image_dir=tmp_dir, image_name=image_name)
            png_file_path = "%s.png" % image_file_path
            # convert to png because opencv doesn't handle 1-bit tiff images
            subprocess.Popen(['convert', image_file_path, png_file_path]).communicate()
            # double_image_file_path='/Users/graffy/data/Perso/pymusco/tmp/page177.png'
            print(png_file_path)

            image = cv2.imread(png_file_path, cv2.IMREAD_GRAYSCALE)
            assert image is not None
            x_size = int(x_scale * image.shape[1])
            y_size = int(y_scale * image.shape[0])

            cropped_image_file_path = '%s/%s_cropped.png' % (tmp_dir, image_name)
            cv2.imwrite(cropped_image_file_path, image[:y_size, :x_size])
            scanned_image_file_paths.append(cropped_image_file_path)

    images_to_pdf(SimplePdfDescription(image_file_paths=scanned_image_file_paths), dst_scanned_pdf_file_path)
