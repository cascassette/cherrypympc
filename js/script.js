/* progressbar.js
 * this will have EVERYTHING javascript in time :)
 */

var tbar_width_px = 400;
var tbar_t_elapsed, tbar_t_total=200;
var songpos;
var intah=0;

/* update errthing
 *  update playtime every sec
 * sync from mpd
 *  sync state/current/playtime track every 5 secs, or every minute if tracklen > 30 min
 *  sync playlist every 1 min
 */
function init_info_framework() {
}

function init_timebar(t_elapsed, t_total, pos, playing) {
	tbar_t_elapsed = t_elapsed;
	tbar_t_total = t_total;
	songpos = pos;
	set_tb_time();
	//init_info_framework();
	if (playing)
		intah = setInterval("inc_time();", 1000);
}

function inc_time() {		// used to increase tbar_t_elapsed every second
	if (tbar_t_elapsed < tbar_t_total) {
		tbar_t_elapsed++;
		set_tb_time();
	} else {
		clearInterval(intah);
		//$$('subframe')[0].contentDocument.reload();
		window.location.reload();
	}
}

function set_tb_time() {
	$$("div#progressbartextlayer")[0].innerHTML=secstotimestr(tbar_t_elapsed) + " / " + secstotimestr(tbar_t_total);
	$$("div#progressbar")[0].style.width = (tbar_t_elapsed/tbar_t_total)*(tbar_width_px-8);		// 8 is for indicator width+border
}

function do_seek(event) {
	pos_x = event.offsetX?event.offsetX:event.pageX-document.getElementById('progressbarcontainer').offsetLeft;
	pos_x -= 6;
	pos_x = ( pos_x < 0? 0 : pos_x )
	newtime=Math.floor((pos_x/tbar_width_px)*tbar_t_total);
	// do ajax-ish call to seek
	async_cl = new XMLHttpRequest();
	async_cl.open( "GET", "/seek?pos="+songpos+"&secs="+newtime );
	async_cl.onreadystatechange = function() {
		if ( async_cl.responseText == "OK" ) {
			tbar_t_elapsed=newtime;
			set_tb_time();
		}
	};
	async_cl.send();
}

function secstotimestr(secs) {
	sec = secs % 60;
	min = (secs - sec) / 60;
	min = Math.floor( min );
	if ( min >= 60 )
	{
		mint = min % 60;
		hour = ( min - mint ) / 60;
		mint = Math.floor( mint );
		sec = numberFormatter("00")(sec);
		mint = numberFormatter("00")(mint);
		//sec = ((sec+'').length == 1)?'0'+sec:''+sec
		//mint = ((mint+'').length == 1)?'0'+mint:''+mint
		return (hour + ":" + mint + ":" + sec);
	}
	else
	{
		sec = numberFormatter("00")(sec);
		//sec = ((sec+'').length == 1)?'0'+sec:''+sec
		return (min + ":" + sec);
	}
}
