BASE_URL = 'http://www.nbc.com'
CURRENT_SHOWS = '%s/video/library/full-episodes/' % BASE_URL
CLASSIC_TV = '%s/classic-tv/' % BASE_URL

# Thumbs
# %d = 360, or 480 for classic tv
# %s = 'nbc2', or 'nbcrewind2' for classic tv
# %s = pid
THUMB_URL = 'http://video.nbc.com/player/mezzanine/image.php?w=640&h=%d&path=%s/%s_mezzn.jpg&trusted=yes'

RE_BASE_URL = Regex('(http://[^/]+)')
RE_THUMB_SIZE = Regex('w=[0-9]+&h=[0-9]+')
RE_SHOW_ID = Regex('nbc.com/([^/]+)/')

####################################################################################################
def Start():

	ObjectContainer.title1 = 'NBC'
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:21.0) Gecko/20100101 Firefox/21.0'

####################################################################################################
@handler('/video/nbc', 'NBC')
def MainMenu():

	oc = ObjectContainer()

	if not Client.Platform in ('Android', 'iOS', 'Roku', 'Safari', 'Firefox', 'Chrome'):
		oc.header = 'Not supported'
		oc.message = 'This channel is not supported on %s' % (Client.Platform if Client.Platform is not None else 'this client')
		return oc

	oc.add(DirectoryObject(key=Callback(CurrentShows), title='Current Shows'))
	oc.add(DirectoryObject(key=Callback(ClassicTV), title='Classic TV'))

	return oc

####################################################################################################
@route('/video/nbc/currentshows')
def CurrentShows():

	oc = ObjectContainer(title2='Current Shows')
	show_ids = []
	content = HTML.ElementFromURL(CURRENT_SHOWS)

	for show in content.xpath('//div[contains(@class, "group-full-eps")]//li'):
		url = show.xpath('./a/@href')[0]
		if '/classic-tv/' in url:
			continue

		title = show.xpath('./p/text()')[0].strip()
		thumb = show.xpath('./a/img/@src')[0]

		id = RE_SHOW_ID.search(url)
		if id:
			show_ids.append(id.group(1))

		oc.add(DirectoryObject(
			key = Callback(Show, show=title, url=url, thumb=thumb),
			title = title,
			thumb = Resource.ContentsOfURLWithFallback(thumb)
		))

	# Try to find shows missing from the main video page
	try:
		content = HTML.ElementFromURL('http://www.nbc.com/assets/core/themes/2012/nbc/includes/auto-generated/dropdowns-global.shtml')

		for show in content.xpath('//li[text()="Current Shows"]/parent::ul/following-sibling::div//ul/li/a'):
			url = show.get('href')

			id = RE_SHOW_ID.search(url)
			if id:
				id = id.group(1)

			if id in show_ids:
				continue

			show_ids.append(id)
			url = '%s/video' % url.rstrip('/')

			if not show.text:
				continue

			title = show.text.strip()

			oc.add(DirectoryObject(key=Callback(Show, show=title, url=url), title=title))
	except:
		pass

	oc.objects.sort(key=lambda obj: obj.title.replace('The ', ''))
	return oc

####################################################################################################
@route('/video/nbc/classictv')
def ClassicTV():

	oc = ObjectContainer(title2='Classic TV')
	content = HTML.ElementFromURL(CLASSIC_TV)

	for show in content.xpath('//h2[text()="classic tv"]/following-sibling::div//div[@class="thumb-block"]'):
		url = show.xpath('.//a[contains(@href, "/classic-tv/") and contains(@href, "/video")]/@href')
		if len(url) < 1:
			continue

		url = url[0]
		title = show.xpath('.//div[@class="title"]/text()')[0].strip()
		thumb = show.xpath('.//img/@src')[0]
		thumb = thumb.replace('150x84xC', '640x360xC')

		oc.add(DirectoryObject(
			key = Callback(Show, show=title, url=url, thumb=thumb),
			title = title,
			thumb = Resource.ContentsOfURLWithFallback(thumb)
		))

	return oc

####################################################################################################
@route('/video/nbc/show')
def Show(show, url, thumb=None):

	oc = ObjectContainer(title2=show)

	try: base = RE_BASE_URL.search(url).group(1)
	except: base = BASE_URL

	if url.find('http://') == -1:
		url = base + url

	content = HTML.ElementFromURL(url)

	for category in content.xpath('//*[text()="Full Episodes" or text()="FULL EPISODES"]/following-sibling::ul[1]/li/a[contains(@href, "categories")]'):
		title = category.text.strip()
		url = category.get('href')

		if url.find('http://') == -1:
			url = base + url

		oc.add(DirectoryObject(
			key = Callback(Episodes, show=show, title=title, url=url, base=base),
			title = title,
			thumb = Resource.ContentsOfURLWithFallback(thumb)
		))

	if len(oc) == 0:
		return ObjectContainer(header='Empty', message='This directory is empty')

	return oc

####################################################################################################
@route('/video/nbc/episodes')
def Episodes(show, title, url, base):

	oc = ObjectContainer(title1=show, title2=title)
	content = HTML.ElementFromURL(url)

	for episode in content.xpath('//div[contains(@class, "thumb-view")]//div[contains(@class, "thumb-block")]'):
		video_url = episode.xpath('./a')[0].get('href')

		if video_url.find('http://') == -1:
			video_url = base + video_url

		episode_title = episode.xpath('.//div[@class="title"]')[0].text.strip()
		air_date = episode.xpath('./div[@class="meta"]/p')[0].text.split(': ', 1)[1]
		date = Datetime.ParseDate(air_date).date()
		thumb = episode.xpath('.//img')[0].get('src')
		thumb = RE_THUMB_SIZE.sub('w=640&h=360', thumb)

		oc.add(EpisodeObject(
			url = video_url,
			show = show,
			title = episode_title,
			originally_available_at = date,
			thumb = Resource.ContentsOfURLWithFallback(thumb)
		))

	# More than 1 page?
	if len(content.xpath('//div[@class="nbcu_pager"]')) > 0:
		next_url = base + content.xpath('//div[@class="nbcu_pager"]//a[text()="Next"]')[0].get('href')

		if next_url != url:
			oc.add(NextPageObject(key=Callback(Episodes, title=title, url=next_url, base=base), title='Next ...'))

	if len(oc) == 0:
		return ObjectContainer(header='Empty', mesage='This directory is empty')

	return oc
