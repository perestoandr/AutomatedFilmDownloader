import contextlib
import os
import datetime
import dropbox
import time
from dropbox.files import FileMetadata, FolderMetadata
from dropbox.exceptions import HttpError
from environment import environment
import logging

logging.basicConfig(level=logging.INFO)
logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)


def download(dbx_obj, _filename_):
    """
    :param dbx_obj: dropbox object
    :param _filename_: filename to download
    :return: returns data as object
    """
    path = '/%s' % _filename_
    while '//' in path:
        path = path.replace('//', '/')
    with stopwatch('download'):
        try:
            md, res = dbx_obj.files_download(path)
        except HttpError as err:
            logging.error('HTTP error: ' + err.__str__())
            return None
    data = res.content
    # print len(data), 'bytes; md:', md
    return data


def upload_data(dbx_obj, data, filename_path, overwrite=False):
    """
    Upload a data.
    :param dbx_obj: dropbox object
    :param data: object to upload
    :param filename_path: path in dropbox system
    :param overwrite: parameter to overwrite file if it exists
    :return: Return the request response, or None in case of error.
    """
    path = '/%s' % filename_path
    while '//' in path:
        path = path.replace('//', '/')
    mode = (dropbox.files.WriteMode.overwrite
            if overwrite
            else dropbox.files.WriteMode.add)

    with stopwatch('upload %d bytes' % len(data)):
        try:
            res = dbx_obj.files_upload(
                data, path, mode,
                mute=True)
        except dropbox.exceptions.ApiError as err:
            logging.error('API error: ' + err.__str__())
            return None
    log_msg = 'uploaded as ' + res.name.encode('utf8')
    logging.info(log_msg)
    return res


def upload(dbx_obj, localfile_path, filename_path, overwrite=False):
    """
    Upload a file.
    :param dbx_obj: dropbox object
    :param localfile_path: path to uploading file in local filesystem
    :param filename_path: path in dropbox system
    :param overwrite: parameter to overwrite file if it exists
    :return: Return the request response, or None in case of error.
    """
    path = '/%s' % filename_path
    while '//' in path:
        path = path.replace('//', '/')
    mode = (dropbox.files.WriteMode.overwrite
            if overwrite
            else dropbox.files.WriteMode.add)
    mtime = os.path.getmtime(localfile_path)
    with open(localfile_path, 'rb') as f:
        data = f.read()
    with stopwatch('upload %d bytes' % len(data)):
        try:
            res = dbx_obj.files_upload(
                data, path, mode,
                client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
                mute=True)
        except dropbox.exceptions.ApiError as err:
            logging.error('API error: ' + err.__str__())
            return None
    log_msg = 'uploaded as ' + res.name.encode('utf8')
    logging.info(log_msg)
    return res


@contextlib.contextmanager
def stopwatch(message):
    """
    Context manager to print how long a block of code took.
    :param message: This message prints after finish
    :return: Returns time result
    """
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        log_msg = ('Total elapsed time for %s: %.3f' % (message, t1 - t0))
        logging.info(log_msg)


def set_up_dropbox():
    dbx = dropbox.Dropbox(environment.get('dropbox_OAuth2_key'))
    dbx.users_get_current_account()
    return dbx

# if __name__ == '__main__':
#     dbx = set_up_dropbox()
#     dbx_path = environment.get('dropbox_folder_path')
#     file_path = environment.get('downloaded_torrents_location')
#     filename = 'TheManfromUNCLE.torrent'
#     upload(dbx, file_path + filename, filename)
#     data = download(dbx, filename)
#     with open(file_path + filename, 'w') as f:
#         f.write(data)
#         f.close()
#     upload_data(dbx, data, 'from_object_' + filename, overwrite=True)
