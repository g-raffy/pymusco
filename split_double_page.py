# encoding:utf8

# how to use :
# [OK]graffy@pr079234:~/data/Perso/pymusco[09:42:12]>PYTHONPATH=./src python ./split_double_page.py

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
    #pymusco.split_double_pages(src_scanned_pdf_file_path='/Users/graffy/data/Perso/MeltingNotes_work.git/partitions/scans/116-jump-in-the-line_double.pdf', dst_scanned_pdf_file_path='/Users/graffy/data/Perso/MeltingNotes_work.git/partitions/scans/116-jump-in-the-line_2.pdf', split_pos=[596.46 / 1190.52])
    pymusco.split_double_pages(src_scanned_pdf_file_path='/Users/graffy/data/Perso/MeltingNotes_work.git/partitions/scans/197-el-agua-prodigiosa_double.pdf', dst_scanned_pdf_file_path='/Users/graffy/data/Perso/MeltingNotes_work.git/partitions/scans/197-el-agua-prodigiosa.pdf', split_pos=[591.00 / 1191.00])
