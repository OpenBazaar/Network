__author__ = 'chris'

import json
import bitcoin
from binascii import unhexlify, hexlify
from collections import OrderedDict

import re
import os
import nacl.encoding
from protos.objects import Listings
from protos.countries import CountryCode
from dht.utils import digest
from constants import DATA_FOLDER
from db.datastore import HashMap, ListingsStore, ModeratorStore
from market.profile import Profile
from keyutils.keys import KeyChain


class Contract(object):
    """
    A class for creating and interacting with OpenBazaar Ricardian contracts.
    """

    def __init__(self, contract=None, hash_value=None):
        """
        This class can be instantiated with either an `OrderedDict` or a hash
        of a contract. If a hash is used, we will load the contract from either
        the file system or cache.

        Alternatively, pass in no parameters if the intent is to create a new
        contract.

        :rtype : object
        Args:
            contract: an `OrderedDict` containing a filled out json contract
            hash: a hash (in raw bytes) of a contract
        """
        if contract is not None:
            self.contract = contract
        elif hash_value is not None:
            try:
                file_path = HashMap().get_file(hash_value)
                if file_path is None:
                    file_path = DATA_FOLDER + "cache/" + hexlify(hash_value)
                with open(file_path, 'r') as filename:
                    self.contract = json.load(filename, object_pairs_hook=OrderedDict)
            except Exception as e:
                print e
                self.contract = {}
        else:
            self.contract = {}

    def create(self,
               expiration_date,
               metadata_category,
               title,
               description,
               currency_code,
               price,
               process_time,
               nsfw,
               shipping_origin,
               shipping_regions,
               est_delivery_domestic=None,
               est_delivery_international=None,
               terms_conditions=None,
               returns=None,
               keywords=None,
               category=None,
               condition=None,
               sku=None,
               images=None,
               free_shipping=None,
               shipping_currency_code=None,
               shipping_domestic=None,
               shipping_international=None,
               options=None,
               moderators=None):
        """
        All parameters are strings except:

        :param expiration_date: `string` (must be formatted UTC datetime)
        :param keywords: `list`
        :param nsfw: `boolean`
        :param images: a `list` of image files
        :param free_shipping: `boolean`
        :param shipping_origin: a 'string' formatted `CountryCode`
        :param shipping_regions: a 'list' of 'string' formatted `CountryCode`s
        :param options: a 'dict' containing options as keys and 'list' as option values.
        :param moderators: a 'list' of 'string' guids (hex encoded).
        """

        # TODO: import keys into the contract, import moderator information from db, sign contract.
        profile = Profile().get()
        keychain = KeyChain()
        self.contract = OrderedDict(
            {
                "vendor_offer": {
                    "listing": {
                        "metadata": {
                            "version": "0.1",
                            "expiry": expiration_date + " UTC",
                            "category": metadata_category,
                            "category_sub": "fixed price"
                        },
                        "id": {
                            "guid": keychain.guid.encode("hex"),
                            "pubkeys": {
                                "guid": keychain.guid_signed_pubkey[64:].encode("hex"),
                                "bitcoin": bitcoin.bip32_deserialize(
                                    KeyChain().bitcoin_master_pubkey)[5].encode("hex")
                            }
                        },
                        "item": {
                            "title": title,
                            "description": description,
                            "process_time": process_time,
                            "price_per_unit": {},
                            "nsfw": nsfw
                        }
                    }
                }
            }
        )
        if metadata_category == "physical good" and condition is not None:
            self.contract["vendor_offer"]["listing"]["item"]["condition"] = condition
        if currency_code.upper() == "BTC":
            item = self.contract["vendor_offer"]["listing"]["item"]
            item["price_per_unit"]["bitcoin"] = price
        else:
            item = self.contract["vendor_offer"]["listing"]["item"]
            item["price_per_unit"]["fiat"] = {}
            item["price_per_unit"]["fiat"]["price"] = price
            item["price_per_unit"]["fiat"]["currency_code"] = currency_code
        if keywords is not None:
            self.contract["vendor_offer"]["listing"]["item"]["keywords"] = []
            self.contract["vendor_offer"]["listing"]["item"]["keywords"].extend(keywords)
        if category is not None:
            self.contract["vendor_offer"]["listing"]["item"]["category"] = category
        if sku is not None:
            self.contract["vendor_offer"]["listing"]["item"]["sku"] = sku
        if options is not None:
            self.contract["vendor_offer"]["listing"]["item"]["options"] = options
        if metadata_category == "physical good":
            self.contract["vendor_offer"]["listing"]["shipping"] = {}
            shipping = self.contract["vendor_offer"]["listing"]["shipping"]
            shipping["shipping_origin"] = shipping_origin
            if free_shipping is False:
                self.contract["vendor_offer"]["listing"]["shipping"]["free"] = False
                self.contract["vendor_offer"]["listing"]["shipping"]["flat_fee"] = {}
                if shipping_currency_code == "BTC":
                    self.contract["vendor_offer"]["listing"]["shipping"]["flat_fee"]["bitcoin"] = {}
                    self.contract["vendor_offer"]["listing"]["shipping"]["flat_fee"]["bitcoin"][
                        "domestic"] = shipping_domestic
                    self.contract["vendor_offer"]["listing"]["shipping"]["flat_fee"]["bitcoin"][
                        "international"] = shipping_international
                else:
                    shipping = self.contract["vendor_offer"]["listing"]["shipping"]
                    shipping["flat_fee"]["fiat"] = {}
                    shipping["flat_fee"]["fiat"]["price"] = {}
                    shipping["flat_fee"]["fiat"]["price"][
                        "domestic"] = shipping_domestic
                    shipping["flat_fee"]["fiat"]["price"][
                        "international"] = shipping_international
                    shipping["flat_fee"]["fiat"][
                        "currency_code"] = shipping_currency_code
            else:
                self.contract["vendor_offer"]["listing"]["shipping"]["free"] = True
            self.contract["vendor_offer"]["listing"]["shipping"]["shipping_regions"] = []
            for region in shipping_regions:
                shipping = self.contract["vendor_offer"]["listing"]["shipping"]
                shipping["shipping_regions"].append(region)
            listing = self.contract["vendor_offer"]["listing"]
            listing["shipping"]["est_delivery"] = {}
            listing["shipping"]["est_delivery"]["domestic"] = est_delivery_domestic
            listing["shipping"]["est_delivery"][
                "international"] = est_delivery_international
        if profile.HasField("handle"):
            self.contract["vendor_offer"]["listing"]["id"]["blockchain_id"] = profile.handle
        if images is not None:
            self.contract["vendor_offer"]["listing"]["item"]["image_hashes"] = []
            for image in images:
                hash_value = digest(image).encode("hex")
                self.contract["vendor_offer"]["listing"]["item"]["image_hashes"].append(hash_value)

                if not os.path.exists(DATA_FOLDER + "store/media/"):
                    os.makedirs(DATA_FOLDER + "store/media/")
                with open(DATA_FOLDER + "store/media/" + hash_value, 'w') as outfile:
                    outfile.write(image)

                HashMap().insert(digest(image), DATA_FOLDER + "store/media/" + hash_value)
        if terms_conditions is not None or returns is not None:
            self.contract["vendor_offer"]["listing"]["policy"] = {}
            if terms_conditions is not None:
                self.contract["vendor_offer"]["listing"]["policy"]["terms_conditions"] = terms_conditions
            if returns is not None:
                self.contract["vendor_offer"]["listing"]["policy"]["returns"] = returns
        if moderators is not None:
            self.contract["vendor_offer"]["listing"]["moderators"] = []
            for mod in moderators:
                mod_info = ModeratorStore().get_moderator(unhexlify(mod))
                print mod_info
                if mod_info is not None:
                    moderator = {
                        "guid": mod,
                        "blockchain_id": mod_info[6],
                        "pubkeys": {
                            "signing": {
                                "key": mod_info[1][64:].encode("hex"),
                                "signature": mod_info[1][:64].encode("hex")
                            },
                            "encryption": {
                                "key": mod_info[2].encode("hex"),
                                "signature": mod_info[3].encode("hex")
                            },
                            "bitcoin": {
                                "key": mod_info[4].encode("hex"),
                                "signature": mod_info[5].encode("hex")
                            }
                        }
                    }
                    self.contract["vendor_offer"]["listing"]["moderators"].append(moderator)

        listing = json.dumps(self.contract["vendor_offer"]["listing"], indent=4)
        self.contract["vendor_offer"]["signature"] = \
            keychain.signing_key.sign(listing, encoder=nacl.encoding.HexEncoder)[:128]
        self.save()

    def update(self,
               expiration_date=None,
               metadata_category=None,
               title=None,
               description=None,
               currency_code=None,
               price=None,
               process_time=None,
               nsfw=None,
               est_delivery_domestic=None,
               est_delivery_international=None,
               shipping_origin=None,
               shipping_regions=None,
               keywords=None,
               category=None,
               condition=None,
               sku=None,
               image_hashes=None,  # if intending to delete an image, pass in
                                   # the hashes that are staying.
               images=None,  # to add new images pass in a list of image files.
               free_shipping=None,
               shipping_currency_code=None,
               shipping_domestic=None,
               shipping_international=None):

        self.delete(False)
        vendor_listing = self.contract["vendor_offer"]["listing"]
        if expiration_date is not None:
            vendor_listing["item"]["expiry"] = expiration_date
        if metadata_category is not None:
            vendor_listing["metadata"]["category"] = metadata_category
        if metadata_category != "physical good" and vendor_listing["metadata"][
                "category"] == "physical good":
            del vendor_listing["shipping"]
        elif metadata_category == "physical good" and vendor_listing["metadata"][
                "category"] != "physical good":
            vendor_listing["shipping"] = {}
            vendor_listing["shipping"]["est_delivery"] = {}
            vendor_listing["shipping"]["free"] = False
        if title is not None:
            vendor_listing["item"]["title"] = title
        if description is not None:
            vendor_listing["item"]["description"] = description
        if currency_code is not None:
            if currency_code.upper() != "BTC" and "bitcoin" \
                    in vendor_listing["item"]["price_per_unit"]:
                p = vendor_listing["item"]["price_per_unit"]["bitcoin"]
                del vendor_listing["item"]["price_per_unit"]["bitcoin"]
                vendor_listing["item"]["price_per_unit"]["fiat"] = {}
                vendor_listing["item"]["price_per_unit"]["fiat"][
                    "currency_code"] = currency_code
                vendor_listing["item"]["price_per_unit"]["fiat"]["price"] = p
            elif currency_code.upper() == "BTC" and "fiat" in \
                    vendor_listing["item"]["price_per_unit"]:
                p = vendor_listing["item"]["price_per_unit"]["fiat"]["price"]
                del vendor_listing["item"]["price_per_unit"]["fiat"]
                vendor_listing["item"]["price_per_unit"]["bitcoin"] = p
        if price is not None:
            if "bitcoin" in vendor_listing["item"]["price_per_unit"]:
                vendor_listing["item"]["price_per_unit"]["bitcoin"] = price
            else:
                vendor_listing["item"]["price_per_unit"]["fiat"]["price"] = price
        if process_time is not None:
            vendor_listing["item"]["process_time"] = process_time
        if nsfw is not None:
            vendor_listing["item"]["nsfw"] = nsfw
        if keywords is not None:
            vendor_listing["item"]["keywords"] = []
            vendor_listing["item"]["keywords"].extend(keywords)
        if category is not None:
            vendor_listing["item"]["category"] = category
        if image_hashes is not None:
            to_delete = list(set(vendor_listing["item"]["image_hashes"]) - set(image_hashes))
            for image_hash in to_delete:
                # delete from disk
                h = HashMap()
                image_path = h.get_file(unhexlify(image_hash))
                if os.path.exists(image_path):
                    os.remove(image_path)
                # remove pointer to the image from the HashMap
                h.delete(unhexlify(image_hash))
            vendor_listing["item"]["image_hashes"] = []
            vendor_listing["item"]["image_hashes"].extend(image_hashes)
        if images is not None:
            if "image_hashes" not in vendor_listing["item"]:
                vendor_listing["item"]["image_hashes"] = []
            for image in images:
                hash_value = digest(image).encode("hex")
                vendor_listing["item"]["image_hashes"].append(hash_value)
                with open(DATA_FOLDER + "store/media/" + hash_value, 'w') as outfile:
                    outfile.write(image)
                HashMap().insert(digest(image), DATA_FOLDER + "store/media/" + hash_value)
        if vendor_listing["metadata"]["category"] == "physical good" and condition is not None:
            vendor_listing["item"]["condition"] = condition
        if sku is not None:
            vendor_listing["item"]["sku"] = sku
        if vendor_listing["metadata"]["category"] == "physical good":
            if shipping_origin is not None:
                vendor_listing["shipping"]["shipping_origin"] = shipping_origin
            if free_shipping is not None:
                if free_shipping is True and vendor_listing["shipping"]["free"] is False:
                    vendor_listing["shipping"]["free"] = True
                    del vendor_listing["shipping"]["flat_fee"]
                elif free_shipping is False and vendor_listing["shipping"]["free"] is True:
                    vendor_listing["shipping"]["flat_fee"] = {}
                    vendor_listing["shipping"]["flat_fee"]["bitcoin"] = {}
                    vendor_listing["shipping"]["free"] = False
            if shipping_currency_code is not None and vendor_listing["shipping"]["free"] is False:
                if shipping_currency_code == "BTC" and "bitcoin" not in \
                        vendor_listing["shipping"]["flat_fee"]:
                    vendor_listing["shipping"]["flat_fee"]["bitcoin"] = {}
                    d = vendor_listing["shipping"]["flat_fee"]["fiat"]["price"]["domestic"]
                    i = vendor_listing["shipping"]["flat_fee"]["fiat"]["price"][
                        "international"]
                    vendor_listing["shipping"]["flat_fee"]["bitcoin"]["domestic"] = d
                    vendor_listing["shipping"]["flat_fee"]["bitcoin"]["international"] = i
                    del vendor_listing["shipping"]["flat_fee"]["fiat"]
                elif shipping_currency_code != "BTC" and "bitcoin" in \
                        vendor_listing["shipping"]["flat_fee"]:
                    d = vendor_listing["shipping"]["flat_fee"]["bitcoin"]["domestic"]
                    i = vendor_listing["shipping"]["flat_fee"]["bitcoin"]["international"]
                    vendor_listing["shipping"]["flat_fee"]["fiat"] = {}
                    vendor_listing["shipping"]["flat_fee"]["fiat"]["price"] = {}
                    vendor_listing["shipping"]["flat_fee"]["fiat"]["price"]["domestic"] = d
                    vendor_listing["shipping"]["flat_fee"]["fiat"]["price"][
                        "international"] = i
                    vendor_listing["shipping"]["flat_fee"]["fiat"][
                        "currency_code"] = shipping_currency_code
                    del vendor_listing["shipping"]["flat_fee"]["bitcoin"]
            if shipping_domestic is not None and "bitcoin" not in \
                    vendor_listing["shipping"]["flat_fee"]:
                vendor_listing["shipping"]["flat_fee"]["fiat"]["price"][
                    "domestic"] = shipping_domestic
            if shipping_international is not None and "bitcoin" not in \
                    vendor_listing["shipping"]["flat_fee"]:
                vendor_listing["shipping"]["flat_fee"]["fiat"]["price"][
                    "international"] = shipping_international
            if shipping_domestic is not None and "bitcoin" in \
                    vendor_listing["shipping"]["flat_fee"]:
                vendor_listing["shipping"]["flat_fee"]["bitcoin"][
                    "domestic"] = shipping_domestic
            if shipping_international is not None and "bitcoin" in \
                    vendor_listing["shipping"]["flat_fee"]:
                vendor_listing["shipping"]["flat_fee"]["bitcoin"][
                    "international"] = shipping_international
            if shipping_regions is not None:
                vendor_listing["shipping"]["shipping_regions"] = shipping_regions
            if est_delivery_domestic is not None:
                vendor_listing["shipping"]["est_delivery"]["domestic"] = est_delivery_domestic
            if est_delivery_international is not None:
                vendor_listing["shipping"]["est_delivery"][
                    "international"] = est_delivery_international

        self.save()

    def get_contract_id(self):
        contract = json.dumps(self.contract, indent=4)
        return digest(contract)

    def delete(self, delete_images=True):
        """
        Deletes the contract json from the OpenBazaar directory as well as the listing
        metadata from the db and all the related images in the file system.
        """
        # build the file_name from the contract
        file_name = str(self.contract["vendor_offer"]["listing"]["item"]["title"][:100])
        file_name = re.sub(r"[^\w\s]", '', file_name)
        file_name = re.sub(r"\s+", '_', file_name)
        file_path = DATA_FOLDER + "store/listings/contracts/" + file_name + ".json"

        h = HashMap()

        # maybe delete the images from disk
        if "image_hashes" in self.contract["vendor_offer"]["listing"]["item"] and delete_images:
            for image_hash in self.contract["vendor_offer"]["listing"]["item"]["image_hashes"]:
                # delete from disk
                image_path = h.get_file(unhexlify(image_hash))
                if os.path.exists(image_path):
                    os.remove(image_path)
                # remove pointer to the image from the HashMap
                h.delete(unhexlify(image_hash))

        # delete the contract from disk
        if os.path.exists(file_path):
            os.remove(file_path)
        # delete the listing metadata from the db
        contract_hash = digest(json.dumps(self.contract, indent=4))
        ListingsStore().delete_listing(contract_hash)
        # remove the pointer to the contract from the HashMap
        h.delete(contract_hash)

    @staticmethod
    def save_contract_to_file(file_path, data):
        try:
            file_dir = os.path.dirname(file_path)
            # Race condition possible, but unlikely
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)

            with open(file_path, 'w') as outfile:
                outfile.write(json.dumps(data, indent=4))
        except IOError as e:
            print 'Cannot save file: ', e

    @staticmethod
    def generate_file_path(contract_title):
        # get the contract title to use as the file name and format it
        file_name = str(contract_title)
        file_name = re.sub(r"[^\w\s]", '', file_name)
        file_name = re.sub(r"\s+", '_', file_name)

        return DATA_FOLDER + "store/listings/contracts/" + file_name + ".json"

    @staticmethod
    def generate_media_file_path(media_title):
        # get the contract title to use as the file name and format it
        file_name = str(media_title)
        file_name = re.sub(r"[^\w\s]", '', file_name)
        file_name = re.sub(r"\s+", '_', file_name)

        return DATA_FOLDER + "store/media/" + file_name

    def save(self):
        """
        Saves the json contract into the OpenBazaar/store/listings/contracts/ directory.
        It uses the title as the file name so it's easy on human eyes. A mapping of the
        hash of the contract and file path is stored in the database so we can retrieve
        the contract with only its hash.

        Additionally, the contract metadata (sent in response to the GET_LISTINGS query)
        is saved in the db for fast access.
        """
        file_path = self.generate_file_path(self.contract["vendor_offer"]["listing"]["item"]["title"][:100])

        self.save_contract_to_file(file_path, self.contract)

        # Create a `ListingMetadata` protobuf object using data from the full contract
        listings = Listings()
        data = listings.ListingMetadata()
        data.contract_hash = digest(json.dumps(self.contract, indent=4))
        vendor_item = self.contract["vendor_offer"]["listing"]["item"]

        data.title = vendor_item["title"]
        if "image_hashes" in vendor_item:
            data.thumbnail_hash = unhexlify(vendor_item["image_hashes"][0])

        if 'category' in vendor_item:
            data.category = vendor_item["category"]
        if "bitcoin" not in vendor_item["price_per_unit"]:
            data.price = float(vendor_item["price_per_unit"]["fiat"]["price"])
            data.currency_code = vendor_item["price_per_unit"]["fiat"][
                "currency_code"]
        else:
            data.price = float(vendor_item["price_per_unit"]["bitcoin"])
            data.currency_code = "BTC"
        data.nsfw = vendor_item["nsfw"]
        if "shipping" not in self.contract["vendor_offer"]["listing"]:
            data.origin = CountryCode.Value("NA")
        else:
            country_code = self.contract["vendor_offer"]["listing"]["shipping"]["shipping_origin"].upper()
            if country_code:
                data.origin = CountryCode.Value(country_code)
            else:
                data.origin = CountryCode.Value("NA")
            for region in self.contract["vendor_offer"]["listing"]["shipping"]["shipping_regions"]:
                data.ships_to.append(CountryCode.Value(region.upper()))

        # save the mapping of the contract file path and contract hash in the database
        HashMap().insert(data.contract_hash, file_path)

        # save the `ListingMetadata` protobuf to the database as well
        ListingsStore().add_listing(data)
