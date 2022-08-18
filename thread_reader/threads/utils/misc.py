def f_put(que, item):
    que.put(item)
    return que

# Mueve los valores de las tuplas una posicion a la izquierda y borra la primer tupla
def shift(ls):
    my_ls = ls.copy()
    my_ls.append((None, None))
    ret = []
    prev = (None, None)

    for item in my_ls:
        ret.append((prev[1], item[0]))
        prev = item

    ret.pop()
    return ret
