__author__ = 'Brian Hoffman'

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

    def tearDown(self):
        os.remove("test.db")

    def test_create_contract(self):

        file_path = contracts.Contract.generate_file_path('00000000000000000000')

        if os.path.isfile(file_path):
            os.remove(file_path)
        self.assertFalse(os.path.isfile(file_path))

        c = contracts.Contract()
        c.create(
            expiration_date='1994-11-05T13:15:30Z',
            metadata_category='physical good',
            title='00000000000000000000',
            description='This is a test contract.',
            currency_code='USD',
            price='100.00',
            process_time='1994-11-05T13:15:30Z',
            nsfw=False,
            shipping_origin='ALL',
            shipping_regions=[])

        self.assertTrue(os.path.isfile(file_path))
