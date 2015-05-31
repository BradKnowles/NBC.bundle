SHOWS_URL = 'http://tve-atcnbce.nbcuni.com/live/3/nbce/containers/iPad'
EPISODES_URL = 'http://tve-atcnbce.nbcuni.com/live/3/nbce/containers/%s/iPad?filterBy=episode'
VIDEO_URL = 'http://www.nbc.com/%s/video/%s/%s#%s|%s' # show, title, short episode_id, show_id, long episode_id

####################################################################################################
def Start():

	ObjectContainer.title1 = 'NBC'
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'BRNetworking/2.7.0.1449 (iPad;iPhone OS-8.1)'

####################################################################################################
@handler('/video/nbc', 'NBC')
@route('/video/nbc/shows')
def Shows():

	oc = ObjectContainer()

	if not Client.Platform in ('Android', 'iOS', 'Roku', 'Safari'):
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

	oc.objects.sort(key=lambda obj: obj.title)
	return oc

####################################################################################################
@route('/video/nbc/episodes/{show_id}')
def Episodes(show_id, show):

	oc = ObjectContainer(title2=show)

	for episode in JSON.ObjectFromURL(EPISODES_URL % show_id)['results']:

		if episode['type'] != 'video' or episode['subtype'] != 'episode' or 'seasonNumber' not in episode or episode['requiresAuth']:
			continue

		episode_id = episode['assetID']
		title = episode['title']
		url = VIDEO_URL % (show.replace(' ', '-').lower(), title.replace(' ', '-').replace('/', '-').replace('?', '').lower(), episode_id.split('_')[-1], show_id, episode_id)
		url = String.StripDiacritics(url)
		try: ep_index = int(episode['episodeNumber'])
		except: ep_index = None

		oc.add(EpisodeObject(
			url = url,
			show = show,
			title = title,
			summary = episode['description'],
			thumb = Resource.ContentsOfURLWithFallback(episode['images'][0]['images']['episode_banner']),
			season = int(episode['seasonNumber']),
			index = ep_index,
			duration = episode['totalDuration'],
			originally_available_at = Datetime.FromTimestamp(episode['firstAiredDate'])
		))

	return oc
