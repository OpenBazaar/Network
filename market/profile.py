__author__ = 'chris'
import gnupg

from protos import objects
from db.datastore import Database


class Profile(object):
    """
    This is a class which handles creating an updating the user profile.
    Data added to a protobuf object and stored in the database. The database
    will update automatically when changes are made to the profile. When we
    need to send it to our peers, we can just call get().
    """

    def __init__(self):
        self.profile = objects.Profile()
        self.db = Database().ProfileStore()
        if self.db.get_proto() is not None:
            self.profile.ParseFromString(self.db.get_proto())

    def get(self, serialized=False):
        if serialized:
            return self.profile.SerializeToString()
        return self.profile

    def update(self, user_info):
        """
        To update the profile, create a new protobuf Profile object and add the
        field you want to update.

        Example:
            u = objects.Profile()
            u.about = "hello world"
            update(u)
        """
        self.profile.MergeFrom(user_info)
        self.db.set_proto(self.profile.SerializeToString())

    def add_social_account(self, account_type, username, proof=None):
        s = self.profile.SocialAccount()
        for social_account in self.profile.social:
            if social_account.type == s.SocialType.Value(account_type.upper()):
                self.profile.social.remove(social_account)
        s.type = s.SocialType.Value(account_type.upper())
        s.username = username
        if proof:
            s.proof_url = proof
        self.profile.social.extend([s])
        self.db.set_proto(self.profile.SerializeToString())

    def remove_social_account(self, account_type):
        s = self.profile.SocialAccount()
        for social_account in self.profile.social:
            if social_account.type == s.SocialType.Value(account_type.upper()):
                self.profile.social.remove(social_account)
        self.db.set_proto(self.profile.SerializeToString())

    def add_pgp_key(self, public_key, signature, guid):
        """
        Adds a pgp public key to the profile. The user must have submitted a
        valid signature covering the guid otherwise the key will not be added to
        the profile.
        """
        gpg = gnupg.GPG()
        gpg.import_keys(public_key)
        if gpg.verify(signature) and guid in signature:
            p = self.profile.PublicKey()
            p.public_key = public_key
            p.signature = signature
            self.profile.pgp_key.MergeFrom(p)
            self.db.set_proto(self.profile.SerializeToString())
            return True
        else:
            return False

    def remove_field(self, field):
        if field is not "name":
            self.profile.ClearField(field)
            self.db.set_proto(self.profile.SerializeToString())

    def get_temp_handle(self):
        return self.db.get_temp_handle()
