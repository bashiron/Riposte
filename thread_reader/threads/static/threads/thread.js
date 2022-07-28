const conv = $('#base-tweet').attr('data-conv');    //aun no se usa...

function moreReplies(url) {
    const boton = $('#more-n');   //reemplazar n por el numero de boton (depende del nivel)
    const fila = boton.parent();
    const tok = boton.attr('data-token');
    const twid = fila.attr('data-id');
    const usid = fila.attr('data-user');
    $.ajax(
        {
            type: 'GET',
            url: url,
            data: {
                token: tok,
                twid: twid,
                user_id: usid
            },
            success: function (res) {
                const tweets = generateElements(res);
                if (res.token) {
                    tweets.push(boton.attr('data-token', res.token));    //actualizo el token y muevo el boton al final de la lista
                } else {
                    boton.remove();
                }
                fila.append(tweets);
            }
        }
    );
};

function generateElements(res) {
    const elems = [];
    for (let i = 0; i < res.items.length; i++) {
        const parrafo_meta = $('<p/>', {
            'class': 'user-name',
            html: res.items[i].name
        });
        const link = $('<a/>', {
            href: `https://twitter.com/${res.items[i].username}/status/${res.items[i].id}`,
            target: '_blank',
            html: 'link'
        })
        const metadata = $('<div/>', {
            'class': 'article-metadata',
            html: [parrafo_meta, link]
        });
        const parrafo_cont = $('<div/>', {
            'class': 'article-content',
            html: res.items[i].text
        });
        const articulo = $('<article/>', {
            'class': 'content-section',
            'data-id': res.items[i].id,
            'data-user': res.items[i].user_id,
            html: [metadata, parrafo_cont, link]
        });
        elems.push(articulo);
    }
    return elems
}

function openThread(reply, url) {
    const container = reply.parent();
    const twid = reply.attr('data-id')
    const user_id = reply.attr('data-user');
    const fila = $('<div/>', {
        'class': 'fila',
        'data-id': twid,
        'data-user': user_id
    });
    $.ajax(
        {
            type: 'GET',
            url: url,
            data: {
                twid: twid,
                user_id: user_id
            },
            success: function (res) {
                const tweets = generateElements(res);
                if (res.token) {
                    tweets.push($('<a/>', {
                        'class': 'load-more btn btn-primary btn-lg',
                        id: 'more-n',   //reemplazar n por el numero de boton (depende del nivel)
                        'data-token': res.token
                    }));
                }
                fila.append(tweets);
                container.append(fila);
            }
        }
    );
}