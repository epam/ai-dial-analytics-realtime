def merge_str(target, source):
    if target is None:
        return source
    else:
        return target + source

def merge_dicts(target, source):
    for key, value in source.items():
        if key in target:
            if isinstance(value, int):
                target[key] = value
            elif isinstance(value, str):
                target[key] = merge_str(target[key], value)
            else:
                merge(target[key], value)
        else:
            target[key] = value

    return target

def merge_lists(target, source):
    for i in source:
        index = i['index']

        if index < len(target):
            merge(target[index], i)
        else:
            target.append(i)

    return target

def merge(target, source):
    if isinstance(source, list):
        return merge_lists(target, source)
    if isinstance(source, dict):
        return merge_dicts(target, source)
