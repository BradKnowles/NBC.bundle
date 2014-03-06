SHOWS_URL = 'http://tve-atcnbc.nbcuni.com/ep-live/2/nbce/shows/iPad'
EPISODES_URL = 'http://tve-atcnbc.nbcuni.com/ep-live/2/nbce/container/x/iPad/%s'
VIDEO_URL = 'http://www.nbc.com/%s/video/%s/%s#%s|%s' # show, title, short episode_id, show_id, long episode_id

####################################################################################################
def Start():

	ObjectContainer.title1 = 'NBC'
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.117 Safari/537.36'

####################################################################################################
@handler('/video/nbc', 'NBC')
@route('/video/nbc/shows')
def Shows():

	oc = ObjectContainer()

	if not Client.Platform in ('Android', 'iOS', 'Roku', 'Safari', 'Windows', 'Windows Phone'):
		oc.header = 'Not supported'
		oc.message = 'This channel is not supported on %s' % (Client.Platform if Client.Platform is not None else 'this client')
		return oc

	for show in JSON.ObjectFromURL(SHOWS_URL):
		show_id = show['assetID']
		title = show['title']
		summary = show['description']
		thumb = show['images'][0]['images']['show_tile']

		oc.add(DirectoryObject(
			key = Callback(Episodes, show_id=show_id, show=title),
			title = title,
			summary = summary,
			thumb = Resource.ContentsOfURLWithFallback(thumb)
		))

	return oc

####################################################################################################
@route('/video/nbc/episodes/{show_id}')
def Episodes(show_id, show):

	oc = ObjectContainer(title2=show)

	for episode in JSON.ObjectFromURL(EPISODES_URL % show_id)['assetsX']:

		if episode['type'] != 'video':
			continue

		episode_id = episode['assetID']
		title = episode['title']
		url = VIDEO_URL % (show.replace(' ', '-').lower(), title.replace(' ', '-').lower(), episode_id.split('_')[-1], show_id, episode_id)

		oc.add(EpisodeObject(
			url = url,
			show = show,
			title = title,
			summary = episode['description'],
			thumb = Resource.ContentsOfURLWithFallback(episode['images'][0]['images']['episode_banner']),
			season = int(episode['seasonNumber']),
			index = int(episode['episodeNumber']),
			duration = episode['totalDuration'],
			originally_available_at = Datetime.FromTimestamp(episode['firstAiredDate'])
		))

	return oc
