let static_url = undefined;
let more_url = undefined;
let open_url = undefined;
let close_url = undefined;

let art, links;    //variables para debugear en consola

//guardo los urls de django porque no puedo usar el tag de static o url en javascript
function storeUrls(static, open, more, close) {
    static_url = static;
    open_url = open;
    more_url = more;
    close_url = close;
}

/**
 * Carga mas respuestas dentro del mismo nivel de conversacion.
 * @param  {jQuery} boton el boton que fue activado
 */
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
                fila.append(tweets);    //acomodo los tweets al final de la fila
                popups.append(pops);    //lo mismo con los popups
                updateSupports(extractLevel(nivel));
            }
        }
    );
};

/**
 * Genera el html y define los handlers a eventos para los tweets.
 * @param  {json} res respuesta en formato json
 * @return {[jQuery]}   tweets preparados
 */
function prepareTweets(res) {
    const tweets = generateTweets(res);
    tweets.forEach(t => setTweetHandlers(t));
    return tweets;
}

/**
 * Setea los handlers de los tweets.
 */
function setTweetHandlers(tweet) {
    setClickHandler(tweet);
    setMouseHandlers(tweet);
}

/**
 * Setea el handler de click.
 * Solo abre un nuevo thread si el tweet no es el activo, sino lo cierra.
 */
function setClickHandler(tweet) {
    tweet.click(function () {
        if (!$(this).hasClass('active')) {
            openThread($(this));
        } else {
            closeThread($(this));
        }
    });
}

/**
 * Setea los handlers de mouse. Al entrar el mouse se muestra y posiciona el popup y su imagen actual, al salir el mouse se esconde el popup.
 */
function setMouseHandlers(tweet) {
    tweet.mouseenter(function () {
        const popup = getPopup($(this));
        const index = popup.children().eq(-1).attr('data-index');
        $(this).addClass('focused');
        if (popup[0]) {     //esta condicion evalua si existe el elemento
            popup.css('display', 'flex');
            positionPopup(popup, $(this));
            popup.children('img').eq(index).css('display', 'block');
            popup.find('button')[0].focus();    //el boton invisible se focusea para poder atrapar las teclas presionadas
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

/**
 * Devuelve el popup asociado a un tweet.
 */
function getPopup(tweet) {
    return tweet.parent().next().find($(`[data-id="${tweet.attr('data-id')}"]`));
}

/**
 * Posiciona el popup centrado debajo del tweet asociado.
 * @param  {jQuery} popup el popup a posicionar
 * @param  {jQuery} tweet el tweet asociado
 */
function positionPopup(popup, tweet) {
    const rect = tweet[0].getBoundingClientRect();  //esta variable almacena info sobre el tamaño y posicion del tweet
    const left = rect.left;
    const width = rect.width;
    const pop_width = popup[0].clientWidth;
    popup.css('left', `${left + (width/2) - (pop_width/2)}px`); //la resta de las mitades de los width son para centrar el popup
}

/**
 * Genera el HTML de los tweets, tambien setea los handlers necesarios.
 * @param  {json} res respuesta en formato json
 * @return {[html]} una lista con los elementos HTML que representan a los tweets
 */
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

/**
 * Setea los handlers de la metadata.
 */
function setMetadataHandlers(meta) {
    meta.hover(     //el evento del mouse sobre el elemento
        function () {   //entra el mouse
            $(this).css('overflow', 'visible');
            $(this).find('.support').css('visibility', 'visible');
            $(this).find('.user-name').css('color', '#617ea7');
        },
        function () {   //sale el mouse
            $(this).css('overflow', 'hidden');
            $(this).find('.support').css('visibility', 'hidden');
            $(this).find('.user-name').css('color', 'black');
        }
    );
}

/**
 * Prepara los popups.
 */
function preparePopups(res) {
    const pops = generatePopups(res);
    return pops;
}

/**
 * Genera el HTML de los popups, tambien setea los handlers necesarios.
 * @param  {json} res respuesta en formato json
 * @return {[html]} una lista con los elementos HTML que representan a los popups
 */
function generatePopups(res) {
    const elems = [];
    for (let i = 0; i < res.items.length; i++) {
        if (res.items[i].urls[0]) {     //solo crear popup si el tweet tiene media
            const imgs = res.items[i].urls.map(url => (
                $('<img/>', {src: url + '&name=small'})
            ));
            const but = $('<button/>', {'data-index': 0, 'data-max': imgs.length});     //un boton invisible que se encarga de atrapar los eventos de teclado y llevar el indice usado para el navegado de imagenes
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

/**
 * Setea los handlers para el boton invisible.
 */
function setButtonHandlers(button) {
    button.keydown(function (ev) {navigatePics($(this),ev)});
}

/**
 * Navega entre las imagenes del popup leyendo la tecla presionada y moviendose en un ciclo entre las imagenes. La tecla 'A' va hacia atras y la 'D' va delante.
 * @param  {jQuery} button el boton invisible
 * @param  {any} event los datos del evento
 */function navigatePics(button, event) {
    const index = parseInt(button.attr('data-index'));
    const max = parseInt(button.attr('data-max'));
    const pos = i => Math.abs(i) % max  //lambda que calcula la posicion haciendo modulo entre el index y el total de imagenes, de esta forma se mueve dentro de un ciclo

    switch (event.code) {
        case 'KeyA':
            button.parent().children('img').css('display', 'none');                     //oculta todas las imagenes
            button.parent().children('img').eq(pos(index-1)).css('display', 'block');   //revela la imagen del numero anterior a la posicion actual
            button.attr('data-index', index-1);                                         //guarda la nueva posicion
            break
        case 'KeyD':
            button.parent().children('img').css('display', 'none');
            button.parent().children('img').eq(pos(index+1)).css('display', 'block');   //revela la imagen del numero siguiente a la posicion actual
            button.attr('data-index', index+1);
            break
    }
}

/**
 * Carga un nuevo nivel de conversacion.
 * @param  {jQuery} reply la respuesta de la cual cargar la conversacion
 */
function openThread(reply) {
    const fila = reply.parent();
    const nivel = fila.parent();
    const container = nivel.parent();
    const lvl = extractLevel(nivel);
    const twid = reply.attr('data-id');
    reply.off('mouseenter mouseleave');    //desactivo el handler de cuando saco el mouse
    getPopup(reply).css('display', 'none'); //oculto el popup del tweet para que no tape
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
                if (res.token) {    //si hay token, o sea si hay mas respuestas que cargar
                    const btn = $('<a/>', {
                        'class': 'load-more btn btn-primary btn-lg',
                        'data-token': res.token,
                        html: $('<img/>', {
                            src: static_url + 'icons/circle-plus-solid.svg',
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
                $('#lv-' + (lvl+1)).replaceWith(new_nivel); //pongo el nuevo nivel en reemplazo del nivel vacio
                container.append($('<div/>', {  //dejo un nivel vacio para el siguiente openThread
                    id: 'lv-' + (lvl+2),
                    'class': 'nivel'
                }));
                updateSupports(lvl+1);
            }
        }
    );
}

/**
 * Extraigo el numero de nivel del elemento 'nivel'.
 */
function extractLevel(nivel) {
    return parseInt(nivel.attr('id').substr(3));
}

/**
 * Cierro un nivel de conversacion, afectando todos los niveles anidados.
 * @param  {jQuery} reply el tweet del cual cerrar conversacion
 */
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
    container.append($('<div/>', {  //dejo un nivel vacio para el siguiente openThread
        id: 'lv-' + (lvl+1),
        'class': 'nivel'
    }));
    reply.removeClass('active');
}

/**
 * Actualiza la altura de todos los support acorde a la del texto que soportan. Esta funcion es necesaria porque esto se tiene que hacer despues de que el username haya sido renderizado.
 * @param  {number} lvl el nivel en el cual actualizar
 */
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









//----------SLIDES--------------



let slideIndex = 1;
showSlides(slideIndex);
showSlidesDos(slideIndex);

function plusSlides(n) {
  showSlides(slideIndex += n);
}

function plusSlidesDos(n) {
    showSlidesDos(slideIndex += n);
  }  

function showSlides(n) {
  let i;
  let slides = $('.base-media .mySlides');
  if (n > slides.length) {slideIndex = 1}    
  if (n < 1) {slideIndex = slides.length}
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";  
  }
  slides[slideIndex-1].style.display = "block";
}

function showSlidesDos(n) {
    let i;
    let slides = $('.modal-media .mySlides');
    if (n > slides.length) {slideIndex = 1}    
    if (n < 1) {slideIndex = slides.length}
    for (i = 0; i < slides.length; i++) {
      slides[i].style.display = "none";  
    }
    slides[slideIndex-1].style.display = "block";
  }
  


//----------MODAL--------------


function openPicture() {
    $('#myModal').css('display', 'block');
}

function closePicture() {
    $('#myModal').css('display', 'none');
}
