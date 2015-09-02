__author__ = 'Brian Hoffman'

import binascii
import unittest

from market import profile
from keyutils.keys import KeyChain
from market.profile import objects
from db import datastore
import os


class ProfileTest(unittest.TestCase):
    def setUp(self):
        datastore.create_database("test.db")
        datastore.DATABASE = "test.db"

        self.test_guid = '0000000000000000000000000000000000'
        self.guid_privkey = binascii.unhexlify("76e0cfba9b4900abfdfbdfc08dd4ba5dd42234d3abbdaba953239466fa677eab")
        self.guid_pubkey = binascii.unhexlify(
            "7e8ac43a2873cc0de24692dad229a5d196b6d173258388e95a8e25c14112f9bace57458a609a9d069282d5de0ee36f0a"
            "885bff349283e977ccd67b1a9c8eba00be6bfb797453e42649ea14090b42d71a6cca1b6fbaa3d4a85095ed8c80e8a677")

        self.btc_privkey = "xprv9s21ZrQH143K3t2rGxe4LjSzTb7t7Fa2SzTKkts7bSTsoTZjv27X2GVvUafi7YQUPwkMucja" \
                           "Tpj3ktbsmVY2gfWqaNvXswZrMTwTJ3xfoot"
        self.btc_pubkey = "xpub661MyMwAqRbcGN7KNzB4hsPj1cxNWiHspDNvZHGj9mzrgFttTZRma4pQKtR5Fub82xWp" \
                          "QvQZzZ8JMazWFgvGAN3grGqGKEC7bTWMetR2VJn"

        self.test_profile_hex = '0a0954657374205573657210001a640a2066dd8742337bfc505e5ba86710682a4531842' \
                           '218ea47ebeccbcbe1713c35a94512401158c4bfc1dc6de0fda2cde7d43b8023b78782b7' \
                           'b8986336bff31b98cc7d7ae2b0829e5ddc59df80414dbafd5732716f0a93dc66157bf24' \
                           '27f950c2b5558b807'
        self.test_profile_hex_updated = '0a0954657374205573657210001a640a2066dd8742337bfc505e5ba86710682a4' \
                                        '531842218ea47ebeccbcbe1713c35a94512401158c4bfc1dc6de0fda2cde7d43b' \
                                        '8023b78782b7b8986336bff31b98cc7d7ae2b0829e5ddc59df80414dbafd57327' \
                                        '16f0a93dc66157bf2427f950c2b5558b8074a0c546573742050726f66696c65'

        self.test_pgp_pubkey = '-----BEGIN PGP PUBLIC KEY BLOCK-----' \
                               '\nComment: GPGTools - https://gpgtools.org\n\nmQINBFTLsw4BEADJWW2HknyMiOdx6F9' \
                               'TROxuuAmwMq27mb7OeHQMaoDMI9XlNnWp\nWDOTjHZshkES0xtOH63q+IaGxHNEm8Dr2oWui/homt' \
                               'sEnHG/omMEw7QVte9tpecy\nheMvQykOdsxzmF1IDuIMLriT9txDMi/pFqVwjB7z6bX2Z/llI7Szk' \
                               'fT6JQlMHXm9\noBfYRS7yQSrjYCaCkmJ4+iUuwjcIUpgVV+qoZvdAlSifhRXcodlKly/ogW143ORS' \
                               '\nQPJeUyHaa8DxQqAW96elekaGZleO3sf21i83oQv36eGwY3WOvrYcvdDC/suheuWM\nGmMXyoWfV' \
                               'ONQKcCcqdx8o43EDL4EPGw9Ru9Hl92DM6Q9OHhsHx8zcQdVqSjTopuc\n2Gm8CbTT+/iw2zFWhxj+' \
                               'XYimo3+ScNbcFEezSr7eR/9qnfW5i1lsxf6T+gkQSrvd\nNwyUGefKklbDIEoMvropimxlGm2Vi59' \
                               'OJ5iHcvbxvTeJct5b9017iHC2Gvf/bJKt\nr+Xy5+jnZRW61NxRGnmhFiV2SonVIiJVtdL3+s0swc' \
                               'Q8TWMpQI0jfPmpySE+9uvF\nwTHbnS+vI0gXlb1F3fbqGw6mAt5h9tMMqX91ku1oNJHJZNR+UM6Xu' \
                               'PgxcIudVRAk\n8kP5Bmac5LqhOwVLtojTFXjSWP7iS91akq4uMcT5jwb/zwSolCzVLznEkwARAQAB' \
                               '\ntEVBdXRvZ2VuZXJhdGVkIEtleSAoQXV0b2dlbmVyYXRlZCBieSBPcGVuIEJhemFh\ncikgPHBnc' \
                               'EBvcGVuYmF6YWFyLm9yZz6JAjcEEwEKACEFAlTLsw4CGy8FCwkIBwMF\nFQoJCAsFFgIDAQACHgEC' \
                               'F4AACgkQ3aIYUn9Ew1a92A//UnJPNMQcRcWZAzaNgOmV\nLZ+9G4ZXqo8PWtO5Cg/frv+AfikcbdQ' \
                               '3qlbjGZnYKIVJsM/YU9eoKF/uMM9vw6sC\n7yM3mF3Sm+oDZR2FyBy9gS0j/9I/wsXwa6Svgdvfhd' \
                               'P4uT1c2JQf6pKb/tilbUKf\nHXXb//uPWsd1yBszW1jO6bB0YUc2wF5EBtS/QPyaHdZq+YwFrAmYG' \
                               'ARSG5EbrPYm\nBmLJiZthwzlrqetjQktXD3RXTWZmgHG/AhzF1mi74dWC5X9N4Mf6/GCLxKBX9gga' \
                               '\npMJ0TMalYmZ8IEDN+gen33lkNurhHc2MMmg4BJzpWuhPwWWPACUXHaps5MqNECc6\nLZe18h3Ia' \
                               'MQdE0/0SJyRKKepJFGD6SRCklUPfheR2Z1uy7fmy69Kwps/ZTSBWeJ9\nksi7HN+SoaV70MedT9dm' \
                               'utN0uXizxHj5tWXSfgciPMhpEt0P7f9WU+UGmmcHXig5\nWfKX88CknsfTiqyftJKmC5HrtPnhAtn' \
                               'wkPNxTbAoXhruAQqLG/T7rZ6CrGzv7wKY\nyVcvAvoILIVbSYHUFaqx7ONr0k6mIInJGQAfzlBfDI' \
                               'jZJODzmx3UbdXcd70+0qiU\n4I+E6Oj3FDcdzncxD4p+bCyNAbdfBDx1s3o3cuFtlFoRNQDeZoH9s' \
                               'RLtL/YEck8b\nbL7Pru+XVhXnHRClRZRfqGE=\n=YRXA\n-----END PGP PUBLIC KEY BLOCK--' \
                               '---\n'
        self.test_pgp_sig = '-----BEGIN PGP SIGNED MESSAGE-----\nHash: SHA512\n\n0000000000000000000000000' \
                            '000000000\n-----BEGIN PGP SIGNATURE-----\nComment: GPGTools - https://gpgtool' \
                            's.org\n\niQIcBAEBCgAGBQJV50HjAAoJEN2iGFJ/RMNW/VMQALHz7JLSugqyVhjgET2iQfKt\nzR' \
                            'oQhSBVXbVqXicJUqd/FRe3DUVXh0IYynoEpa1TUuipkpkQWY+KIJ3n7IMoGF8K\njIhEjks/fa6vR' \
                            '205oA2QBlDpIcJgGP62rkaJP4LZntAzjkI+u6OITG/txMJTM7Qc\nEuiMoDgWdql/iZZXwZhpdbxZ' \
                            '1jfgZl1W9KUc07zLfkf75sfNkq9Oel9bFrfgDW/T\n6KduC0qDl8KYMlpr8Kl0tyms3IdsBueOA4g' \
                            'ynQOJwtIhpX4yc7pTyioQsV0S044/\npeRbijiyejEY7qnfkoImWvORdGu/WQIw7D3yJdQ+CYqF3X' \
                            'Ok6HbVn5yzVGr3A5Yn\nMMrkYI9sx8p/d8pcEMnwHf1n4iaq0IWP5G9/mviTI4vwxFs255M7P6DIW' \
                            'xhyUmKl\nbhs8ru6z4O4swsVzIhve7F/11+xLtqHctNu4Ru4yFXjApZhsaJYOy8aGTNWz9tae\nVJ' \
                            'ylHDZbbM/UEas3mRF8tdp9mGTZh7nKWX6EvbQsVYEgX9wSg0HaWzdcnihvCPka\nrnNxmjUEKUulv' \
                            'z9Wwvh9hukW17ZvgGCcPMXjs60GBGH3iMLCvHb2fppTytxdLCKH\nv84AixT+H/Jsn0gNTvTkjhwP' \
                            'SEulkHh1sZ5eEvCFYheQQxhHDuOyekPa7lv1fcr9\n1UdB9Scyx5xiW8c0+AIF\n=7Bko\n-----E' \
                            'ND PGP SIGNATURE-----\n'

        self.ks = datastore.KeyStore()
        self.ks.set_key('guid', self.guid_privkey, self.guid_pubkey)
        self.ks.set_key('bitcoin', self.btc_privkey, self.btc_pubkey)

        self.p = profile.Profile()
        self.p.profile.name = 'Test User'
        self.p.profile.location = 0

        u = objects.Profile()

        enc = u.PublicKey()
        enc.public_key = KeyChain().encryption_pubkey
        enc.signature = KeyChain().signing_key.sign(enc.public_key)[:64]
        u.encryption_key.MergeFrom(enc)
        self.p.update(u)

    def tearDown(self):
        os.remove("test.db")

    def test_getUpdateProfile(self):
        p = self.p.get(True)
        self.assertEqual(p.encode('hex'), self.test_profile_hex)

        u = objects.Profile()
        u.about = "Test Profile"
        self.p.update(u)

        p = self.p.get(True)
        self.assertEqual(p.encode('hex'), self.test_profile_hex_updated)

        self.p.add_social_account('FACEBOOK', 'OpenBazaarProject', 'https://www.facebook.com/OpenBazaarProject')
        p = self.p.get()
        self.assertEqual(p.social[0].type, 1)
        self.assertEqual(p.social[0].username, 'OpenBazaarProject')
        self.assertEqual(p.social[0].proof_url, 'https://www.facebook.com/OpenBazaarProject')

        self.p.remove_social_account('FACEBOOK')
        p = self.p.get()
        self.assertEqual(len(p.social), 0)

        r = self.p.add_pgp_key(
            self.test_pgp_pubkey,
            self.test_pgp_sig,
            self.test_guid)

        p = self.p.get()
        self.assertEqual(p.pgp_key.public_key, self.test_pgp_pubkey)
        self.assertEqual(p.pgp_key.signature, self.test_pgp_sig)
