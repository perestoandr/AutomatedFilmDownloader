import contextlib
import os
import datetime
import dropbox
import time
from dropbox.files import FileMetadata, FolderMetadata
from dropbox.exceptions import HttpError

# from official dropbox example
# def download(dbx, folder, subfolder, name):
#     """
#     Download a file.
#     Return the bytes of the file, or None if it doesn't exist.
#     """
#     path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
#     while '//' in path:
#         path = path.replace('//', '/')
#     with stopwatch('download'):
#         try:
#             md, res = dbx.files_download(path)
#         except HttpError as err:
#             print('*** HTTP error', err)
#             return None
#     data = res.content
#     print(len(data), 'bytes; md:', md)
#     return data

# modified function from official dropbox example
# TODO: Modify
import environment


def upload(dbx, localfile_path, filename_path, overwrite=False):
    """Upload a file.
    Return the request response, or None in case of error.
    """
    path = '/%s' % filename_path
    while '//' in path:
        path = path.replace('//', '/')
    print path
    mode = (dropbox.files.WriteMode.overwrite
            if overwrite
            else dropbox.files.WriteMode.add)
    mtime = os.path.getmtime(localfile_path)
    with open(localfile_path, 'rb') as f:
        data = f.read()
    with stopwatch('upload %d bytes' % len(data)):
        try:
            res = dbx.files_upload(
                data, path, mode,
                client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
                mute=True)
        except dropbox.exceptions.ApiError as err:
            print('*** API error', err)
            return None
    print 'uploaded as', res.name.encode('utf8')
    return res


@contextlib.contextmanager
def stopwatch(message):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        print('Total elapsed time for %s: %.3f' % (message, t1 - t0))


if __name__ == '__main__':
    dbx = dropbox.Dropbox(environment.environment.get('dropbox_OAuth2_key'))
    dbx.users_get_current_account()
    dbx_path = 'T:/Dropbox/Apps/RutrackerFilmLoader'
    file_path = 'T:/Downloads/TorrentFiles/'
    filename = 'TheManfromUNCLE.torrent'
    upload(dbx, file_path + filename, filename, overwrite=True)
