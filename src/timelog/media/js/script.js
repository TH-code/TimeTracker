/* Author: THijs

 */

function pretty_time_string(num) {
    return (num < 10 ? "0" : "" ) + num;
}

function add_minute (str, max) {
    var pre = str.split(' '),
        long_format = pre.length > 1,
        _time = pre[0].split(':'),
        _apm = long_format ? pre[1] : '',
        lookup = {'AM': ['AM', 'PM'], 'PM': ['PM', 'AM']},
        _hrs = parseInt(_time[0], 10),
        _min = parseInt(_time[1], 10) + 1,
        min = _min % 60;
    if (long_format) {
        var hrs = (_hrs === 12 ? 0 : _hrs) + Math.floor(_min / 60),
            lhrs = hrs % 12;
        return pretty_time_string(lhrs !== 0 ? lhrs : 12) + ':' + pretty_time_string(min) + ' ' + lookup[_apm][Math.floor(hrs / 12) % 2]
    } else {
        var hrs = _hrs + Math.floor(_min / 60);
        if (max) {
            return pretty_time_string(hrs % 24) + ':' + pretty_time_string(min);
        } else {
            return hrs + ':' + pretty_time_string(min);
        }
    }    
    
}

setInterval(function() {
    $('.live').each(function () {
        var $me = $(this);
        $me.text(add_minute($me.text(), $me.hasClass('time')));
    })
}, 60000);
