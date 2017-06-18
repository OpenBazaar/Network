"""Import and export data for the OpenBazaar server."""
__author__ = 'marc'
from constants import DATA_FOLDER
import db.datastore as db
import os
import sqlite3 as lite
import tarfile
import time

BACKUP_FOLDER = 'backup'

def _getdatabase():
    """Retrieves the OpenBazaar database file."""
    database = db.Database()
    return database.DATABASE

def backupfiles(output_name=None):
    """Archives OpenBazaar files in a single tar archive."""
    os.chdir(DATA_FOLDER)
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)
    if not output_name:
        output_name = 'backup_{0}.tar.gz'.format(time.strftime('%Y-%m-%d'))
    if not os.path.isabs(output_name):
        output = BACKUP_FOLDER + os.sep + output_name
    if os.path.isfile(output):
        raise IOError(output + ' already exists.')

    # Lock the database
    db_file = _getdatabase()
    db_connection = lite.connect(db_file)
    db_connection.commit()

    # Archive files
    files = os.listdir(DATA_FOLDER)
    with tarfile.open(output, 'w:gz') as tar:
        for fil in files:
            if fil != BACKUP_FOLDER:
                tar.add(fil)
        tar.close()

    # Unlock database
    db_connection.rollback()
    db_connection.close()

    return True


def restorefiles(input_file):
    """Restores files of given archive to OpenBazaar folder."""
    os.chdir(DATA_FOLDER)
    if not os.path.isabs(input_file):
        input_file = BACKUP_FOLDER + os.sep + input_file

    if not os.path.isfile(input_file):
        raise IOError(input_file + ' does not exist.')

    # Unarchive files
    with tarfile.open(input_file, 'r:gz') as tar:
        tar.extractall()

    return True
