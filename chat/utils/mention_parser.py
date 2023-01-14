from .misc import shift

# TODO: si el texto es solo una mencion a un usuario (un amigo por ejemplo) la mencion es borrada porque esta justo despues de las menciones generadas automaticamente
# TODO: a lo mejor se podria pedir informacion a la api para determinar cual de las menciones es la ultima de las generadas automaticamente (la del padre mas alto)
# TODO: a lo mejor se puede usar el conversation_id
def rm_parents_mentions(text, mentions):
    """Returns the text but cropped not to include auto-generated mentions (at the start of the text)

    Parameters
    -----
    text : `str`
        Text to crop.
    mentions : `list` of `dict`
        Objects representing every mention in the tweet.

    Returns
    -----
    `str`
    """
    pos_ls = list(map(lambda m: (m['start'], m['end']), mentions))
    ed = last_mention_ending(pos_ls) + 1
    return text[ed:]

def last_mention_ending(pos_ls):
    """Calculates position of the ending of the last mention in the first chain. It doesn't just use the end of the last
    mention because it can be a user-added mention, it is interested in the auto-gen chain of mentions at the beginning.

    Parameters
    -----
    pos_ls : `list` of `tuple`
        Two-value tuples with: starting position of mention | ending position of mention

    Returns
    -----
    `int`
    """
    shifted = shift(pos_ls)
    consec = [consecutive(pos) for pos in shifted]
    cons_pos = []

    for i in range(len(pos_ls)):    # iterate over pos_ls and consec at the same time
        if consec[i]:
            cons_pos.append(pos_ls[i])
        else:
            break

    try:
        end = cons_pos[-1][1]   # second value (end) of last position
    except IndexError:
        end = 0
    return end

def consecutive(tup):
    return tup[0] is None or tup[1] == tup[0] + 1

# quita las menciones autogeneradas del texto
# TODO: por ahora solo funciona si el primer tweet no es respuesta de ningun otro, sino quedan menciones sin borrar
def rm_auto_mentions(text, mentions, users):
    """Removes auto generated mentions from the tweet text

    Parameters
    -----
    text : `str`
        Text to remove mentions from.
    mentions : `list` of `dict`
        Objects representing every mention in the tweet.
    users : `list` of `dict`
        Objects representing every user involved in the conversation.
    """
    filtered = [m for m in mentions if (m['id'] in users)]
    return rm_all_mentions(text, filtered)


def rm_all_mentions(text, mentions):
    """Returns text but with all received mentions removed from it.

    Parameters
    -----
    text : `str`
        Text to remove mentions from.
    mentions : `list` of `dict`
        Objects representing mentions. These mentions are to be removed from the final text.

    Returns
    -----
    `str`
    """
    pos_ls = list(map(lambda m: (m['start'], m['end']), mentions))
    gap = 0     # used for adjusting to the decreasing length of the text

    for pos in pos_ls:
        st = pos[0] - gap
        ed = pos[1] - gap + 1   # +1 for whitespace
        text = text[:st] + text[ed:]
        gap += pos[1] - pos[0] + 1   # +1 for whitespace

    return text

def entities_mention(obj, levels):
    """Insert mentions into the entities of the received tweet object.

    Parameters
    -----
    obj : `dict`
        Tweet object to update.
    levels : `list` of `dict`
        Chat levels data.
    """
    obj['entities'] = {'mentions': []}
    offset = 0

    for lv in levels:
        length = len(lv['user_username'])
        mention = {
            'start': offset,
            'end': offset + 1 + length,  # +1 for the @
            'username': lv['user_username'],
            'id': lv['user_id']
        }
        obj['entities']['mentions'].append(mention)
        offset += (1 + length + 1)    # +1 for the @ and +1 for the whitespace

def text_mention(obj, levels):
    """Insert mentions into the text of the received tweet object.

    Parameters
    -----
    obj : `dict`
        Tweet object to update.
    levels : `list` of `dict`
        Chat levels data.
    """
    pos = 0

    for lv in levels:
        mention = '@' + lv['user_username'] + ' '
        txt = obj['text']
        obj['text'] = txt[:pos] + mention + txt[pos:]
        pos += len(mention)
