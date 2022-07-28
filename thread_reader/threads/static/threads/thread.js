function moreReplies(url) {
    const boton = $('#more');
    const fila = boton.parent();
    console.log('boton parent:')
    console.log(fila)
    const tok = boton.attr('data-token');
    const conv = fila.attr('data-conv');
    const usid = fila.attr('data-user');
    $.ajax(
        {
            type: 'GET',
            url: url,
            data: {
                token: tok,
                conv_id: conv,
                user_id: usid
            },
            success: function (res) {
                const tweets = [];
                console.log('res:')
                console.log(res);
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
                        html: [metadata, parrafo_cont, link]
                    });
                    tweets.push(articulo);
                }
                if (res.token) {
                    tweets.push(boton.attr('data-token', res.token));    //actualizo el token y muevo el boton al final de la lista
                } else {
                    boton.remove();
                }
                console.log('tweets:')
                console.log(tweets)
                fila.append(tweets);
            }
        }
    )
};
