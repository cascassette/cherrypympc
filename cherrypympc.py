#!/usr/bin/env python2

import os.path

from mpd import MPDClient
import cherrypy

from mpclib import SecToTimeString
from mpclib import TreeList

class MPCWebSimple:
	"""Simple MPD Web Client

	GOALS
	CherryPyMPC 0.2 will be able to:
		- display playlist, file tree, and artist/album tree in different tabs
			(without reloading the whole page)
		- update the library (auto refresh when done)
		- seek in a song, graphically
		- be styled much better than 0.1 :-)

	REQS
		- python 2.x
		- python-mpd
		- cherrypy
		
	RUN
		- ./cherrypympc.py"""

# init
	def __init__(self, host, port, passw):
		self.__app__ = "CherryPyMPC 0.2 (static/iframe)"
		self.c = MPDClient()
		self.c.connect(host, port)
		if passw:
			self.c.password(passw)

# actions
	def play(self):
		self.c.play()
		raise cherrypy.HTTPRedirect("/")

	def pause(self):
		self.c.pause()
		raise cherrypy.HTTPRedirect("/")

	def stop(self):
		self.c.stop()
		raise cherrypy.HTTPRedirect("/")

	def prev(self):
		self.c.previous()
		raise cherrypy.HTTPRedirect("/")

	def next(self):
		self.c.next()
		raise cherrypy.HTTPRedirect("/")

	def playno(self, pos):
		if pos:
			self.c.playid(int(pos))
		raise cherrypy.HTTPRedirect("/")

	def addsong(self, song):
		self.c.add(song[1:-1])
		raise cherrypy.HTTPRedirect("/")

	def seek(self, pos, secs):
		self.c.seek(pos, secs)
		cherrypy.response.headers['content-type']='text/plain'
		return "OK"

	def update(self):
		self.c.update()
		cherrypy.response.headers['content-type']='text/plain'
		return "OK"

	def findadd(self, field, query, field2=None, query2=None):
		if field2 and query2:
			self.c.findadd(field, query, field2, query2)
		else:
			self.c.findadd(field, query)
		raise cherrypy.HTTPRedirect("/")

# subframe html
	def playlist(self):
		current_track = self.c.currentsong()['pos']
		plinfo = self.c.playlistinfo()
		pltable = "<table class='playlist'><tr class='header'><th>&nbsp;</th><th>Artist</th><th>Track</th><th>Lengtr</th></tr>"
		for item in plinfo:
			trclass = ""
			if item["pos"] == current_track:
				trclass = " class='currentsong'"
			pltable += "<tr{tr_class} onclick='top.location.href=\"/playno?pos={plpos}\"'><td><img src='/img/musicfile.png' /></td><td>{artist}</td><td>{title}</td><td class='tracklen'>{length}</td></tr>".format( \
					plpos=item["pos"],
					artist=item.get("artist", "&nbsp;"),
					title=item.get("title", item["file"].split("/")[-1]),
					length=SecToTimeString(item["time"]),
					tr_class=trclass)
		pltable += "</table>"
		return self.surround_head_tags_basic(pltable)

	def filetree(self):
		treelist = TreeList(self.c.list('file'))
		def make_ul(tlist, path=[], level=0):
			r = "<ul" + ("" if (level is not 0) else " class='tree'") + ">"
			if len(tlist) > 1:
				flist = sorted(tlist[1:])
				for filename in flist:
					liclass = "" if (filename is not flist[-1] or len(tlist[0].keys()) > 1) else " class='last'"
					r += "<li" + liclass + "> <img src='/img/musicfile.png' alt='folder' /> <a href='addsong?song=\"" + "" + "".join([ "/" + el for el in path])[1:] + "/" + filename + "\"' target='_top'><img src='/img/add.png' alt='add' /></a> " + filename[:filename.rindex(".")]
			dirlist = sorted(tlist[0].keys())
			for subdir in dirlist:
				r += ( "<li>" if subdir is not dirlist[-1] else ("<li class='last'>") ) + "<img src='/img/folder-music.png' alt='folder' /> " + subdir + " <a href='/addsong?song=\"" + "".join([ "/" + el for el in path])[1:] + ("/" if len(path)>0 else "") + subdir + "\"' target='_top'><img src='/img/add.png' alt='add entire folder' /></a>"
				r += make_ul(tlist[0][subdir], path + [subdir], level+1)
				r += "</li>"
			r += "</ul>"
			return r
		return self.surround_head_tags_basic(make_ul(treelist))

	def albumtree(self):
		albumlist = self.c.list("album")
		r = "<ul class='tree'>"
		albumlist = sorted(albumlist)
		for album in albumlist:
			liclass = "" if album is not albumlist[-1] else " class='last'"
			a = album if album else "Unknown Album"
			r += "<li" + liclass + "><img src='/img/cd16.png' alt='cd' /> " + a + " <a href='/findadd?field=album&query=" + a + "' target='_top'><img src='/img/add.png' /></a><ul>"
			tracklist = self.c.find("album", album)
			tracklist = sorted(tracklist, key=lambda t: int(t.get('track', '0').split("/")[0]))			# sort albums
			for track in tracklist:
				fn = track['file']
				t = track.get("title", fn[:fn.rindex('.')].split("/")[-1])
				liclass = "" if (fn is not tracklist[-1]['file']) else " class='last'"
				r += "<li" + liclass + "><a href='addsong?song=\"" + track['file'] + "\"' target='_top'><img src='/img/add.png' alt='add' /></a> " + t + "</li>"
			r += "</ul></li>"
		r += "</ul>"
		return self.surround_head_tags_basic(r)

	def artisttree(self):
		artistlist = self.c.list("artist")
		r = "<ul class='tree'>"
		artistlist = sorted(artistlist)
		for artist in artistlist:
			liclass = "" if artist is not artistlist[-1] else " class='last'"
			r += "<li" + liclass + "><img src='/img/artist16.png' alt='artist' /> " + (artist or "Unknown Artist") + " <a href='/findadd?field=artist&query=" + artist + "' target='_top'><img src='/img/add.png' /></a><ul>"
			tlist_artist = self.c.find("artist", artist)
			albumlist = list(set([ t.get('album', 'Unknown Album') for t in tlist_artist ]))    # get unique albums by artist
			for album in albumlist:
				liclass = "" if album is not albumlist[-1] else " class='last'"
				r += "<li" + liclass + "><img src='/img/cd16.png' alt='cd' /> " + album + " <a href='/findadd?field=album&query=" + album + "&field2=artist&query2=" + artist + "' target='_top'><img src='/img/add.png' /></a><ul>"
				try:
					tlist_album = [ x for x in tlist_artist if x['album'] == album ]
				except KeyError:
					tlist_album = tlist_artist
				tlist_album = sorted(tlist_album, key=lambda x: int(x.get('track', '0').split("/")[0]))
				for t in tlist_album:
					liclass = "" if t is not tlist_album[-1] else " class='last'"
					fn = t['file']
					ti = t.get("title", fn[:fn.rindex('.')].split("/")[-1])
					r += "<li" + liclass + "><a href='/addsong?song=\"" + t['file'] + "\"' target='_top'><img src='/img/add.png' alt='add' /></a> " + ti + "</li>"
				r += "</ul></li>"
			r += "</ul></li>"
		r += "</ul>"
		return self.surround_head_tags_basic(r)

# index html
	def index(self):
		s = self.c.currentsong()
		status = self.c.status()
		state = status["state"]
		t_elapsed, t_total = status["time"].split(":")
		if state == "play":
			ppbutton = "pause"
		else:
			ppbutton = "play"
		html = self.surround_head_tags("""
				<h1>{title}</h1>
				<h2>by <i>{artist}</i> from <i>{album}</i> {track}</h2>
				<div id='controlbar'>
					<div id='progressbarcontainer' onclick='do_seek(event)'>
						<div id='progressbartextlayer'>{timepos}</div>
						<div id='progressbar'>&nbsp;</div><div id='progressind'>&nbsp;</div>
					</div>
					<br />
					<a href='/prev'><img src='img/prev.png' /></a>
					<a href='/stop'><img src='img/stop.png' /></a>
					<a href='/{ppbutton}'><img src='img/{ppbutton}.png' /></a>
					<a href='/next'><img src='img/next.png' /></a>
				</div>
				<br>
				<ul class='tab'>
					<li><a href='/playlist' target='subframe'><img src='/img/current.png' /> playlist</a></li>
					<li><a href='/filetree' target='subframe'><img src='/img/browse.png' /> files</a></li>
					<li><a href='/albumtree' target='subframe'><img src='/img/cd24.png' /> albums</a></li>
					<li><a href='/artisttree' target='subframe'><img src='/img/artist24.png' /> artists</a></li>
					<li class='r'><a href='{jsupdatecall}' target='_top'><img src='/img/refresh.png' alt='update' /></a></li>
				</ul>
				<iframe class='subframe' name='subframe' width='100%' height='400px' src='/playlist'></iframe>
				<div id='copyright'><a href='http://hasj-kebab.blogspot.com/search/label/cherrypympc' target='_blank'>CherryPyMPC</a> v0.2 by SDC superb design+code</div>
		""", t_elapsed, t_total, s['pos'], (state=="play"))\
				.format(artist = s.get("artist", "Unknown Artist"),
					title = s.get("title", "Unknown Track"),
					album = s.get("album", "Unknown Album"),
					track = ( "(<i>" + s.get("track", "0") + "</i>)" ) if 'track' in s else "",
					ppbutton = ppbutton,
					timepos = SecToTimeString(t_elapsed) + " / " + SecToTimeString(t_total),
					jsupdatecall = "javascript:call=new XMLHttpRequest();call.open(\"GET\",\"/update\");call.onreadystatechange=function(){};call.send();")
		return html
	
# html encapsulation
	def surround_head_tags(self, innerhtml, secs_elapsed, secs_total, songpos, playing):
		return """
		<html>
			<head>
				<title>{artist} - {title} ({album}) - """ + self.__app__ + """</title>
				<!--<meta http-equiv='refresh' content='60'>!-->
				<link rel='stylesheet' href='style/style.css' type='text/css' />
				<script type='text/javascript' src='js/MochiKit.js'></script>
				<script type='text/javascript' src='js/script.js'></script>
			</head>
			<body class='main' onload='init_timebar(""" + secs_elapsed + "," + secs_total + "," + songpos + "," + ("true" if playing else "false") + """);'>""" + innerhtml + """
			</body>
		</html>"""
	
	def surround_head_tags_basic(self, innerhtml):
		return """
		<html>
			<head>
				<title>""" + self.__app__ + """</title>
				<link rel='stylesheet' href='style/style.css' type='text/css' />
			</head>
			<body class='subframe'>""" + innerhtml + """
			</body>
		</html>"""
	
# methods exposure to http request
	play.exposed = True
	pause.exposed = True
	stop.exposed = True
	next.exposed = True
	prev.exposed = True
	playno.exposed = True
	addsong.exposed = True
	seek.exposed = True
	update.exposed = True
	findadd.exposed = True

	playlist.exposed = True
	filetree.exposed = True
	albumtree.exposed = True
	artisttree.exposed = True

	index.exposed = True

# run cherrypy
if __name__ == "__main__":
	current_dir = os.path.dirname(os.path.abspath(__file__))
	conf = { '/img': { "tools.staticdir.on": True,
					   "tools.staticdir.dir": os.path.join(current_dir, "img") },
		     '/style': { "tools.staticdir.on": True,
					   "tools.staticdir.dir": os.path.join(current_dir, "style") },
		     '/js': { "tools.staticdir.on": True,
					   "tools.staticdir.dir": os.path.join(current_dir, "js") },
			 '/favicon.ico': { "tools.staticfile.on": True,
				 		"tools.staticfile.filename": os.path.join(current_dir, "img", "favicon.ico") }
			}
	mpcweb = MPCWebSimple(host="localhost", port="6600", passw="ptfmwb")
	cherrypy.quickstart(mpcweb, '/', config=conf)

# vim: ts=4 sw=4 noet
