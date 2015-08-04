from txrestapi.resource import APIResource
from txrestapi.methods import GET, POST, PUT, DELETE, ALL


class OpenBazaarAPI(APIResource):
    """fdsafsdds"""

    @GET('^/users/(?P<userid>[a-zA-Z0-9]+)')
    def get_user(self, request, userid):
        """Interacting with users (vendors, buyers, moderators)"""
        return userid

    @GET('^/users/(?P<userid>[a-zA-Z0-9]+)/follow')
    def follow_user(self, request, userid):
        """Follow a user"""
        return userid

    @GET('^/users/(?P<userid>[a-zA-Z0-9]+)/unfollow')
    def unfollow_user(self, request, userid):
        """Stop following a user"""
        return userid

    @GET('^/users/(?P<userid>[a-zA-Z0-9]+)/reputation')
    def get_user_reputation(self, request, userid):
        """Retrieving reputation for a specific user on the network"""
        return userid

    @ALL('^/')
    def default(self, request):
        return "Your request did not match any API calls. %s" % request