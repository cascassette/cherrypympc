#!/usr/bin/env python2

def SecToTimeString(secstr):
	secs = int(secstr)
	xmin, xsec = divmod(secs, 60)
	if xmin < 60:
		return "%d:%02d" % ( xmin, xsec )
	else:
		xhour, xmin = divmod(xmin, 60)
		return "%d:%02d:%02d" % ( xhour, xmin, xsec )

def TreeList(full_list = []):
	"""Returns a list with a full easily traversable tree of all MPD music files

	Structure is as follows:
	- every dir is made of a list where item 0 is a dictionary of subdirectories,
	- and strings for the files
	every subdirectory is again a list where [0] is a dict of subdirs etc etc."""
	tree_list = [ {} ]
	for item in full_list:
		if item.find("/") is -1:
			tree_list.append(item)
		else:					# directory
			path = item.split("/")
			# find and/or build dir structure accordingly
			workingdir = tree_list
			for subdir in path[0:-1]:
				if not workingdir[0].has_key(subdir):
					workingdir[0][subdir] = [ {} ]
				workingdir = workingdir[0][subdir]
			workingdir.append(path[-1])
	return tree_list


# connection/unittest:
# careful. not up to date :)
if __name__ == "__main__":
	from mpd import MPDClient

	def PrettyPrintTreeList(tree_list, level=0):
		if len(tree_list) > 1:
			for filename in tree_list[1:]:
				print (level * "    ") + "*" + filename
		for subdir in tree_list[0].keys():
			print level * "    " + subdir + ">"
			PrettyPrintTreeList(tree_list[0][subdir], level+1)

	c = MPDClient()
	c.connect(host="localhost", port="6600")

	print "printing current playlist, artist - title (# from album)"
	plist = c.playlistinfo()
	for item in plist:
		print "{pos}: {artist} - {title} (#{track} from {album})".format(pos = item["pos"],
																	artist = item["artist"],
																	title = item["title"],
																	track = item["track"],
																	album = item["album"])

	print "grabbing entire MPD dir struct"
	flist = c.list('file')
	tlist = TreeList(flist)

	print "printing entire MPD dir struct"
	PrettyPrintTreeList(tlist)

# vim: ts=4 sw=4 noet
