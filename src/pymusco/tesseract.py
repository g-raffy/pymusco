'''
Created on Sep 8, 2018

@author: graffy
'''
import os
import PyPDF2
import tesseract
import cv2
from PIL import Image
from .pdf import pdf_page_to_png
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


def extract_pdf_text(src_pdf_file_path):
    os.environ["TESSDATA_PREFIX"] = '/opt/local/share'  # this is required otherwise tesseract complains about file permissions

    with open(src_pdf_file_path, 'rb') as src_pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(src_pdf_file)
        # pdfReader.numPages
        # 19
        for page_index in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_index)

            image = pdf_page_to_png(page, resolution=72)
            # extract_pdf_page_images(page)
            
            tmp_img_path = '/tmp/titi.png'
            cv2.imwrite(tmp_img_path, image)
            text = tesseract.image_to_string(Image.open(tmp_img_path))  # , lang='deu')
            print(text)
