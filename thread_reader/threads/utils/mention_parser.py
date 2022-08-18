from .misc import shift

# TODO: si el texto es solo una mencion a un usuario (un amigo por ejemplo) la mencion es borrada porque esta justo despues de las menciones generadas automaticamente
# TODO: a lo mejor se podria pedir informacion a la api para determinar cual de las menciones es la ultima de las generadas automaticamente (la del padre mas alto)
# TODO: a lo mejor se puede usar el conversation_id
def rm_parents_mentions(text, mentions):
    pos_ls = list(map(lambda m: (m['start'], m['end']), mentions))
    ed = last_mention_ending(pos_ls) + 1
    return text[ed:]

def last_mention_ending(pos_ls):
    shifted = shift(pos_ls)
    consec = [consecutive(pos) for pos in shifted]
    cons_pos = []

    for i in range(len(pos_ls)):
        if consec[i]:
            cons_pos.append(pos_ls[i])
        else:
            break

    try:
        end = cons_pos[-1][1]
    except IndexError:
        end = 0
    return end

def consecutive(tup):
    return tup[0] is None or tup[1] == tup[0] + 1

# quita las menciones autogeneradas del texto
# TODO: por ahora solo funciona si el primer tweet no es respuesta de ningun otro, sino quedan menciones sin borrar
def rm_auto_mentions(text, mentions, users):
    filtradas = [m for m in mentions if (m['id'] in users)]
    return rm_all_mentions(text, filtradas)


def rm_all_mentions(text, mentions):
    pos_ls = list(map(lambda m: (m['start'], m['end']), mentions))
    gap = 0

    for pos in pos_ls:
        st = pos[0] - gap
        ed = pos[1] - gap + 1   # +1 por el espacio
        text = text[:st] + text[ed:]
        gap += pos[1] - pos[0] + 1   # +1 por el espacio

    return text

def entities_mention(obj, levels):
    obj['entities'] = {'mentions': []}
    offset = 0

    for lv in levels:
        length = len(lv['user_username'])
        mention = {
            'start': offset,
            'end': offset + 1 + length,  # +1 por el arroba
            'username': lv['user_username'],
            'id': lv['user_id']
        }
        obj['entities']['mentions'].append(mention)
        offset += (1 + length + 1)    # +1 por el arroba y +1 por el espacio

def text_mention(obj, levels):
    pos = 0

    for lv in levels:
        mention = '@' + lv['user_username'] + ' '
        txt = obj['text']
        obj['text'] = txt[:pos] + mention + txt[pos:]
        pos += len(mention)
