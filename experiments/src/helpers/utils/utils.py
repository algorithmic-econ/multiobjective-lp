import json


def write_to_json(path, data):
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def read_from_json(path):
    with open(path, 'r', encoding='utf-8') as file:
        return json.load(file)
