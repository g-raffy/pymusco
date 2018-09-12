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
from .core import rotate_image
from .core import get_stub_tracks
from .pdf import check_pdf


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


def scan_to_stub(src_scanned_pdf_file_path, dst_stub_pdf_file_path, toc, title, orchestra, stamp_file_path=None, scale=1.0, tx=500.0, ty=770.0, rotate_images=False):
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
    :param str or None stamp_file_path:
    """

    # check that the track_ids in the toc are known
    for track_id in toc.get_labels():
        try:
            track = Track(track_id, orchestra)  # @UnusedVariable
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
            image_file_path = extract_pdf_page_main_image(page, image_dir=tmp_dir, image_name=('page%03d' % page_index))
            
            if rotate_images:
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
        
        latex_file.write(r'% textpos package is used to position text at a specific position in the page (eg page number)' + '\n')
        latex_file.write(r'\usepackage[absolute,overlay]{textpos}')
        
        latex_file.write(r'% setspace package is used to to reduce the spacing between table of contents imes' + '\n')
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

        latex_file.write(r'  \title{%s}' % title + '\n')
        latex_file.write(r'  \date{}' + '\n')  # remove the date from the title
        
        latex_file.write(r'  \maketitle' + '\n')
        
        latex_file.write(r'  \begin{spacing}{0.1}' + '\n')
            
        latex_file.write(r'  \tableofcontents' + '\n')
        latex_file.write(r'  \end{spacing}' + '\n')
        
        current_track = None
        current_track_page_number = 0
        current_track_num_pages = 0
        date_as_string = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        page_index = 1
        for scanned_image_file_path in scanned_image_file_paths:
            latex_file.write(r'\newpage' + '\n')
            latex_file.write(r'\PageBackground{%s}' % scanned_image_file_path + '\n')
            
            if stamp_file_path is not None:
                latex_file.write(r'\begin{tikzpicture}[overlay]' + '\n')
                latex_file.write(r'\node at (%f,%f) {\includegraphics[scale=%f]{%s}};' % (tx, ty, scale, stamp_file_path) + '\n')
                latex_file.write(r'\end{tikzpicture}' + '\n')

            if toc.get_label(page_index) is not None:
                current_track = toc.get_label(page_index)
                current_track_page_number = 1
                current_track_num_pages = toc.get_label_last_page_index(current_track, len(scanned_image_file_paths)) - toc.get_label_first_page_index(current_track) + 1
                latex_file.write(r'\invisiblesection{%s}' % current_track + '\n')
            else:
                latex_file.write(r'\null' + '\n')

            latex_file.write(r'\begin{textblock*}{20cm}(0.2cm,27cm) % {block width} (coords)' + '\n')
            latex_file.write(r'%s on %s - page %d/%d : %s - page %d/%d' % (title, date_as_string, page_index, len(scanned_image_file_paths), current_track, current_track_page_number, current_track_num_pages) + '\n')
            latex_file.write(r'\end{textblock*}' + '\n')

            page_index += 1
            current_track_page_number += 1
        latex_file.write(r'\end{document}' + '\n')

    bug1_is_alive = True  # https://github.com/g-raffy/pymusco/issues/1

    # compile stub.tex document into stub.pdf
    for pass_index in range(2):  # the compilation of latex files require 2 passes to get correct table of contents.
        # note : we use subprocess.Popen instead of subprocess.check_call because for some unexplained reasons, subprocess.check_call doesn't wait for the call to complete before ending. This resulted in currupted pdf files (see https://github.com/g-raffy/pymusco/issues/1)
        command = ["pdflatex", "-halt-on-error", "./stub.tex"]
        p = subprocess.Popen(command, cwd=tmp_dir)
        return_code = p.wait()
        assert return_code == 0, "pass %d the command '%s' failed with return code %d" % (pass_index, str(command), return_code)
        if bug1_is_alive:
            assert not is_locked(tmp_dir + '/stub.pdf')
            time.sleep(5)  # this seems to prevent the file corruption
    
    stub_hash = 0
    if bug1_is_alive:
        stub_hash = md5(tmp_dir + '/stub.pdf')
        print("stub hash of %s : %s" % (tmp_dir + '/stub.pdf', str(stub_hash)))
        check_pdf(tmp_dir + '/stub.pdf')
        
    os.rename(tmp_dir + '/stub.pdf', dst_stub_pdf_file_path)
    if bug1_is_alive:
        stub_hash_after_move = md5(dst_stub_pdf_file_path)
        print("stub hash of %s : %s" % (dst_stub_pdf_file_path, str(stub_hash_after_move)))
        assert stub_hash == stub_hash_after_move
        check_pdf(dst_stub_pdf_file_path)


def stub_to_print(src_stub_file_path, dst_print_file_path, track_selector, orchestra, stub_toc=None):
    """
    :param str src_stub_file_path:
    :param str dst_print_file_path:
    :param ITrackSelector track_selector: the mechanism that computes the number of copies to do for each track
    :param Orchestra orchestra:
    :param dict(str, int) musician_count: gets the number of musicians for each musical intrument family
    :param TableOfContents or None stub_toc: if defined, gets the start page number for each track in the stub
    """
    if stub_toc is None:
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
                    first_page_index = stub_toc.get_label_first_page_index(track_id)
                    last_page_index = stub_toc.get_label_last_page_index(track_id, stub_pdf.getNumPages())
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
                for copy_index in range(num_copies):  # @UnusedVariable
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