def tree_find(element, tree):
    if element in tree:
        return tree

    for value in tree.values():
        result = tree_find(element, value)
        if result:
            return result

    return None


def chunks(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]