# Author: Mateusz Słuszniak
# this script inputs auxiliary zeros between two consequtive ';' signs
# because getline with delimiter set to ';' does not accepts two consequtive delimiters
import os
data_path = 'path_to_dir_with_pb_instances'

for filename in os.scandir(data_path):
    if filename.is_file():
        data = None
        with open(filename.path, 'r', encoding="utf8") as file:
            data = file.read()
        data = data.replace(';;', ';0;').replace(';\n', ';0\n')
        with open(filename.path, 'w', encoding="utf8") as file:
            file.write(data)
