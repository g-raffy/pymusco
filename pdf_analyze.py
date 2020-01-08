# sudo port install py27-pypdf2
import PyPDF2
from PyPDF2 import PdfFileMerger, PdfFileReader

def decrypt_pdf_page(pdf_page):
    """
    :param pdf.PageObject pdf_page:
    """
    print(pdf_page)
    print(pdf_page['/Resources'])
    


# /Users/graffy/data/Perso/pymusco/tmp/Raffy\ et\ al.\ -\ 2016\ -\ School\ SVOC\ article\ SI.pdf 

with open('/Users/graffy/data/Perso/MeltingNotes_work.git/partitions/scans/169-huckleberry-finn.pdf', 'rb') as pdf_file:
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)
    decrypt_pdf_page(pdf_reader.getPage(267))
    decrypt_pdf_page(pdf_reader.getPage(268))
    decrypt_pdf_page(pdf_reader.getPage(269))

    # {
    #     '/Parent': IndirectObject(1980, 0),
    #     '/Contents': IndirectObject(2009, 0),
    #     '/Type': '/Page',
    #     '/Resources': IndirectObject(2011, 0),
    #     '/Rotate': 0,
    #     '/MediaBox': [0, 0, 595, 842]
    # }
