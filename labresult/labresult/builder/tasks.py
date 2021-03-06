"""
Integrations taks
"""

from bson.objectid import ObjectId
import bson
import gridfs
from mongoengine.connection import get_db

import labresult
from labresult.builder import Builder
from labresult.model import Document



@labresult.celery.task()
def get_gridfs_data_from_id(id, coll='fs', db='default'):
    fs = gridfs.GridFS(get_db(db), coll)
    return  fs.get(bson.ObjectId(id)).read()

@labresult.celery.task()
def get_gridfs_data(doc_id):
    """
    :param doc_id: str, id of the document
    """
    #reload doc to avoid race condition
    doc = Document.objects.get(pk=doc_id)
    data = doc.data.read()
    return data

@labresult.celery.task()
def integrate(**kwargs):
    """
    Integrate or re-integrate a doc. If doc_id given, document will be load
    from db, otherwise a new one will be created and its attribute will be set
    with what'is in kwargs.
    :param doc_id: str, document id
    :param kwargs: document attributes (origin, numdos...)
    :rtype : :class:`labresult.model.Document`
    """
    if "doc_id" in kwargs:
        doc = Document.objects.get(pk=kwargs['doc_id'])
        doc.healthworkers = None
        doc.groups = None
        doc.log = None
        doc.traceback = None
        doc.pdf_nb_pages = 0
        for img in doc.imgs :
            img.delete()
        if doc.data :
            doc.pdf.delete()
    else :
        doc = Document(**kwargs)
        doc.save()
    Builder().build(doc)
    return doc.id

@labresult.celery.task()
def get_doc(**kwargs):
    """
    Return doc matching given parameter or raise exception
    :param kwargs: id, gridfs_id, numdos, doc_type
    :rtype: :class:`labresult.model.Document`
    """
    if kwargs.get('id',None):
        doc = Document.objects.get(id=kwargs['id'])
    elif kwargs.get('gridfs_id', None):
        doc = Document.objects.get(data=ObjectId(kwargs['gridfs_id']))
    else :
        same_keys = ['numdos', 'doc_type',]
        qry={ k : kwargs[k] for k in same_keys if kwargs.get(k ,False)}
        doc = Document.objects.get(**qry)
    return doc

