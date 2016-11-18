import os

def load_lib_file(relative_path):
    with open(BASE + '/' + relative_path, 'r') as content_file:
        content = content_file.read()

    return content

def resource_path(*path):
    return os.path.join(BASE, 'resources', *path)
