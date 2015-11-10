TITLE = 'Trance Podcasts'
PREFIX = '/music/trancepodcasts'
ART = "art-default.jpg"
ICON = "icon-default.png"

####################################################################################################
def Start():
    ObjectContainer.title1 = TITLE
    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    PopupDirectoryObject.thumb = R(ICON)
    PopupDirectoryObject.art = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art = R(ART)
    HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
@handler(PREFIX, TITLE)
def MainMenu():
    oc = ObjectContainer()
    #Template:          AddAudioMenuItem(oc, '', '')

    AddAudioMenuItem(oc, 'Aly & Fila - Future Sound Of Egypt', 'http://www.fsoe-recordings.com/fsoepodcast/fsoepod.xml')
    AddAudioMenuItem(oc, 'International Departures Podcast with Myon & Shane 54', 'http://www.myonandshane54.com/id/idpodcast.xml')
    AddAudioMenuItem(oc, 'A State of Trance Official Podcast', 'http://podcast.armadamusic.com/asot/podcast.xml')
    AddAudioMenuItem(oc, 'Global DJ Broadcast', 'http://feeds.feedburner.com/MarkusSchulzGlobalDJBroadcast?format=xml')
    AddAudioMenuItem(oc, "Paul van Dyk's VONYC Sessions Podcast", 'http://podcast.paulvandyk.com/feed.xml')
    AddAudioMenuItem(oc, 'Perfecto Podcast: featuring Paul Oakenfold', 'http://oakenfold.libsyn.com/rss')
    AddAudioMenuItem(oc, "Andy Moor's Moor Music Podcast", 'http://www.andymoor.com/moormusic.rss')

    return oc

####################################################################################################
@route(PREFIX + '/add-audio-menu-item')
def AddAudioMenuItem(oc, titleString, rssfeedString):
    oc.add(DirectoryObject(
        key=Callback(GenerateAudioMenu, title=titleString, rssfeed=rssfeedString),
        title=titleString))

    return oc

####################################################################################################
@route(PREFIX + '/generate-audio-menu')
def GenerateAudioMenu(title, rssfeed):
    oc = ObjectContainer(title1=title)

    feed = RSS.FeedFromURL(rssfeed)
    AddItemsToContainer(oc, feed) #TODO could do a pagination, a feed can hold too many items to load quickly.

    return oc

####################################################################################################
@route(PREFIX + '/add-items-to-container')
def AddItemsToContainer(oc, feed):
    # pull out feed title and thumb for global settings
    feed_title = feed['feed']['title']
    Log(feed_title)
    main_thumb = feed['feed']['image']['href']

    # parse entries for episodes and corresponding metadata
    for item in feed.entries:
        item_keys = item.keys()
        url = item.enclosures[0]['url']
        title_text = item.title
        title = title_text.replace(feed_title, '').lstrip(': ')

        # clean episode titles
        if feed_title == 'Perfecto Podcast: featuring Paul Oakenfold':
            if 'Paul Oakenfold:' in title:
                test = Regex('(Episode\ .+)').search(title)
                if test:
                    title = test.group(1).strip()
            else:
                title = title.replace('Planet Perfecto Podcast', 'Episode').strip()
        elif feed_title == 'Aly & Fila - Future Sound Of Egypt':
            title = 'Episode ' + title
        elif feed_title == 'Andy Moor\'s Moor Music Podcast':
            test = Regex('(Episode\ .+)').search(title)
            if test:
                title = test.group(1).strip()
        elif feed_title == 'Paul van Dyk\'s VONYC Sessions Podcast':
            test = Regex('(\d+)').search(title)
            if test:
                title = 'Episode ' + test.group(1).lstrip('0 ').strip()

        # find ep thumb, if not then use global thumb
        if 'image' in item_keys:
            thumb = item['image']['href']
        else:
            thumb = main_thumb

        # setup artist and genres if included
        artist = None
        genres = []
        if 'author' in item_keys:
            artist = item['author']
            if feed_title == 'Paul van Dyk\'s VONYC Sessions Podcast':
                test = Regex('(.*)\(').search(artist)
                if test:
                    artist = test.group(1).strip()

        if 'tags' in item_keys:
            genres = [t['term'] for t in item['tags']]

        # test summary for html format
        summary_text = item.summary
        if summary_text:
            summary_node = HTML.ElementFromString(summary_text)
            summary = String.StripTags(summary_node.text_content())
        else:
            summary = None

        #leave as string, cannot propagate datetime objects between functions
        originally_available_at = item.updated
        # ep duration in milliseconds
        duration = Datetime.MillisecondsFromString(item.itunes_duration)

        item_info = {
            'title': title, 'artist': artist, 'summary': summary, 'thumb': thumb,
            'oaa_date': originally_available_at, 'duration': duration, 'album': feed_title,
            'genres': genres, 'url': url
            }

        # www.moormusic.info URL is offline, they moved to moormusic.co, but not all ep are hosted
        # this will weed out the old URL host
        if not 'www.moormusic.info' in url:
            oc.add(CreateTrackObject(item_info=item_info))

    return oc

####################################################################################################
@route(PREFIX + '/create-track-object', item_info=dict)
def CreateTrackObject(item_info, include_container=False):

    if item_info['url'].endswith('.mp3'):
        container = Container.MP3
        audio_codec = AudioCodec.MP3
    else:
        container = Container.MP4
        audio_codec = AudioCodec.AAC

    # some dates are formatted incorrectly, skip those we cannot parse
    try:
        date = Datetime.ParseDate(item_info['oaa_date'])
    except:
        date = None

    track_object = TrackObject(
        key=Callback(CreateTrackObject, item_info=item_info, include_container=True),
        rating_key=item_info['url'],
        title=item_info['title'],
        album=item_info['album'],
        artist=item_info['artist'],
        summary=item_info['summary'],
        genres=item_info['genres'],
        originally_available_at=date,
        duration=int(item_info['duration']),
        thumb=item_info['thumb'],
        art=R(ART),
        items=[
            MediaObject(
                parts=[PartObject(key=item_info['url'])],
                container=container,
                audio_codec=audio_codec,
                audio_channels=2
                )
            ]
        )

    if include_container:
        return ObjectContainer(objects=[track_object])
    else:
        return track_object
