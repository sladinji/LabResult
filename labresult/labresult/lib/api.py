from functools import wraps

from flask.ext import restful
from flask.ext.restful import reqparse

from labresult.lib.auth import RestrictedArea
from labresult.lib.auth import InvalidRequestException
from labresult.lib.auth import auth_exception_manager
from labresult.lib.model import get_option

def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not getattr(func, 'authenticated', True):
            return func(*args, **kwargs)

        acct = func.__self__.user_is_authorized()

        if acct:
            return func(*args, **kwargs)

        restful.abort(401)
    return wrapper


class PrivateResource(restful.Resource, RestrictedArea):
    method_decorators = [authenticate]
    model = None
    """Class from labresult.model to expose."""

    def _get_limit_per_page(self):
        return get_option("api.%s.max_ids" % self.model._class_name.lower(), 25)

class FilterableListResource(PrivateResource):
    allowed_users = ["User.Administrator"]
    parser = reqparse.RequestParser()
    parser.add_argument("page_num", type=int, default=1)
    parser.add_argument("filter", type=str)
    parser.add_argument("patient_id", type=str)
    def_args = { arg.name: None for arg in parser.args }
    model = None

    def _get_qry(self, args=def_args):
        raise Exception("Not Implemented")

    @auth_exception_manager
    def get(self):
        args = self.parser.parse_args()
        qry = self._get_qry(args)
        page_num = args.get('page_num', 1)
        docs_per_page =  self._get_limit_per_page()
        total = len(qry)
        if page_num > (total / docs_per_page) :
            page_num = int(total / docs_per_page) + 1
        offset = docs_per_page * (page_num - 1)
        ids = [ str(doc.id) for doc in
                qry.only('id').skip(offset).limit(docs_per_page)
              ]
        return {'success': True, 'items_ids' : ids,
            'nb_items': total, 'nb_pages': divmod(total, docs_per_page)[0] + 1,
            'current_page': page_num,
            }

class StandardPermissionsCheck(PrivateResource):
    """
    Base class for standard get put post method with permission check.
    """
    parser = reqparse.RequestParser()
    """RequestParser must be overriden in sub class to add agruments."""
    parser.add_argument('ids', type=str, action='append')
    parser.add_argument('id', type=str)

    def _pack_item(self, id):
        raise Exception("Not implemented")

    def _pack_items(self, ids):
        """
        Do a response with many items.
        """
        if len(ids) > self._get_limit_per_page():
            raise InvalidRequestException("too much items"
            " requested (%s max %s)" % (len(ids), max)
                )

        return [self._pack_item(id) for id in ids]

    @auth_exception_manager
    def get(self):
        """
        Return items matching ids.
        """
        args = self.parser.parse_args()
        ids = args['ids']
        ret = dict(success=True)
        if ids :
            ret.update(items=self._pack_items(ids))
        else:
            ret = { 'success' : False, 'error': 'No item id requested'}
        return ret


    @auth_exception_manager
    def put(self):
        """
        Update item matching id.
        """
        args = self.parser.parse_args()
        item = self.model.objects.get(id=args['id'])
        self.check_permission(item)
        for k in args:
            if args[k]:
                setattr(item, k, args[k])
        item.save()
        ret = dict(success=True)
        return ret

    def check_permission(self, item):
        raise Exception("Must be implemented in subclass")

