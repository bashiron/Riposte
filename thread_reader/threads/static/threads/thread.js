let media_url = undefined;
let more_url = undefined;
let open_url = undefined;
let close_url = undefined;

let art, links;    //variables para debugear en consola

function storeUrls(media, open, more, close) {
    media_url = media;
    open_url = open;
    more_url = more;
    close_url = close;
}

function moreReplies(boton) {
    const nivel = boton.parent().parent();
    const fila = nivel.children().eq(0) //la lista de tweets
    const popups = nivel.children().eq(1) //la lista de popups
    const tok = boton.attr('data-token');
    const twid = nivel.attr('data-id');
    $.ajax(
        {
            type: 'GET',
            url: more_url,
            data: {
                token: tok,
                twid: twid,
            },
            success: function (res) {
                const tweets = prepareTweets(res);
                const pops = preparePopups(res);
                if (res.token) {
                    tweets.push(boton.attr('data-token', res.token));   //actualizo el token y muevo el boton al final de la lista
                } else {
                    boton.remove();
                }
                fila.append(tweets);
                popups.append(pops);
                updateSupports(extractLevel(nivel));
            }
        }
    );
};

//genera el html y define los handlers a eventos
function prepareTweets(res) {
    const tweets = generateTweets(res);
    tweets.forEach(t => setTweetHandlers(t));
    return tweets;
}

function setTweetHandlers(tweet) {
    setClickHandler(tweet);
    setMouseHandlers(tweet);
}

function setClickHandler(tweet) {
    tweet.click(function () {
        if (!$(this).hasClass('active')) {
            openThread($(this));
        } else {
            closeThread($(this));
        }
    });
}

function setMouseHandlers(tweet) {
    tweet.mouseenter(function () {
        const popup = getPopup($(this));
        const index = popup.children().eq(-1).attr('data-index');
        $(this).addClass('focused');
        if (popup[0]) {
            popup.css('display', 'flex');
            positionPopup(popup, $(this));
            popup.children('img').eq(index).css('display', 'block');
            popup.find('button')[0].focus();
        }
    });
    tweet.mouseleave(function () {
        const popup = getPopup($(this));
        $(this).removeClass('focused');
        if (popup[0]) {
            popup.css('display', 'none');
        }
    });
}

function getPopup(tweet) {
    return tweet.parent().next().find($(`[data-id="${tweet.attr('data-id')}"]`));
}

function positionPopup(popup, tweet) {
    const rect = tweet[0].getBoundingClientRect();
    const left = rect.left;
    const width = rect.width;
    const pop_width = popup[0].clientWidth;
    popup.css('left', `${left + (width/2) - (pop_width/2)}px`); //la resta de las mitades de los width son para centrar el popup
}

function generateTweets(res) {
    const elems = [];
    for (let i = 0; i < res.items.length; i++) {
        const support = $('<div/>', {
            'class': 'support'
        });
        const parrafo_meta = $('<div/>', {
            'class': 'user-name',
            html: res.items[i].name,
        });
        const link = $('<a/>', {
            'class': 'link',
            href: `https://twitter.com/${res.items[i].username}/status/${res.items[i].id}`,
            target: '_blank',
            html: 'link'
        })
        const metadata = $('<div/>', {
            'class': 'article-metadata',
            html: [support, parrafo_meta, link]
        });
        setMetadataHandlers(metadata);
        const parrafo_cont = $('<div/>', {
            'class': 'article-content',
            html: res.items[i].text
        });
        const articulo = $('<article/>', {
            'class': 'content-section',
            'data-id': res.items[i].id,
            html: [metadata, parrafo_cont, link]
        });
        elems.push(articulo);
    }
    return elems;
}

function setMetadataHandlers(meta) {
    meta.hover(
        function () {
            $(this).css('overflow', 'visible');
            $(this).find('.support').css('visibility', 'visible');
            $(this).find('.user-name').css('color', '#617ea7');
        },
        function () {
            $(this).css('overflow', 'hidden');
            $(this).find('.support').css('visibility', 'hidden');
            $(this).find('.user-name').css('color', 'black');
        }
    );
}

function preparePopups(res) {
    const pops = generatePopups(res);
    return pops;
}

function generatePopups(res) {
    const elems = [];
    for (let i = 0; i < res.items.length; i++) {
        if (res.items[i].urls[0]) {     //solo mostrar popup si el tweet tiene media
            const imgs = res.items[i].urls.map(url => (
                $('<img/>', {src: url})
            ));
            const but = $('<button/>', {'data-index': 0, 'data-max': imgs.length});
            setButtonHandlers(but);
            imgs.push(but);
            const popup = $('<span/>', {
                'class': 'images-popup',
                'data-id': res.items[i].id,
                html: imgs
            });
            elems.push(popup);
        }
    }
    return elems;
}

function setButtonHandlers(button) {
    button.keydown(function (ev) {navigatePics($(this),ev)});
}

function navigatePics(button, event) {
    const index = parseInt(button.attr('data-index'));
    const max = parseInt(button.attr('data-max'));
    const pos = i => Math.abs(i) % max

    switch (event.code) {
        case 'KeyA':
            button.parent().children('img').css('display', 'none');
            button.parent().children('img').eq(pos(index-1)).css('display', 'block');
            button.attr('data-index', index-1);
            break
        case 'KeyD':
            button.parent().children('img').css('display', 'none');
            button.parent().children('img').eq(pos(index+1)).css('display', 'block');
            button.attr('data-index', index+1);
            break
    }
}

function openThread(reply) {
    const fila = reply.parent();
    const nivel = fila.parent();
    const container = nivel.parent();
    const lvl = extractLevel(nivel);
    const twid = reply.attr('data-id');
    reply.off('mouseenter mouseleave');    //desactivo el handler de cuando saco el mouse
    getPopup(reply).css('display', 'none');
    reply.addClass('active');
    fila.addClass('locked-thread');
    fila.children('article').children('.article-metadata').off('mouseenter mouseleave');
    fila.children('article:not(.active)').off('click mouseenter mouseleave');    //desactivo el handler de click para todos los otros tweets
    fila.find('.load-more').off('click')
    const new_fila = $('<div/>', {
        'class': 'fila'
    });
    const new_popups = $('<div/>', {
        'class': 'popups'
    });
    $.ajax(
        {
            type: 'GET',
            url: open_url,
            data: {
                twid: twid
            },
            success: function (res) {
                const tweets = prepareTweets(res);
                const pops = preparePopups(res);
                if (res.token) {
                    const btn = $('<a/>', {
                        'class': 'load-more btn btn-primary btn-lg',
                        'data-token': res.token,
                        html: $('<img/>', {
                            src: media_url + '/icons/circle-plus-solid.svg',
                            alt: 'cargar mas'
                        })
                    });
                    btn.click(function () {
                        moreReplies($(this));
                    });
                    tweets.push(btn);
                }
                new_fila.append(tweets);
                new_popups.append(pops);
                const new_nivel = $('<div/>', {
                    id: 'lv-' + (lvl+1),
                    'class': 'nivel',
                    'data-id': twid,
                    html: [new_fila, new_popups]
                });
                $('#lv-' + (lvl+1)).replaceWith(new_nivel);
                container.append($('<div/>', {  //dejo un nivel vacio para el siguiente openThread
                    id: 'lv-' + (lvl+2),
                    'class': 'nivel'
                }));
                updateSupports(lvl+1);
            }
        }
    );
}

//tomo el numero del nivel
function extractLevel(nivel) {
    return parseInt(nivel.attr('id').substr(3));
}

function closeThread(reply) {
    const fila = reply.parent();
    const nivel = fila.parent();
    const container = nivel.parent();
    const lvl = extractLevel(nivel);
    const last_lvl = extractLevel(container.children().eq(-2));     //el nivel del anteultimo ya que el ultimo esta vacio
    $.ajax(
        {
            type: 'GET',
            url: close_url,
            data: {
                num: last_lvl - lvl
            },
            success: res => console.log(res)
        }
    );
    setMouseHandlers(reply);
    fila.removeClass('locked-thread');
    fila.children('article').children('.article-metadata').each(function () {
        setMetadataHandlers($(this));
    });
    fila.children('article:not(.active)').each(function () {
        setTweetHandlers($(this));
    });
    fila.find('.load-more').click(function () {
        moreReplies($(this));
    });
    container.children().slice(lvl+1).remove();   //borro los niveles que vienen delante
    container.append($('<div/>', {
        id: 'lv-' + (lvl+1),
        'class': 'nivel'
    }));
    reply.removeClass('active');
}

function updateSupports(lvl) {
    const tweets = $('#lv-' + lvl).children().eq(0).children('article');
    const sups = tweets.children('.article-metadata').children('.support').slice(-10); //los ultimos 10 ya que como maximo, y la mayoria de las veces, cargo 10 tweets
    sups.each(function () {
        const txt = $(this).parent().find('.user-name');
        $(this).css('height', txt.height());
    });
}

//-------------variables para consola----------------

function consoleInit() {
    console.log('Variables inicializadas');
    art = $('#lv-1').children().eq(0).children().eq(2);
    links = $('.link');
}
