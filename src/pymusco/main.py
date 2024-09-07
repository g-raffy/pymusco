'''
Created on Sep 8, 2018

@author: graffy
'''
import os
import datetime
import subprocess
import hashlib
import time
import shutil
import abc
from typing import List, Dict
from pathlib import Path
import PyPDF2  # sudo apt-get install python3-pypdf2
import cv2   # sudo apt-get install python3-opencv
from .core import Track, ITrackSelector, Orchestra, TableOfContents
from .pdf import extract_pdf_page_main_image
from .pdf import extract_pdf_page
from .core import get_stub_tracks
from .pdf import check_pdf, check_pdf_reader


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def is_locked(filepath: Path):
    """Checks if a file is locked by opening it in append mode.
    If no exception thrown, then the file is not locked.
    """
    locked = None
    file_object = None
    if os.path.exists(filepath):
        try:
            print(f"Trying to open {filepath}.")
            buffer_size = 8
            # Opening file in append mode and read the first 8 characters.
            file_object = open(filepath, 'a', buffer_size)  # pylint: disable=unspecified-encoding
            if file_object:
                print(f"{filepath} is not locked.")
                locked = False
        except IOError as e:
            print(f"File is locked (unable to open in append mode). {e.strerror}.")
            locked = True
        finally:
            if file_object:
                file_object.close()
                print(f"{filepath} closed.")
    else:
        print(f"{filepath} not found.")
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
            print(f"{filepath} hasn't arrived. Waiting {wait_time} seconds.")
            time.sleep(wait_time)
        # If the file exists but locked, wait wait_time seconds and check
        # again until it's no longer locked by another process.
        while is_locked(filepath):
            print(f"{filepath} is currently in use. Waiting {wait_time} seconds.")
            time.sleep(wait_time)


class StampDesc(object):

    def __init__(self, file_path: Path, scale: float = 1.0, tx: float = 500.0, ty: float = 770.0):
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
    def stamp_descs(self):
        return []

    def get_page_footers(self):
        return {}

    def get_sections(self):
        return {}


class SimplePdfDescription(PdfContents):
    image_file_paths: List[Path]

    def __init__(self, image_file_paths: List[Path]):
        """
        :param list(Path) image_file_paths: the file path for each image
        """
        self.image_file_paths = image_file_paths

    def get_image_file_paths(self) -> List[Path]:
        return self.image_file_paths


class StubContents(PdfContents):
    image_file_paths: List[Path]
    toc: TableOfContents
    _title: str
    _stamp_descs: List[StampDesc]
    page_footers: Dict[int, str]  # the footer text for each page
    page_to_section: Dict[int, str]  # the tracks description for each page
    page_info_line_y_pos : float

    def __init__(self, image_file_paths: List[Path], toc: TableOfContents, title: str, stamp_descs: List[StampDesc] = None, page_info_line_y_pos: float = 2.7):
        """
        creates a pdf file from a set of pages (either)

        :param list(str) image_file_paths: the file path for each image
        :param TableOfContents or None toc:
        :param str title: the title
        :param list(StampDesc) or stamp_descs: the images to overlay on each page
        """
        self.image_file_paths = image_file_paths
        self.toc = toc
        self._title = title
        self._stamp_descs = stamp_descs if stamp_descs is not None else []
        self.page_footers = {}
        self.page_to_section = {}
        self.page_info_line_y_pos = page_info_line_y_pos
        current_tracks = None
        current_track_page_number = 0
        current_track_num_pages = 0
        date_as_string = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        num_pages = len(self.image_file_paths)
        for page_index in range(1, num_pages + 1):
            if self.toc:
                page_tracks = self.toc.get_tracks_for_page(page_index)
                if len(page_tracks) > 0:
                    toc = self.toc
                    current_tracks = page_tracks
                    # print('current tracks :', [track.id for track in current_tracks])
                    current_track_page_number = 1
                    current_track_num_pages = toc.get_tracks_last_page_index(current_tracks, num_pages) - toc.get_tracks_first_page_index(current_tracks) + 1
                    self.page_to_section[page_index] = '/'.join([track.id for track in current_tracks])
                tracks_as_str = '/'.join([track.id for track in current_tracks])
                self.page_footers[page_index] = f'{self.title} on {date_as_string} - page {page_index}/{num_pages} : {tracks_as_str} - page {current_track_page_number}/{current_track_num_pages}'

            current_track_page_number += 1

    def get_image_file_paths(self):
        return self.image_file_paths

    @property
    def stamp_descs(self) -> List[StampDesc]:
        return self._stamp_descs

    @property
    def title(self) -> str:
        return self._title

    def get_page_footers(self) -> Dict[int, str]:
        return self.page_footers

    def get_sections(self) -> Dict[int, str]:
        return self.page_to_section


def images_to_pdf(pdf_contents: PdfContents, dst_pdf_file_path: Path):
    """
    creates a pdf file from a set of pages (either)

    :param PdfContents pdf_contents:
    :param list(str) image_file_paths: the file path for each image
    :param str dst_pdf_file_path: the destination pdf file path
    :param TableOfContents or None toc:
    :param str title: the title
    :param str or None stamp_file_path: the image to overlay on each page
    """
    assert isinstance(dst_pdf_file_path, Path)
    tmp_dir = Path('/tmp/pymusco')
    tmp_dir.mkdir(parents=True, exist_ok=True)

    latex_file_path = tmp_dir / 'stub.tex'
    with open(latex_file_path, 'w', encoding='utf-8') as latex_file:
        page_to_footers = pdf_contents.get_page_footers()
        page_to_section = pdf_contents.get_sections()
        has_toc = len(page_to_section) > 0
        latex_file.write(r'\documentclass[a4paper]{article}' + '\n')

        # latex_file.write(r'\usepackage[showframe, paperwidth=3.25in,paperheight=2.5in,margin=.5pt ]{geometry}' + '\n')
        # latex_file.write(r'\usepackage[showframe]{geometry}' + '\n')

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
            assert scanned_image_file_path is not None
            latex_file.write(r'\PageBackground{%s}' % scanned_image_file_path + '\n')

            for stamp_desc in pdf_contents.stamp_descs:
                assert stamp_desc.file_path is not None
                # shift=(current page.south west) sets the origin at the bottom left of the page
                latex_file.write(r'\begin{tikzpicture}[remember picture, overlay, shift=(current page.south west)]' + '\n')
                latex_file.write(r'\node at (%f,%f) {\includegraphics[scale=%f]{%s}};' % (stamp_desc.tx, stamp_desc.ty, stamp_desc.scale, stamp_desc.file_path) + '\n')
                latex_file.write(r'\end{tikzpicture}' + '\n')

            if page_index in page_to_section:
                latex_file.write(r'\invisiblesection{%s}' % page_to_section[page_index] + '\n')
            else:
                latex_file.write(r'\null' + '\n')

            if page_index in page_to_footers:
                text_block_pos_y = 29.7 - pdf_contents.page_info_line_y_pos
                latex_file.write(r'\begin{textblock*}{20cm}(0.2cm,%f cm) %% {block width} (coords)' % text_block_pos_y + '\n')
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
        assert return_code == 0, f"pass {pass_index} the command '{str(command)}' failed with return code {return_code}"
        if bug1_is_alive:
            assert not is_locked(tmp_dir + '/stub.pdf')
            time.sleep(10)  # this seems to prevent the file corruption

    stub_hash = 0
    if bug1_is_alive:
        stub_hash = md5(tmp_dir / 'stub.pdf')
        print(f"stub hash of {tmp_dir + '/stub.pdf'} : {str(stub_hash)}")
        check_pdf(tmp_dir + '/stub.pdf')

    dst_pdf_file_path.parent.mkdir(parents=True, exist_ok=True)
    # os.rename(tmp_dir / 'stub.pdf', dst_pdf_file_path)
    # (tmp_dir / 'stub.pdf').replace(dst_pdf_file_path)
    shutil.move(tmp_dir / 'stub.pdf', dst_pdf_file_path)
    if bug1_is_alive:
        stub_hash_after_move = md5(dst_pdf_file_path)
        print(f"stub hash of {dst_pdf_file_path} : {str(stub_hash_after_move)}")
        assert stub_hash == stub_hash_after_move
        check_pdf(dst_pdf_file_path)


def scan_to_stub(src_scanned_pdf_file_path: Path, dst_stub_pdf_file_path: Path, toc: TableOfContents, title: str, orchestra: Orchestra, stamp_descs: List[StampDesc] = None, page_info_line_y_pos: float = 1.0):
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
    :param list(StampDesc) stamp_descs: description of the stamps to overlay on each page
    :param float page_info_line_y_pos: y position of the status line relative to the bottom of the page
    """
    assert len(toc.tracks) > 0
    assert isinstance(src_scanned_pdf_file_path, Path)
    assert isinstance(dst_stub_pdf_file_path, Path)
    # check that the track_ids in the toc are known
    for track_id in toc.get_track_ids():
        try:
            track = Track(track_id, orchestra)  # noqa:F841 @UnusedVariable  pylint: disable=unused-variable
        except KeyError as e:  # noqa:F841 pylint: disable=unused-variable
            raise KeyError(f"Failed to identify track id '{track_id}'. Either its syntax is incorrect or the related instrument in not yet registered in the orchestra.") from e

    # tmp_dir = tempfile.mkdtemp()
    tmp_dir = Path('/tmp/pymusco')
    tmp_dir.mkdir(parents=True, exist_ok=True)

    scanned_image_file_paths = []
    with open(src_scanned_pdf_file_path, 'rb') as src_pdf_file:
        pdf_reader = PyPDF2.PdfReader(src_pdf_file)
        page_index = 0
        for page in pdf_reader.pages:
            print(f'page_index = {page_index}')
            # image_file_path = extract_pdf_page_main_image(page, image_dir=tmp_dir, image_name=('page%03d' % page_index))
            image_file_path = extract_pdf_page(page, image_dir=tmp_dir, image_name=f'page{page_index:03d}')

            scanned_image_file_paths.append(image_file_path)
            page_index += 1
            # break
    stamp_descs = stamp_descs if stamp_descs is not None else []
    images_to_pdf(StubContents(image_file_paths=scanned_image_file_paths, toc=toc, title=title, stamp_descs=stamp_descs, page_info_line_y_pos=page_info_line_y_pos), dst_stub_pdf_file_path)
    check_pdf(dst_stub_pdf_file_path)  # ensure that the generated pdf is supported by pypdf2


def stub_to_print(src_stub_file_path: Path, dst_print_file_path: Path, track_selector: ITrackSelector, orchestra: Orchestra):
    """
    :param Path src_stub_file_path:
    :param Path dst_print_file_path:
    :param ITrackSelector track_selector: the mechanism that computes the number of copies to do for each track
    :param Orchestra orchestra:
    :param dict(str, int) musician_count: gets the number of musicians for each musical intrument family
    :param TableOfContents or None stub_toc: if defined, gets the start page number for each track in the stub
    """

    check_pdf(src_stub_file_path)

    stub_toc = get_stub_tracks(src_stub_file_path, orchestra)
    print(stub_toc)

    track_to_print_count = track_selector.get_track_to_copy(stub_toc.get_track_ids())
    print(track_to_print_count)
    dst_print_file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(dst_print_file_path, 'wb') as print_file, open(dst_print_file_path.with_suffix('.log'), 'wt', encoding='utf-8') as log_file:
        print_pdf = PyPDF2.PdfWriter()
        log_file.write(f"contents of print file {dst_print_file_path} :\n\n")
        with open(src_stub_file_path, 'rb') as stub_file:
            stub_pdf = PyPDF2.PdfReader(stub_file)

            sorted_tracks = [Track(track_id, orchestra) for track_id in track_to_print_count.keys()]
            sorted_tracks.sort()
            ranges = []
            range_to_num_copies = {}
            range_to_tracks = {}
            for track in sorted_tracks:
                # for track_id, num_copies in track_to_print_count.iteritems().sorted():
                # track_id = track.get_id()
                num_copies = track_to_print_count[track.id]
                if num_copies > 0:
                    first_page_index = stub_toc.get_tracks_first_page_index([track])
                    last_page_index = stub_toc.get_tracks_last_page_index([track], len(stub_pdf.pages))
                    print(f'adding {num_copies} copies of {track.id} (pages {first_page_index}-{last_page_index})')
                    assert first_page_index <= last_page_index
                    assert last_page_index <= len(stub_pdf.pages)
                    page_range = (first_page_index, last_page_index)
                    if page_range in ranges:
                        # this page range has already been encountered. This can happen when multiple tracks share the same pages (eg crash cymbals are on the same pages as suspended cybal)
                        if track.instrument.get_player() == 'percussionist':
                            # we don't want to duplicate these shared pages for each track so
                            # we make as many copies as the track that asks for the most
                            range_to_num_copies[page_range] = max(range_to_num_copies[page_range], num_copies)
                            range_to_tracks[page_range].append(track.id)
                        else:
                            # here we're in the case of a page that contains 2 non percussion tracks (eg bassoon 1,2)
                            # these must be not be merged, but be treated as 2 separate copies :
                            # if we request 2 copies of bassoon 1 and 2 copies of bassoon 2, we want 4 copies of bassoon 1,2, not 2
                            range_to_num_copies[page_range] += num_copies
                            range_to_tracks[page_range].append(track.id)
                    else:
                        ranges.append(page_range)
                        range_to_num_copies[page_range] = num_copies
                        range_to_tracks[page_range] = [track.id]
            for page_range in ranges:
                (first_page_index, last_page_index) = page_range
                num_copies = range_to_num_copies[page_range]
                log_file.write(f"{num_copies} copies of {'/'.join(range_to_tracks[page_range])}\n")
                # print(page_range, num_copies, range_to_tracks[page_range])
                for copy_index in range(num_copies):  # @UnusedVariable pylint: disable=unused-variable
                    for page_index in range(first_page_index, last_page_index + 1):
                        track_page = stub_pdf.pages[page_index - 1]  # -1 to convert 1-based index into 0-based index
                        # print(f'adding page {page_index}')
                        print_pdf.add_page(track_page)

            log_file.write("\nunprinted tracks :\n\n")
            for label in stub_toc.get_track_ids():
                label_is_printed = False
                for tracks in range_to_tracks.values():
                    for track in tracks:
                        # print(track, label)
                        if track == label:
                            label_is_printed = True
                            break
                    if label_is_printed:
                        break
                if not label_is_printed:
                    log_file.write(f"no copies of {label}\n")
            print_pdf.write(print_file)


def split_double_pages(src_scanned_pdf_file_path: Path, dst_scanned_pdf_file_path: Path, split_pos: List[float] = [0.5]):  # pylint: disable=dangerous-default-value
    """
    :param list(float) split_pos: where to split the pages (ratio of the width of the double page). If this list contains more than one element, the positions are used sequencially and in a cyclic way
    """
    tmp_dir = Path('/tmp/pymusco')
    tmp_dir.mkdir(parents=True, exist_ok=True)
    scanned_image_file_paths = []
    with open(src_scanned_pdf_file_path, 'rb') as src_pdf_file:
        pdf_reader = PyPDF2.PdfReader(src_pdf_file)
        for page_index in range(len(pdf_reader.pages)):
            print(f'page_index = {page_index}')
            double_page = pdf_reader.pages[page_index]
            image_name = f'page{page_index:03d}'
            double_image_file_path = extract_pdf_page_main_image(double_page, image_dir=tmp_dir, image_name=image_name)
            double_png_file_path = f"{double_image_file_path}.png"
            # convert to png because opencv doesn't handle 1-bit tiff images
            subprocess.Popen(['convert', double_image_file_path, double_png_file_path]).communicate()
            # this command can fail with
            # graffy@graffy-ws2:~/private/pymusco$ convert /home/graffy/private/pymusco/tmp/page000.tiff /home/graffy/private/pymusco/tmp/page000.png
            # convert-im6.q16: DistributedPixelCache '127.0.0.1' @ error/distribute-cache.c/ConnectPixelCacheServer/244.
            # convert-im6.q16: cache resources exhausted `/home/graffy/private/pymusco/tmp/page000.png' @ error/cache.c/OpenPixelCache/3984.
            # convert-im6.q16: No IDATs written into file `/home/graffy/private/pymusco/tmp/page000.png' @ error/png.c/MagickPNGErrorHandler/1628.
            # to fix this I had to change the value of disk from 1GiB to 10GiB in sudo vi /etc/ImageMagick-6/policy.xml (see https://github.com/ImageMagick/ImageMagick/issues/396) so that :
            # graffy@graffy-ws2:~/private/pymusco$ identify -list resource
            # Resource limits:
            #   Width: 16KP
            #   Height: 16KP
            #   Area: 128MP
            #   Memory: 1GiB
            #   Map: 512MiB
            #   Disk: 10GiB
            #   File: 6144
            #   Thread: 8
            #   Throttle: 0
            #   Time: unlimited
            # double_image_file_path='/Users/graffy/data/Perso/pymusco/tmp/page177.png'
            print(double_png_file_path)
            double_page = cv2.imread(double_png_file_path, cv2.IMREAD_GRAYSCALE)
            assert double_page is not None
            x_split_pos = int(double_page.shape[1] * split_pos[page_index % len(split_pos)])

            single_image_file_path = f'{tmp_dir}/{image_name}_left.png'
            cv2.imwrite(single_image_file_path, double_page[:, :x_split_pos])
            scanned_image_file_paths.append(single_image_file_path)

            single_image_file_path = f'{tmp_dir}/{image_name}_right.png'
            cv2.imwrite(single_image_file_path, double_page[:, x_split_pos:])
            scanned_image_file_paths.append(single_image_file_path)

    images_to_pdf(SimplePdfDescription(image_file_paths=scanned_image_file_paths), dst_scanned_pdf_file_path)


def crop_pdf(src_scanned_pdf_file_path: Path, dst_scanned_pdf_file_path: Path, x_scale: float, y_scale: float):
    tmp_dir = Path('/tmp/pymusco')
    tmp_dir.mkdir(parents=True, exist_ok=True)
    scanned_image_file_paths = []
    with open(src_scanned_pdf_file_path, 'rb') as src_pdf_file:
        pdf_reader = PyPDF2.PdfReader(src_pdf_file)
        for page_index in range(len(pdf_reader.pages)):
            print(f'page_index = {page_index}')
            page = pdf_reader.pages[page_index]
            image_name = f'page{page_index:03d}'
            image_file_path = extract_pdf_page_main_image(page, image_dir=tmp_dir, image_name=image_name)
            png_file_path = f"{image_file_path}.png"
            # convert to png because opencv doesn't handle 1-bit tiff images
            subprocess.Popen(['convert', image_file_path, png_file_path]).communicate()
            # double_image_file_path='/Users/graffy/data/Perso/pymusco/tmp/page177.png'
            print(png_file_path)

            image = cv2.imread(png_file_path, cv2.IMREAD_GRAYSCALE)
            assert image is not None
            x_size = int(x_scale * image.shape[1])
            y_size = int(y_scale * image.shape[0])

            cropped_image_file_path = f'{tmp_dir}/{image_name}_cropped.png'
            cv2.imwrite(cropped_image_file_path, image[:y_size, :x_size])
            scanned_image_file_paths.append(cropped_image_file_path)

    images_to_pdf(SimplePdfDescription(image_file_paths=scanned_image_file_paths), dst_scanned_pdf_file_path)


def pdf_is_readable_by_pypdf2(src_pdf_path: Path):
    with open(src_pdf_path, 'rb') as src_pdf_file:
        try:
            src_pdf = PyPDF2.PdfReader(src_pdf_file)
            num_pages = len(src_pdf.pages)  # noqa:F841 pylint: disable=unused-variable
            return True
        except NotImplementedError as error:
            if str(error) == "only algorithm code 1 and 2 are supported":
                return False
            else:
                raise error
        except PyPDF2.errors.PdfReadError as error:  # noqa:F841 pylint: disable=unused-variable
            return False


def merge_pdf(dst_pdf_path: Path, src_pdf_paths: Path):
    dst_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with open(dst_pdf_path, 'wb') as dst_pdf_file:
        dst_pdf = PyPDF2.PdfWriter()
        for src_pdf_path in src_pdf_paths:
            print(src_pdf_path)
            if not pdf_is_readable_by_pypdf2(src_pdf_path):
                print(f'warning : {src_pdf_path} is not readable by pypdf2... converting it')
                fixed_pdf_path = '/tmp/readable-by-pypdf2.pdf'
                remove_unneeded_pdf_password(src_pdf_path, fixed_pdf_path)
                src_pdf_path = fixed_pdf_path
            with open(src_pdf_path, 'rb') as src_pdf_file:
                src_pdf = PyPDF2.PdfReader(src_pdf_file)
                for src_page in range(src_pdf.pages):
                    dst_pdf.add_page(src_page)
                dst_pdf.write(dst_pdf_file)


def pdftk_is_available() -> bool:
    completed_process = subprocess.run(['pdftk'], stdout=subprocess.PIPE, check=False)
    return completed_process.returncode == 0


def remove_unneeded_pdf_password(src_pdf_path: Path, dst_pdf_path: Path):
    """
        Some pdfs have an owner password that is not required to view the file. For example :
            graffy@graffy-ws2:~/private/melting-notes/partitions/scans$ pdftk ./215-avengers-age-of-ultron/avengers-the-age-of-ultron-main-theme---piccolo.pdf dump_data
            WARNING: The creator of the input PDF:
               ./215-avengers-age-of-ultron/avengers-the-age-of-ultron-main-theme---piccolo.pdf
               has set an owner password (which is not required to handle this PDF).
               You did not supply this password. Please respect any copyright.

        This causes pypdf2 to fail retreiving the number of pages :
            File "/usr/lib/python3/dist-packages/PyPDF2/pdf.py", line 1147, in pages
                self.decrypt('')
            File "/usr/lib/python3/dist-packages/PyPDF2/pdf.py", line 1987, in decrypt
                return self._decrypt(password)
            File "/usr/lib/python3/dist-packages/PyPDF2/pdf.py", line 1996, in _decrypt
                raise NotImplementedError("only algorithm code 1 and 2 are supported")

        So, this function intends to simplify this pdf file so that pypdf2 can handle it.
    """
    assert pdftk_is_available(), 'the pdftk command is missing. Please install it as it is required.'

    command = ['pdftk', src_pdf_path, 'input_pw', '', 'output', dst_pdf_path]
    completed_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    assert completed_process.returncode == 0, "command failed : %s" % command
    # pdftk ./215-avengers-age-of-ultron/avengers-the-age-of-ultron-main-theme---piccolo.pdf input_pw '' output ~/toto/unsecured.pdf
