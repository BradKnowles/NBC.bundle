import re, time

####################################################################################################

TITLE  = 'NBC'
PREFIX = '/video/nbc'
ART    = 'art-default.jpg'
ICON   = 'icon-default.png'

BASE_URL     = 'http://www.nbc.com'
FULL_EPS_URL = '%s/video/library/full-episodes/' % BASE_URL

# Thumbs
# %d = 360 or 480 for classic tv
# %s = 'nbc2' or 'nbcrewind2' for classic tv
# %s = pid
THUMB_URL = 'http://video.nbc.com/player/mezzanine/image.php?w=640&h=%d&path=%s/%s_mezzn.jpg&trusted=yes'

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

  try:
    base = re.search('(http://[^/]+)', url).group(1)
  except:
    base = BASE_URL

  if url.find('http://') == -1:
    url = base + url

  content = HTML.ElementFromURL(url, errors='ignore')
  for category in content.xpath('//h3[text()="Full Episodes"]/following-sibling::ul[1]/li/a[contains(@href, "categories")]'):
    title = category.text.strip()
    url = base + category.get('href')

    dir.Append(Function(DirectoryItem(Episodes, title=title, thumb=Function(Thumb, url=thumb)), url=url, base=base))

  if len(dir) == 0:
    return MessageContainer('Empty', 'This directory is empty')

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

    thumb_url = episode.xpath('./a/img')[0].get('src')
    uri = re.search('\.com/(.+?)/thumb/(.+?)_large', thumb_url)
    path = uri.group(1)
    pid = uri.group(2)

    # Classic tv gets 4:3 AR thumbs, newer tv 16:9 AR
    classic_tv = False
    if url.find('classic-tv') != -1:
      classic_tv = True

    video_url = base + episode.xpath('./a')[0].get('href')

    dir.Append(WebVideoItem(video_url, title=title, subtitle=subtitle, summary=summary, thumb=Function(Thumb, path=path, pid=pid, classic_tv=classic_tv)))

  # More than 1 page?
  if len(content.xpath('//div[@class="nbcu_pager"]')) > 0:
    next_url = base + content.xpath('//div[@class="nbcu_pager"]//a[text()="Next"]')[0].get('href')

    if next_url != url:
      dir.Extend(Episodes(sender, next_url, base))

  if len(dir) == 0:
    return MessageContainer('Empty', 'This directory is empty')

  return dir

####################################################################################################

def Thumb(url=None, path=None, pid=None, classic_tv=False):
  if url == None:
    if classic_tv == True:
      url = THUMB_URL % (480, path, pid)
    else:
      url = THUMB_URL % (360, path, pid)

  try:
    data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
    return DataObject(data, 'image/jpeg')
  except:
    return Redirect(R(ICON))
