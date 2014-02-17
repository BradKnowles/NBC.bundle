# LATE NIGHT WITH JIMMY FALON USES OLD FORMAT

BASE_URL = 'http://www.nbc.com'

# This is the json document for the main links and pull down menus at the top of each page on the site
SECTION_CAROUSEL = "http://www.nbc.com/data/node/%s/video_carousel"

# Variables for old format 
RE_THUMB_SIZE = Regex('w=[0-9]+&h=[0-9]+')
RE_BASE_URL = Regex('(http://[^/]+)')

####################################################################################################
def Start():

	ObjectContainer.title1 = 'NBC'
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:26.0) Gecko/20100101 Firefox/26.0'

####################################################################################################
@handler('/video/nbc', 'NBC')
def MainMenu():

	oc = ObjectContainer()

	if not Client.Platform in ('Android', 'iOS', 'Roku', 'Safari', 'Firefox', 'Chrome', 'Windows', 'Windows Phone'):
		oc.header = 'Not supported'
		oc.message = 'This channel is not supported on %s' % (Client.Platform if Client.Platform is not None else 'this client')
		return oc

	oc.add(DirectoryObject(key=Callback(Section, title='Current shows'), title='Current Shows'))
	oc.add(DirectoryObject(key=Callback(Section, title='Classics'), title='Classics'))

	return oc

####################################################################################################
# This function creates a list of shows and icons for both current and classic shows using the show page
@route('/video/nbc/section')
def Section(title):

	oc = ObjectContainer(title2=title)
	# Here we form the video page and show page url for current shows and classics
	if 'Current' in title:
		all_url = BASE_URL + '/video'
		local_url = BASE_URL + '/shows/current'
	else:
		all_url = BASE_URL + '/video/classics'
		local_url = BASE_URL + '/shows/classic'
	# This takes you to the video or classic video page to get the latest videos
	oc.add(DirectoryObject(key=Callback(Show, show='Latest Videos', url=all_url), title='Latest Videos'))
	html = HTML.ElementFromURL(local_url)

	# List is shwoing up blank
	for show in html.xpath('//div[contains(@class,"shows_grid")]/div/a'):
		url = show.xpath('./@href')[0]
		# They do not give a title and the @title and @alt for images can contain summary or art references
		# So instead we are converting the url to the title. Classic TV shows have a subfolder '/classic-tv' in the url
		title_list = url.split('/')
		title = title_list[len(title_list)-1].replace('-', ' ').title()
		if not url.startswith('http://'):
			url = BASE_URL + url
		thumb = show.xpath('./img/@src')[0]

		oc.add(DirectoryObject(key=Callback(Show, show=title, url=url+'/video', thumb=thumb), title=title, thumb=thumb))

	return oc

####################################################################################################
# This function creates the sections of videos for each shows video page
# It pulls the carousel id number and uses it to create the carousel's json url  
@route('/video/nbc/show')
def Show(show, url, thumb=''):

	oc = ObjectContainer(title2=show)

	html = HTML.ElementFromURL(url)

	for category in html.xpath('//div[contains(@id,"nbc_mpx_carousel")]'):
		carousel_id = category.xpath('./@id')[0].split('carousel_')[1]
		car_url = SECTION_CAROUSEL %carousel_id
		# They break up the title into parts and some only have one part that may be in a span tag or may not be
		# So we create it as a list and join it. Because text tag can be h2 or h1, look for pane-title class
		title_list = category.xpath('.//*[@class="pane-title"]//text()')
		cat_title = ''.join(title_list).replace('  ', ' ').strip()
		# Some symbols are not translated so we have to do that manually 
		cat_title = String.DecodeHTMLEntities(cat_title)

		oc.add(DirectoryObject(
			key = Callback(Episodes, show=show, title=cat_title, url=car_url),
			title = cat_title,
			thumb = thumb
		))

	# We try to see if those with not videos will work with the old setup
	if len(oc) < 1:
		# Late Night with Jimmy Fallon still uses the old format
		if 'jimmy-fallon' in url:
			new_url = html.xpath('//meta[@property="og:url"]/@content')[0]
			oc.add(DirectoryObject(key=Callback(ShowOld, show=show, url=new_url), title=show))
		else:
			Log('Still no value for show')
			return ObjectContainer(header='Empty', message='This directory is empty')

	return oc

####################################################################################################
# This function creates a list of videos from the carousels json file for each video section of a show 
@route('/video/nbc/episodes')
def Episodes(show, title, url):

	oc = ObjectContainer(title1=show, title2=title)
	json = JSON.ObjectFromURL(url)

	for video in json['entries']:
		vid_url = BASE_URL + video['link']
		summary = String.DecodeHTMLEntities(video['description'])
		title = String.DecodeHTMLEntities(video['title'])
		date = Datetime.FromTimestamp(video['pubDate'] / 1000)
		# Not all have an episode number. But all have a season
		season = int(video['pl1$seasonNumber'])
		try: episode = int(video['pl1$episodeNumber'])
		except: episode = None
		thumb = video['plmedia$defaultThumbnailUrl']['big']

		oc.add(EpisodeObject(
			url = vid_url,
			season = season,
			index = episode,
			summary = summary,
			title = title,
			originally_available_at = date,
			#### thumb = Resource.ContentsOfURLWithFallback(url=thumb)
			thumb = thumb
		))

	if len(oc) < 1:
		return ObjectContainer(header='Empty', message='This directory is empty')

	return oc

####################################################################################################
# Late Night with Jimmy Fallon still uses the old format
@route('/video/nbc/showold')
def ShowOld(show, url):

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
			key = Callback(EpisodesOld, show=show, title=title, url=url, base=base),
			title = title
		))

	if len(oc) < 1:
		return ObjectContainer(header='Empty', message='This directory is empty')

	return oc

####################################################################################################
# Late Night with Jimmy Fallon still uses the old format
@route('/video/nbc/episodesold')
def EpisodesOld(show, title, url, base):

	oc = ObjectContainer(title1=show, title2=title)
	content = HTML.ElementFromURL(url)

	for episode in content.xpath('//div[contains(@class, "thumb-view")]//div[contains(@class, "thumb-block")]'):
		video_url = episode.xpath('./a/@href')[0]

		if video_url.find('http://') == -1:
			video_url = base + video_url

		episode_title = episode.xpath('.//div[@class="title"]')[0].text.strip()
		air_date = episode.xpath('./div[@class="meta"]/p')[0].text.split(': ', 1)[1]
		date = Datetime.ParseDate(air_date).date()
		thumb = episode.xpath('.//img/@src')[0]
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
		next_url = base + content.xpath('//div[@class="nbcu_pager"]//a[text()="Next"]/@href')[0]

		if next_url != url:
			oc.add(NextPageObject(key=Callback(Episodes, title=title, url=next_url, base=base), title='Next ...'))

	if len(oc) < 1:
		return ObjectContainer(header='Empty', message='This directory is empty')

	return oc
