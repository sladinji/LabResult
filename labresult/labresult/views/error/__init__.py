from flask.ext.admin import expose
from flask.ext.admin import BaseView


class ErrorView(BaseView):

    @expose('/', methods=('GET'))
    def index(self):
        return self.render("error.html")

