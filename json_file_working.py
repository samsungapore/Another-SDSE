from json import loads, dumps

from os.path import exists


def load_json_file(filename):
    if not exists(filename):
        return {}

    with open(filename, 'r') as f:
        data = loads(f.read())

    return data


def dump_into_json(filename, data):

    with open(filename, 'w') as f:
        f.write(dumps(data))


def append_dump_into_json(filename, new_data):
    if not exists(filename):
        return False

    with open(filename, 'r') as f:
        data = loads(f.read())

    data.update(new_data)

    dump_into_json(filename, data)
