__author__ = 'Brian Hoffman'

import binascii
import unittest

from market import contracts
from db import datastore
import os


class ContractTest(unittest.TestCase):
    def setUp(self):
        datastore.create_database("test.db")
        datastore.DATABASE = "test.db"
        self.ps = datastore.ProfileStore()

        self.test_contract_filename = '00000000000000000000.json'
        self.guid_privkey = binascii.unhexlify("76e0cfba9b4900abfdfbdfc08dd4ba5dd42234d3abbdaba953239466fa677eab")
        self.guid_pubkey = binascii.unhexlify(
            "7e8ac43a2873cc0de24692dad229a5d196b6d173258388e95a8e25c14112f9bace57458a609a9d069282d5de0ee36f0a"
            "885bff349283e977ccd67b1a9c8eba00be6bfb797453e42649ea14090b42d71a6cca1b6fbaa3d4a85095ed8c80e8a677")

        self.btc_privkey = "xprv9s21ZrQH143K3t2rGxe4LjSzTb7t7Fa2SzTKkts7bSTsoTZjv27X2GVvUafi7YQUPwkMucja" \
                           "Tpj3ktbsmVY2gfWqaNvXswZrMTwTJ3xfoot"
        self.btc_pubkey = "xpub661MyMwAqRbcGN7KNzB4hsPj1cxNWiHspDNvZHGj9mzrgFttTZRma4pQKtR5Fub82xWp" \
                          "QvQZzZ8JMazWFgvGAN3grGqGKEC7bTWMetR2VJn"

        self.test_image = 'ff'
        self.ks = datastore.KeyStore()
        self.ks.set_key('guid', self.guid_privkey, self.guid_pubkey)
        self.ks.set_key('bitcoin', self.btc_privkey, self.btc_pubkey)

    def tearDown(self):
        os.remove("test.db")

    def test_create_contract(self):
        self.file_path = contracts.Contract.generate_file_path('00000000000000000000')

        if os.path.isfile(self.file_path):
            os.remove(self.file_path)
        self.assertFalse(os.path.isfile(self.file_path))

        c = contracts.Contract()
        c.create(
            expiration_date='1994-11-05T13:15:30Z',
            metadata_category='physical good',
            title='00000000000000000000',
            description='This is a test contract.',
            currency_code='BTC',
            price='100.00',
            process_time='1994-11-05T13:15:30Z',
            nsfw=False,
            shipping_origin='ALL',
            shipping_regions=[],
            condition='Used',
            keywords=['test'],
            free_shipping=False,
            shipping_currency_code='BTC',
            images=[self.test_image])

        self.assertTrue(os.path.isfile(self.file_path))

        cid = c.get_contract_id().encode('hex')
        self.assertEqual(cid, 'ffbb1d1d341c8297be4e5c8671b5927e26a65465')

        c.delete(True)
        self.assertFalse(os.path.isfile(self.file_path))

        img_path = contracts.Contract.generate_media_file_path('5ba31e0f523ab6bdc58a013e210d8317ab6ad8d9')
        self.assertFalse(os.path.isfile(img_path))
