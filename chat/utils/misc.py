def f_put(que, item):
    """Functional version of put(), returns queue
    """
    que.put(item)
    return que

def shift(ls):
    """Shifts tuples' values one position to the left and deletes last tuple.

    Examples
    -----
    >>> shift([(0, 14), (15, 17), (18, 28), (40, 60), (75, 99)])
    [(None, 0), (14, 15), (17, 18), (28, 40), (60, 75)]
    """
    my_ls = ls.copy()
    my_ls.append((None, None))
    ret = []
    prev = (None, None)

    for item in my_ls:
        ret.append((prev[1], item[0]))
        prev = item

    ret.pop()
    return ret
