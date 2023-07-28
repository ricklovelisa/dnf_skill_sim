tree = {
    '炸热': {
        '波爆': {},
        '无双': {
            "不动": {}
        }
    }
}


def traverse(tree, path=None):
    if path is None:
        path = []
    paths = []
    for node, subtree in tree.items():
        current_path = path + [node]
        if not subtree:
            paths.append(current_path)
        else:
            for sub_path in traverse(subtree, current_path):
                paths.append(sub_path)
    return paths


for path in traverse(tree):
    print(type(path), path)
