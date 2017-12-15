//-----------------------------------------实现多个输入框同时输入的方法-----------------------------------------------
/// <summary>
/// 类说明：HttpHelps类，用来实现Http访问，Post或者Get方式的，直接访问，带Cookie的，带证书的等方式
/// 编码日期：2011-08-20
/// 编 码 人：  苏飞
/// 联系方式：361983679  Email：sufei.1013@163.com  Blogs:http://cckan.net
/// </summary>
//得到控件ID
function getid(id) {
    return (typeof id == 'string') ? document.getElementById(id) : id
};
function getOffsetTop(el, p) {
    var _t = el.offsetTop;
    while (el = el.offsetParent) {
        if (el == p) break;
        _t += el.offsetTop
    }
    return _t
};
function getOffsetLeft(el, p) {
    var _l = el.offsetLeft;
    while (el = el.offsetParent) {
        if (el == p) break;
        _l += el.offsetLeft
    }
    return _l
};

var currentInput = null;
//修改属性显示列表
function BoxShow(e) {
    var input = e;
    if (!input.id) {
        input = e.target ? e.target : e.srcElement;
    }
    currentInput = input;
    FillUrls();
    var box = getid("allSitesBoxHdl");
    if (box.style.display == 'block' && currentInput.id == input.id) {
        return;
    }
    box.style.left = (getOffsetLeft(input)) + 'px';
    box.style.top = (getOffsetTop(input) + (input.offsetHeight - 1)) + 'px';
    box.style.width = (input.offsetWidth - 4) + 'px';
    box.style.display = 'block';
}
//显示列表
function BoxShowUrls(e) {
    var input = e;
    if (!input.id) {
        input = e.target ? e.target : e.srcElement;
    }
        BoxShow(e);
}
//给Input设置值
function InputSetValue(val) {
    var obj = currentInput;
    obj.value = val;
    if (obj.getAttribute('url') == 'true') {
        var tags = document.getElementsByTagName('input');
        for (var i = 0; i < tags.length; i++) {
            if (tags[i].getAttribute('url') == 'true' && tags[i] != obj) {
                tags[i].value = val;
            }
        }
    }
    BoxHide();
}

function BoxHide() {
    if (getid("allSitesBoxHdl")) {
        getid("allSitesBoxHdl").style.display = 'none';
    }
}
//加载列表
function FillUrls() {
    var strdomin = $.trim($("#Text1").val());
    var qsData = { 'wd': strdomin, 'p': '3', 'cb': 'ShowDiv', 't': '1324113456725' };
    $.ajax({
        async: false,
        url: "http://suggestion.baidu.com/su",
        type: "GET",
        dataType: 'jsonp',
        jsonp: 'jsoncallback',
        data: qsData,
        timeout: 5000,
        success: function (json) {
            console.log(json)
        },
        error: function (xhr, textStatus) {
            console.log(xhr.status);
            console.log(xhr.readyState);
            console.log(textStatus);
        }
    });
}
function ShowDiv(strurls) {
    var urls = strurls["s"];
    var html = "";
    if (urls) {
        var urllist = urls;
        var forlength = 0;
        var stringcookie;
        for (var i = urllist.length - 1; i >= 0; i--) {
            var textval = urllist[i];
            if ($.trim(textval) != "" && $.trim(textval) != "undefined") {
                html += "<li class=\"lis\"><a href=\"javascript:InputSetValue('" + textval + "');\">" + textval + "</a></li><br/>";
            }
        }
    } else {
        html = "<li style='font-size: 12px;' >&nbsp;&nbsp;没有记录</li>";
    }
    if ($.trim(html) == "") {
        html = "<li style='font-size: 12px;' >&nbsp;&nbsp;没有记录</li>";
    }
    getid("allSitesBoxContent").innerHTML = html;
}
//关闭输入法
function closeIME(e) {
    var obj = e.target ? e.target : e.srcElement;
    obj.style.imeMode = 'disabled';
}

function OnPaste(e) {
    var obj = e.target ? e.target : e.srcElement;
    setTimeout("MoveHttp('" + obj.id + "')", 100);
}
//修正URL
function MoveHttp(id) {
    var val = getid(id).value;
    val = val.replace("http://", "");
    if (val[val.length - 1] == '/') {
        val = val.substring(0, val.length - 1);
    }
    getid(id).value = val;
}
function OnKeyup(e) {
    var obj = e.target ? e.target : e.srcElement;
    setTimeout("addInput('" + obj.id + "')", 200);
}
//赋值
function addInput(id) {
    var obj = getid(id);
    //如果是一个没有True的input不执行
    if (obj.getAttribute('url') == 'true') {
        if (obj.value.indexOf('。') > 0) {
            obj.value = obj.value.replace('。', '.');
        }
        var tags = document.getElementsByTagName('input');
        for (var i = 0; i < tags.length; i++) {
            if (tags[i].getAttribute('url') == 'true' && tags[i] != obj) {
                tags[i].value = obj.value;
            }
        }
    }
    FillUrls();
}
//注册对象的事件
function Init() {
    $("#allSitesBoxHdl")[0].style.display = "none"; 
    $(":text").each(function () {
        if ($(this)[0].getAttribute('url') == 'true') {//给所有的url=true属性的Text加效果
            $(this).bind("keyup", OnKeyup); //按键时
            $(this).bind("mousedown", BoxShowUrls); //鼠标安下时
            $(this).bind("mouseout", BoxHide); //鼠标离开时
            $(this).bind("paste", OnPaste); //处理http;//
            $(this)[0].setAttribute("autocomplete", "off");
        }
    });
}

