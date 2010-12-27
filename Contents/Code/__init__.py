import re, time

####################################################################################################

TITLE  = 'NBC'
PREFIX = '/video/NBC'
ART    = 'art-default.jpg'
ICON   = 'icon-default.png'

BASE_URL     = 'http://www.nbc.com'
FULL_EPS_URL = '%s/video/library/full-episodes/' % BASE_URL

####################################################################################################

def Start():
  Plugin.AddPrefixHandler(PREFIX, MainMenu, TITLE, ICON, ART)
  Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
  Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

  MediaContainer.title1 = TITLE
  MediaContainer.viewGroup = 'List'
  MediaContainer.art = R(ART)

  DirectoryItem.thumb = R(ICON)
  WebVideoItem.thumb  = R(ICON)

  HTTP.CacheTime = CACHE_1HOUR
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13'

####################################################################################################

def MainMenu():
  dir = MediaContainer()

  content = HTML.ElementFromURL(FULL_EPS_URL, errors='ignore')
  for show in content.xpath('//div[contains(@class, "group-full-eps")]//li'):
    title = show.xpath('./p/text()[last()]')[0].strip()
    url = show.xpath('./a')[0].get('href')
    thumb = show.xpath('./a/img')[0].get('src')

    dir.Append(Function(DirectoryItem(Show, title=title, thumb=Function(Thumb, url=thumb)), url=url, thumb=thumb))

  return dir

####################################################################################################

def Show(sender, url, thumb):
  dir = MediaContainer(title2=sender.itemTitle)

  if url.find(BASE_URL) == -1:
    base = re.search('(http://[^/]+)', url).group(1)
  else:
    base = BASE_URL

  content = HTML.ElementFromURL(url, errors='ignore')
  for category in content.xpath('//h3[text()="Full Episodes"]/following-sibling::ul[1]/li/a'):
    title = category.text.strip()
    url = base + category.get('href')

    dir.Append(Function(DirectoryItem(Episodes, title=title, thumb=Function(Thumb, url=thumb)), url=url, base=base))

  return dir

####################################################################################################

def Episodes(sender, url, base):
  dir = MediaContainer(title2=sender.itemTitle, viewGroup='InfoList')

  content = HTML.ElementFromURL(url, errors='ignore')
  for episode in content.xpath('//li[@class="list_full_detail_horiz"]'):
    title = episode.xpath('.//p[@class="list_full_det_title"]//a')[0].text.strip()
    summary = episode.xpath('.//p[@class="list_full_des"]//text()')[0]

    try:
      airdate = episode.xpath('./div[@class="list_full_det_time"]/p[1]/text()')[0].strip()
      date = time.strptime(airdate, '%m/%d/%y')
      subtitle = time.strftime('%a, %d %b %Y', date)
    except:
      subtitle = None

    thumb = episode.xpath('./a/img')[0].get('src')
    video_url = base + episode.xpath('./a')[0].get('href')

    dir.Append(WebVideoItem(video_url, title=title, subtitle=subtitle, summary=summary, thumb=Function(Thumb, url=thumb)))

  # More than 1 page?
  if len(content.xpath('//div[@class="nbcu_pager"]')) > 0:
    next_url = base + content.xpath('//div[@class="nbcu_pager"]//a[text()="Next"]')[0].get('href')

    if next_url != url:
      dir.Extend(Episodes(sender, next_url, base))

  return dir

####################################################################################################

def Thumb(url):
  try:
    data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
    return DataObject(data, 'image/jpeg')
  except:
    return Redirect(R(ICON))
