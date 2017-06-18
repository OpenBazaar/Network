"""Test for db/backuptool"""
from constants import DATA_FOLDER
import os
import unittest

import db.backuptool as bt

TEST_FOLDER = 'test'
TEST_TAR = 'test.tar.gz'
TEST_FILE_1 = 'test.txt'
TEST_FILE_2 = TEST_FOLDER + os.sep + 'test2.txt'

class BackuptoolTest(unittest.TestCase):
    """Test class for backuptool functions"""
    def setUp(self):
        os.chdir(DATA_FOLDER)
        # Create test folder
        if not os.path.exists(TEST_FOLDER):
            os.makedirs(TEST_FOLDER)
        # Create test files "test.txt", "test/test2.txt"
        fil = open(TEST_FILE_1, 'w')
        fil.close()
        fil = open(TEST_FILE_2, 'w')
        fil.close()
        # Backup to "test.tar.gz"
        if os.path.exists(bt.BACKUP_FOLDER + os.sep + TEST_TAR):
            os.remove(bt.BACKUP_FOLDER + os.sep + TEST_TAR)
        bt.backupfiles(TEST_TAR)
        # Remove test files and directory
        os.remove(TEST_FILE_1)
        os.remove(TEST_FILE_2)
        # Restore from "test.tar.gz"
        bt.restorefiles(TEST_TAR)

    def tearDown(self):
        os.remove(TEST_FILE_1)
        os.remove(TEST_FILE_2)
        os.remove(bt.BACKUP_FOLDER + os.sep + TEST_TAR)

    def test_backupexists(self):
        """Checks if the backup file exists"""
        self.assertTrue(os.path.isfile(bt.BACKUP_FOLDER + os.sep + TEST_TAR))

    def test_restoreexists(self):
        """Checks if the restored files exists"""
        self.assertTrue(os.path.isfile(TEST_FILE_1))
        self.assertTrue(os.path.isfile(TEST_FILE_2))
