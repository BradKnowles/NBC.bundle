NAME = 'NBC'
ART = 'art-default.jpg'
ICON = 'icon-default.jpg'

SHOWS_URL = 'http://tveatc-usa.nbcuni.com/awe3/live/5/nbce/containers/iPadRetina'
SECTIONS_URL = 'http://tveatc-usa.nbcuni.com/awe3/live/5/nbce/asset/iPadRetina/%s'
VIDEOS_URL = 'http://tveatc-usa.nbcuni.com/awe3/live/5/nbce/containers/iPadRetina/%s?seasonNumber=%s&filterBy=%s'

VIDEO_URL = 'http://www.nbc.com/%s/video/%s/%s#%s|%s' # show, title, short episode_id, show_id, long episode_id

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'BRNetworking/2.7.0.1449 (iPad;iPhone OS-8.1)'

####################################################################################################
@handler('/video/nbc', NAME, art=ART, thumb=ICON)
def Shows():

	oc = ObjectContainer()

	for show in JSON.ObjectFromURL(SHOWS_URL)['results']:

		show_id = show['assetID']
		title = show['title']
		summary = show['description']

		try:
			thumb = show['images'][0]['images']['show_thumbnail_16_by_9']
		except:
			thumb = ''

		oc.add(DirectoryObject(
			key = Callback(Sections, show_id=show_id, show=title),
			title = title,
			summary = summary,
			thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=ICON)
		))

	oc.objects.sort(key=lambda obj: Regex('^The ').split(obj.title)[-1])
	return oc

####################################################################################################
@route('/video/nbc/{show_id}/sections')
def Sections(show_id, show):

	oc = ObjectContainer(title2=show)
	json_obj = JSON.ObjectFromURL(SECTIONS_URL % (show_id))

	try:
		thumb = json_obj['images'][0]['images']['show_thumbnail_16_by_9'] 
	except:
		thumb = ''

	has_episodes = False
	has_clips = False

	for season in json_obj['seasons']:

		if season['hasEpisodes']:
			has_episodes = True

		if season['hasClips']:
			has_clips = True

	if has_episodes:

		oc.add(DirectoryObject(
			key = Callback(Seasons, show_id=show_id, show=show, filter_by='episode'),
			title = 'Full Episodes',
			thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=ICON)
		))

	if has_clips:

		oc.add(DirectoryObject(
			key = Callback(Seasons, show_id=show_id, show=show, filter_by='clip'),
			title = 'Clips',
			thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=ICON)
		))

	return oc

####################################################################################################
@route('/video/nbc/{show_id}/{filter_by}/seasons')
def Seasons(show_id, show, filter_by):

	oc = ObjectContainer(title2=show)
	json_obj = JSON.ObjectFromURL(SECTIONS_URL % (show_id))

	try:
		thumb = json_obj['images'][0]['images']['show_thumbnail_16_by_9'] 
	except:
		thumb = ''

	for season in json_obj['seasons']:

		if filter_by == 'episode' and season['hasEpisodes']:

			oc.add(DirectoryObject(
				key = Callback(Videos, show_id=show_id, show=show, filter_by='episode', season=season['number']),
				title = 'Season %s' % (season['number']),
				thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=ICON)
			))

		elif filter_by == 'clip' and season['hasClips']:

			oc.add(DirectoryObject(
				key = Callback(Videos, show_id=show_id, show=show, filter_by='clip', season=season['number']),
				title = 'Season %s' % (season['number']),
				thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=ICON)
			))

	return oc

####################################################################################################
@route('/video/nbc/{show_id}/{filter_by}/{season}/videos')
def Videos(show_id, show, filter_by, season):

	oc = ObjectContainer(title2=show)

	for episode in JSON.ObjectFromURL(VIDEOS_URL % (show_id, season, filter_by))['results']:

		if episode['requiresAuth']:
			continue

		episode_id = episode['assetID']

		# Get show directory of url
		parent_id = episode['parentContainerId']

		title = episode['title']

		# Remove parenthesis, apsotrophe, question mark, comma, period, dash, and colon from title for url build
		url_title = title.replace("(", "").replace(")", "").replace("'", "").replace('?', '').replace(',', '').replace('-', '').replace('.', '').replace(":", "")

		# Change title spaces and slashes to dashes and make lowercase for url build
		url_title = url_title.replace('/', '-').replace(' ', '-').lower()

		url = VIDEO_URL % (parent_id, url_title, episode_id.split('_')[-1], show_id, episode_id)
		url = String.StripDiacritics(url)

		try: ep_index = int(episode['episodeNumber'])
		except: ep_index = None

		try: thumb = episode['images'][0]['images']['video_detail_16_by_9']
		except: thumb = ''

		oc.add(EpisodeObject(
			url = url,
			show = show,
			title = title,
			summary = episode['description'],
			thumb = Resource.ContentsOfURLWithFallback(url=thumb),
			season = int(episode['seasonNumber']),
			index = ep_index,
			duration = episode['totalDuration'],
			originally_available_at = Datetime.FromTimestamp(episode['firstAiredDate'])
		))

	return oc
