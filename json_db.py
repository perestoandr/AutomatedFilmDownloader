import json
import db_updater as db


def new_empty_db(dbx_obj, filename):
    clear_data = {'total': 0, 'records': []}
    clear_data = json.dumps(clear_data, indent=4)
    db.upload_data(dbx_obj, clear_data, filename, overwrite=True)


def add_to_db(dbx_obj, additional_data, filename):
    data = read_from_db(dbx_obj, filename)
    data['records'].extend(additional_data)
    data['total'] = len(data['records'])
    data = json.dumps(data, indent=4)
    db.upload_data(dbx_obj, data, filename, overwrite=True)


def read_from_db(dbx_obj, filename):
    data = db.download(dbx_obj, filename)
    return json.loads(data)


if __name__ == '__main__':
    dbx = db.set_up_dropbox()
    name = 'data.json'
    new_empty_db(dbx, name)
    print read_from_db(dbx, name)
    add_to_db(dbx, {'name': name, 'test_data': 'not empty'}, name)
    print read_from_db(dbx, name)
    add_to_db(dbx, {'name': name + ', again', 'test_data': 'not empty, again'}, name)
    print read_from_db(dbx, name)
    add_to_db(dbx, {'name': name + ', again', 'test_data': ''}, name)
    print read_from_db(dbx, name)
