from txrestapi.resource import APIResource
from txrestapi.methods import GET, POST, ALL

DEFAULT_RECORDS_COUNT = 20
DEFAULT_RECORDS_OFFSET = 0


class OpenBazaarAPI(APIResource):
    """
    This RESTful API allows clients to pull relevant data from the
    OpenBazaar daemon for use in a GUI or other application.
    """

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

    @GET('^/users/(?P<userid>[a-zA-Z0-9]+)/listings')
    def get_user_reputation(self, request, userid):
        """Retrieving reputation for a specific user on the network"""
        return userid

    @GET('^/cases')
    def get_cases(self, request):
        """Retrieving moderator cases the current user is participating in."""
        return request.args

    @GET('^/cases/refund_buyer/(?P<caseid>[a-zA-Z0-9]+)')
    def refund_buyer(self, request, caseid):
        """Refund payment to a buyer for a specific case."""
        return caseid

    @GET('^/cases/pay_vendor/(?P<caseid>[a-zA-Z0-9]+)')
    def pay_vendor(self, request, caseid):
        """Release payment to vendor for a specific case."""
        return caseid

    @POST('^/cases/split_payment/(?P<caseid>[a-zA-Z0-9]+)')
    def split_payment(self, request, caseid):
        """Allows moderator to split escrow across both parties for a specific case."""
        args = request.args
        amount_to_buyer = args.get('amount_to_buyer')
        return caseid

    @GET('^/sales')
    def get_sales(self, request):
        """Retrieving orders that the current user is the vendor for."""
        args = request.args
        count = args.get('count', DEFAULT_RECORDS_COUNT)
        offset = args.get('offset', DEFAULT_RECORDS_OFFSET)
        filter = args.get('filter', '')

        return request

    @GET('^/sales/refund/(?P<orderid>[a-zA-Z0-9]+)')
    def sales_refund(self, request, orderid):
        """Allows vendor to refund the buyer and cancel the order."""
        return orderid

    @GET('^/sales/protest/(?P<orderid>[a-zA-Z0-9]+)')
    def sales_protest(self, request, orderid):
        """Allows vendor to protest the order to a moderator in event of a problem."""
        args = request.args
        message_to_mod = args.get('message_to_mod', '')
        return orderid

    @GET('^/purchases')
    def get_purchases(self, request):
        """Retrieving orders that the current user is the buyer for."""
        args = request.args
        count = args.get('count', DEFAULT_RECORDS_COUNT)
        offset = args.get('offset', DEFAULT_RECORDS_OFFSET)
        filter = args.get('filter', '')

        return request

    @GET('^/purchases/cancel/(?P<orderid>[a-zA-Z0-9]+)')
    def cancel_purchase(self, request, orderid):
        """Allows vendor to refund the buyer and cancel the order."""
        return orderid

    @GET('^/purchases/protest/(?P<orderid>[a-zA-Z0-9]+)')
    def purchase_protest(self, request, orderid):
        """Allows buyer to protest the order to a moderator in event of a problem."""
        args = request.args
        message_to_mod = args.get('message_to_mod', '')
        return orderid

    @GET('^/settings')
    def get_settings(self, request):
        """Retrieve an object containing all the settings for the current user."""
        args = request.args
        include_sensitive = args.get('include_sensitive', False)

        return request

    @GET('^/messages')
    def get_messages(self, request):
        """Retrieve messages from private inbox."""
        args = request.args
        count = args.get('count', DEFAULT_RECORDS_COUNT)
        offset = args.get('offset', DEFAULT_RECORDS_OFFSET)
        filter = args.get('filter', '')

        # Optional URL parameters
        from_user = args.get('from_user')
        to_user = args.get('to_user')
        show_cleared = args.get('show_cleared', False)

        return request

    @POST('^/messages/send')
    def send_message(self, request):
        """Send a new private message to another user."""
        args = request.args
        to_user = args.get('to_user')
        body = args.get('body', '')

        return request

    @GET('^/messages/clear/(?P<userid>[a-zA-Z0-9]+)')
    def clear_conversation(self, request, userid):
        """Mark all current visible messages with a user as hidden."""
        return userid

    @GET('^/search/(?P<query>[a-zA-Z0-9]+)')
    def search(self, request, query):
        """Search term to look for on the network."""
        args = request.args
        count = args.get('count', DEFAULT_RECORDS_COUNT)

        return query

    @GET('^/search/vendors/(?P<query>[a-zA-Z0-9]+)')
    def search_vendors(self, request, query):
        """Search for vendor users."""
        args = request.args
        count = args.get('count', DEFAULT_RECORDS_COUNT)

        return query

    @GET('^/search/moderators/(?P<query>[a-zA-Z0-9]+)')
    def search_moderators(self, request, query):
        """Search for moderator users."""
        args = request.args
        count = args.get('count', DEFAULT_RECORDS_COUNT)

        return query

    @GET('^/search/users/(?P<query>[a-zA-Z0-9]+)')
    def search_users(self, request, query):
        """Search for someone against all users."""
        args = request.args
        count = args.get('count', DEFAULT_RECORDS_COUNT)

        return query

    @GET('^/search/listings/(?P<query>[a-zA-Z0-9]+)')
    def search_listings(self, request, query):
        """Search for vendor users."""
        args = request.args
        count = args.get('count', DEFAULT_RECORDS_COUNT)

        return query

    @GET('^/my_listings')
    def get_my_listings(self, request):
        """Retrieve current user's listings."""
        args = request.args
        count = args.get('count', DEFAULT_RECORDS_COUNT)
        offset = args.get('offset', DEFAULT_RECORDS_OFFSET)
        filter = args.get('filter', '')

        return args

    @POST('^/create_listing')
    def get_my_listings(self, request):
        """Retrieve current user's listings."""
        args = request.args
        count = args.get('count', DEFAULT_RECORDS_COUNT)
        offset = args.get('offset', DEFAULT_RECORDS_OFFSET)
        filter = args.get('filter', '')

        return args

    @ALL('^/')
    def default(self, request):
        return "Your request did not match any API calls. %s" % request