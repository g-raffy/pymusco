# encoding:utf8

# how to use :
# [OK]graffy@pr079234:~/data/Perso/pymusco[09:42:12]>PYTHONPATH=./src python ./crop_pdf.py

import io
import os
import cv2
from PIL import Image
import struct
import subprocess
import pymusco  # pylint: disable=import-error
import sys
import copy
import ntpath
import re
import ntpath

if __name__ == '__main__':
    #pymusco.split_double_pages(src_scanned_pdf_file_path='/Users/graffy/data/Perso/MeltingNotes_work.git/partitions/scans/191-seagate-overture_double.pdf', dst_scanned_pdf_file_path='/Users/graffy/data/Perso/MeltingNotes_work.git/partitions/scans/191-seagate-overture.pdf', split_pos=[4900.0 / 9921.0, 4850.0 / 9921.0])
    letter_ratio = 8.5/11.0
    a4_ratio = 21.0/29.7
    x_scale=0.89
    y_scale=x_scale/letter_ratio*a4_ratio
    #pymusco.crop_pdf(src_scanned_pdf_file_path='/Users/graffy/data/Perso/MeltingNotes_work.git/partitions/scans/toto-original-scan.pdf', dst_scanned_pdf_file_path='/Users/graffy/data/Perso/MeltingNotes_work.git/partitions/scans/toto.pdf', x_scale=x_scale, y_scale=y_scale)
    pymusco.crop_pdf(src_scanned_pdf_file_path='/Users/graffy/data/Perso/MeltingNotes_work.git/partitions/scans/194-atlantis-original-scan.pdf', dst_scanned_pdf_file_path='/Users/graffy/data/Perso/MeltingNotes_work.git/partitions/scans/194-atlantis.pdf', x_scale=x_scale, y_scale=y_scale)


