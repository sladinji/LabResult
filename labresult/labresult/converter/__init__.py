"""
Module with smart functions finding how to convert a given document in the
required format.
"""
import io
import traceback

import PyPDF2
from PyPDF2.pdf import PdfFileReader, PdfFileWriter

import labresult
from labresult.converter import tasks
from labresult.lib.model import get_existing_img_or_new_one


def get_pdf(doc):
    """
    TODO make this function works with all kind of doc.
    convert pcl to pdf for now
    """
    pdf_data = None
    if hasattr(doc.pdf, '_id'):
        pdf_data = doc.pdf.read()
        if not doc.pdf_nb_pages :
            result = tasks.get_pdf_num_pages.delay(pdf_data)
            _, doc.pdf_nb_pages = result.get()
            doc.save()
    else :
        errback = tasks.error_handler.s(doc.id)
        chain = ( tasks.pcl2pdf.s(doc.data.read()).set(link_error = errback) |
                tasks.get_pdf_num_pages.s().set(link_error = errback)
                ).apply_async()
        pdf_data, doc.pdf_nb_pages = chain.get()
        if doc.underlay :
            pdf_data = merge_pdfs(pdf_data, doc.pdf_nb_pages,
                    doc.underlay.recto.read(),
                    doc.underlay.verso.read(), above=False, allPage =
                    doc.underlay.all_pages)

        doc.pdf = pdf_data
        doc.save()
    return pdf_data


def get_img(doc, page_num, thumbnail, format_):
    """
    Convert doc to img if not already done. Given doc is updated with new img
    if created.
    :param doc: :class:`labresult.model.Document`
    :param page_num: int, desired page number
    :param thumbnail: bool, thumbnail or not
    :param format_: str, "svg" pr "png"
    :rtype: bytes, img data
    """
    imgobj = get_existing_img_or_new_one(doc, page_num, thumbnail, format_)
    img_data= None
    if thumbnail and hasattr(imgobj.thumbnail,'_id'):
        img_data = imgobj.thumbnail.read()
    elif not thumbnail and hasattr(imgobj.data,'_id'):
        img_data = imgobj.data.read()
    if not img_data :
        if not hasattr(doc.pdf, '_id'):
            doc.pdf = get_pdf(doc)
        doc.pdf.seek(0)
        pdf_data = doc.pdf.read()
        img_data = tasks.pdf2img.delay(pdf_data, page_num, thumbnail, format_).get()
        tasks.save_img(img_data, doc.id, page_num, thumbnail, format_)

    return img_data

class MergePDFException(Exception):
    pass

def _merge_verso( verso, page_origin, above, pages):
    if verso:
        page_verso = PdfFileReader(io.BytesIO(verso)).getPage(0)
        pages.append(tasks.merge.delay(page_origin, page_verso,
            above))
    else:
        pages.append(page_origin)

def merge_pdfs(origin, num_pages, aux, verso=None, above=False, allPage=False):
    """
    this is a general purpose merging function, it helps in various plugins in order to
    not redo the wheel. It merges origin as the back, aux above.
    """
    try:
        output = PdfFileWriter()
        input_result = PdfFileReader(io.BytesIO(origin))
        pages = []

        for i in range(0, num_pages):
            page_origin = input_result.getPage(i)

            if allPage or i % 2 == 0:
                page_aux = PdfFileReader(io.BytesIO(aux)).getPage(0)
                pages.append(tasks.merge.delay(page_origin, page_aux, above))
            else:
                _merge_verso(verso, page_origin, above, pages)

        for page in pages :
            if type(page) == PyPDF2.pdf.PageObject:
                output.addPage(page)
            else :
                #request celery result
                data = page.get()
                output.addPage(data)

        out_io = io.BytesIO()
        output.write(out_io)
        out_io.seek(0, 0)
        return out_io.read()

    except Exception:
        labresult.app.logger.error(traceback.format_exc())
        raise MergePDFException('Error while merging PDFs')

