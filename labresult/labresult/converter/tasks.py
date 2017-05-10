"""
Conversion tasks
"""
import io
from PyPDF2 import PdfFileReader

import labresult
from labresult.model import Document
from labresult.lib.model import get_existing_img_or_new_one, dblog
from labresult.converter import pcl
from labresult.converter import pdf
from celery.result import AsyncResult

@labresult.celery.task()
def pcl2pdf(data):
    return pcl.topdf(data)

@labresult.celery.task()
def error_handler(uuid, doc_id):
    result = AsyncResult(uuid)
    exc = result.get(propagate=False)
    doc = Document.objects.get(id=doc_id)
    dblog(doc, str(exc))

@labresult.celery.task()
def pdf2img(pdf_data, page_num, thumbnail, format_):
    img_data = pdf.toimg(pdf_data, page_num, thumbnail, format_)
    return img_data

@labresult.celery.task()
def get_pdf_num_pages(pdf_data):
        pdf_nb_pages = PdfFileReader(io.BytesIO(pdf_data)).getNumPages()
        return pdf_data, pdf_nb_pages

@labresult.celery.task(ignore_result=True)
def save_img(img_data, doc_id, page_num, thumbnail, format_):
    """
    Save img_data
    :param img_data: data to save
    :param doc_id: document.id
    :param page_num: page number of document
    :param thumbnail: boolean
    """
    doc = Document.objects.get(id=doc_id)
    imgobj = get_existing_img_or_new_one(doc, page_num, thumbnail, format_)
    if thumbnail :
        imgobj.thumbnail = img_data
    else:
        imgobj.data = img_data
    imgobj.save()
    doc.imgs.append(imgobj)
    doc.save()

@labresult.celery.task()
def merge(page1, page2, above):
    """
    merge pdf page (from pyPdf getPage)
    """
    if above :
        page1.mergePage(page2)
        return page1
    else :
        page2.mergePage(page1)
        return page2
