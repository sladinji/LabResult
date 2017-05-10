from flask.ext.admin.base import MenuLink
from flask.ext.login import current_user

class MenuLinkWithIcon(MenuLink):
        def __init__(self, name, url=None, endpoint=None, category=None,
                icon=None):
            self.icon = icon
            super().__init__(name, url, endpoint, category)

# This is used to display login our logout button
class AuthenticatedMenuLink(MenuLinkWithIcon):
    def is_accessible(self):
        return current_user.is_authenticated


class NotAuthenticatedMenuLink(MenuLinkWithIcon):
    def is_accessible(self):
        return not current_user.is_authenticated

