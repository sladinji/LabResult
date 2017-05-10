"""
Utilities to work with DB model.
"""
import sys
import ast
import cgitb
from functools import lru_cache


import mongoengine
import labresult
from labresult.model import Option, IntOption, StringOption, ListOption, FileOption
from labresult.model import Document, Img

class DbDictException(Exception):
    pass

class DbDict(object):
    """
    Wrapper class to work with model object before merging it in DB.
    """
    role = None
    """Can be doctor, corres... used by healthworker"""

    def __init__(self, model_class, role=None):
        object.__setattr__(self, 'datastore', {})
        object.__setattr__(self, 'model_class', model_class)
        object.__setattr__(self, 'role', role)

    def __getattr__(self, key):
        try :
            return self.datastore[key]
        except KeyError as e:
            if hasattr(self.model_class, key) :
                return None
            else :
                raise e

    def __setattr__(self, key, value):
        if hasattr(self.model_class, key) :
            self.datastore[key] = value
        else :
            raise DbDictException("%s has no attribute %s" % (self.model_class,
                key))


    def merge(self):
        """
        Merge object in db and return model object.
        Object must have an external_id or Exception is raised.
        """
        if not self.external_id :
            raise DbDictException("No external id available for merge")
        #prepare args for upsert
        kwargs = { "set__" + k : v for k, v in self.datastore.items()}
        #perform upsert
        self.model_class.objects(
                external_id = self.external_id).update_one(
                    upsert = True,
                    **kwargs
                    )
        # get object from db
        obj = self.model_class.objects.get(external_id =
                self.external_id )
        return obj

@lru_cache(maxsize=1024)
def get_option(key, default=None, description=None, visible=True):
    """
    Retrieve option matching key or raise exception if not found. Function
    results are stored in a cache. Cache is cleard each time an option is set
    using set_option.
    """
    try :
        value = Option.objects(key=key).get().value
        if isinstance(value, mongoengine.fields.GridFSProxy):
            return value.read()
        else:
            return value
    except Exception:
        labresult.app.logger.warn("Add %s option in DB" % key)
        set_option(key, default, description, visible)
        return default

def set_option(key, value, description=None, visible=True):
    """
    Set option in DB according to value type. Type can be int, str, or list.
    Clear option cache and restart celery workers to clean their caches.
    :param key: str, option key (ie name)
    :param value: str or int or list, option value
    """
    mapping = {
      int : IntOption,
      str : StringOption,
      list : ListOption,
      bytes : FileOption,
    }

    # try to convert value to str or int
    try :
        value = int(value)
    except :
        try :
            new_value = ast.literal_eval(value)
            if type(new_value) == list :
                value = new_value
        except :
            pass
    if type(value) is bytes \
    or type(value) is mongoengine.fields.GridFSProxy:
        opt = FileOption.objects(key=key).first()
        if not opt:
            opt = FileOption()
        opt.value = value
        opt.key = key
        opt.save()
    else:
        mapping[type(value)].objects(key=key).update_one(
            upsert=True, set__value = value,
            set__description = description,
            set__visible = visible,
            )
    get_option.cache_clear()
    #restart workers
    try :
        labresult.celery.control.broadcast('pool_restart')
    except :
        labresult.app.logger.warn('Celery restart failed')


def dblog(doc, exception, traceback=None):
    """
    Save exception to doc.log
    :param doc: :class:`labresult.model.Document`
    :param exception: exception
    """
    if not traceback:
        try :
            traceback = cgitb.html(sys.exc_info())
        except :
            pass
    Document.objects(id=str(doc.id)).update_one(
        set__traceback = traceback,
        set__status=Document.ERROR,
        set__log=str(exception)
    )

def get_readable_name(doc):
    """
    Return as nice as possible according to doc.
    :param doc: :class:`labresult.model.Document`
    """
    pname = doc.patient.user.name if doc.patient else ""
    numdos = doc.numdos if doc.numdos else ""
    doc_type = doc.doc_type if doc.doc_type else ""

    if not pname and not numdos and not doc_type :
        return str(doc.id)

    name = "{pname}_{doc_type}_{numdos}".format(numdos=numdos,pname=pname,
            doc_type = doc_type)
    name = name.replace(" ", "_")
    return name

def get_existing_img_or_new_one(doc, page_num, thumbnail, format_):
    """
    Return PNG if doc has it or a new instance
    :param doc: :class:`labresult.model.Document`
    :param page_num: int, desired page number
    :param thumbnail: bool, thumbnail or not
    :param format_: str, "png" or "svg"
    :rtype: :class:`labresult.model.Img`
    """
    wegotit = [ img for img in doc.imgs if hasattr(img, 'page_num') and
            img.page_num == page_num and img.format_ == format_ ]
    if wegotit:
        return wegotit[0]
    return Img(page_num = page_num, format_ = format_)

