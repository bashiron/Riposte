function moreReplies(url) {
    const boton = $('#more');
    const row = boton.parent();
    const tok = boton.attr('data-token');
    const conv = row.attr('data-conv');
    const usid = row.attr('data-user');
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
                const items = [];
                console.log(res);
                for (let i = 0; i < res.data.length; i++) {
                    const parrafo_meta = $('<p/>', {
                        'class': 'user-name mr-2',
                        html: res.includes.users[i].name
                    });
                    const link_meta = $('<a/>', {
                        href: `https://twitter.com/${res.includes.users[i].username}/status/${res.data[i].id}`,
                        target: '_blank',
                        html: 'link'
                    })
                    const metadata = $('<div/>', {
                        'class': 'article-metadata',
                        html: [parrafo_meta, link_meta]
                    });
                    const parrafo_cont = $('<p/>', {
                        'class': 'article-content',
                        html: res.data[i].text
                    });
                    const articulo = $('<article/>', {
                        'class': 'content-section',
                        html: [metadata, parrafo_cont]
                    });
                    const reply = $('<div/>', {
                        'class': 'col',
                        html: articulo
                    });
                    items.push(reply);
                }
                if (res.meta.next_token) {
                    items.push(boton.attr('data-token', res.meta.next_token));    //actualizo el token y muevo el boton al final de la lista
                } else {
                    boton.remove();
                }
                row.append(items);
            }
        }
    )
};
