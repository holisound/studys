function XMLHttp() {
    this.request = function (param) { };
    this.response = function (param) { };
};
var http = new XMLHttp();

function initXMLHttpRequest() {
    var open = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (...args) {
        var send = this.send;
        var _this = this;
        var post_data = [];
        this.send = function (...data) {
            post_data = data;
            return send.apply(_this, data)
        };
        http.request(args);

        this.addEventListener('readystatechange', function () {
            if (this.readyState == 3 && this.status == 200 && args[1].indexOf('/weapi/song/enhance/player/url/v1') != -1) {
                var jsonobj = JSON.parse(this.response),
                    musicUrl = jsonobj.data[0].url
                    ;
                http.response({ musicUrl: musicUrl })

            }
            /*
            if (this.readyState === 4) {
                var config = {
                    url: args[1],
                    status: this.status,
                    method: args[0],
                    data: post_data
                }
                http.response({ config, response: this.response })
            }
            */
        }, false);
        return open.apply(this, args);
    }
}

function netease() {
    http.request = function (param) {
        console.log(param, "---request");
    };
    http.response = function (res) {
        var info = onload();
        info.musicUrl = res.musicUrl;
        console.log(info);
        if (!q1('#clickdownload')) {
            var div = iframeDoc.createElement('div'),
                a = iframeDoc.createElement('a');
            a.id = 'clickdownload';
            a.target = '_blank';
            a.href = `http://localhost:8080/netease/music?data=${encodeURIComponent(JSON.stringify(info))}`;
            a.innerHTML = '点这里下载';
            div.appendChild(a);
            q1("#wgloadok").appendChild(div);
        }

    };
    initXMLHttpRequest();

    var iframeDoc = window.frames['contentFrame'].document
        ;

    function q1(selector) {
        return iframeDoc.querySelector(selector)
    }
    function q(selector) {
        return iframeDoc.querySelectorAll(selector)
    };
    function onload() {
        /*提取页面中歌曲的信息*/
        var
            node_song = q1('.tit .f-ff2'),
            node_desc = q1('.tit .subtit'),
            node_artist = q1('.des.s-fc4>span'),
            node_albumn = q1('.des.s-fc4>a'),
            node_img = q1('.m-lycifo .u-cover img')
            ;
        var info = {
            artist: node_artist ? node_artist.getAttribute('title') : '',
            albumn: node_albumn ? node_albumn.innerHTML : '',
            song: node_song ? node_song.innerHTML : '',
            desc: node_desc ? node_desc.innerHTML : '',
            imgUrl: node_img ? node_img.src : ''
        };
        return info
    };
    if (q1('#wgloadok')) {
        return
    }
    var div = iframeDoc.createElement('div');
    div.id = 'wgloadok';
    div.innerHTML = '网易音乐外挂加载成功.';
    div.style = 'color:red;font-size:15px;float:left;';
    q1(".cvrwrap").appendChild(div);
}

function kugou() {
    if ($('#wgloadok').length>0) {
        return
    }
    var info = {
        desc: ''
    ,   song: $('.active .musiclist-songname-txt').text() || ''
    ,   imgUrl: $('.albumImg').find('img').attr('src') || ''
    ,   musicUrl: $('#myAudio').attr('src') || ''
    ,   albumn: $('.albumName').find('a').attr('title') || ''
    ,   artist: $('.active .musiclist-artist').text() || ''
    };
    var link = $('<a id="wgloadok">点这里下载</a>');
    link.attr({
        style: 'color:red;font-size:15px;position:fixed;left:15%;',
        target: '_blank',
        href: `http://localhost:8080/netease/music?data=${encodeURIComponent(JSON.stringify(info))}`
    });
    $('.singerContent').append(link);
}

(function () {
    var host = window.location.host;
    if (host === 'music.163.com') {
        netease();
    } else if (host == 'www.kugou.com') {
        kugou();
    } else {
        alert('加载失败T_T、');
    }
})();
