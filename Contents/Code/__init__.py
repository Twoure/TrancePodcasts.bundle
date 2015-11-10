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

    oc.add(DirectoryObject(
        key=Callback(AudioList,
            title='Aly & Fila - Future Sound Of Egypt', page=0,
            rssfeed='http://www.fsoe-recordings.com/fsoepodcast/fsoepod.xml'),
        title='Aly & Fila - Future Sound Of Egypt'))
    oc.add(DirectoryObject(
        key=Callback(AudioList,
            title='International Departures Podcast with Myon & Shane 54', page=0,
            rssfeed='http://www.myonandshane54.com/id/idpodcast.xml'),
        title='International Departures Podcast with Myon & Shane 54'))
    oc.add(DirectoryObject(
        key=Callback(AudioList,
            title='A State of Trance Official Podcast', page=0,
            rssfeed='http://podcast.armadamusic.com/asot/podcast.xml'),
        title='A State of Trance Official Podcast'))
    oc.add(DirectoryObject(
        key=Callback(AudioList,
            title='Global DJ Broadcast', page=0,
            rssfeed='http://feeds.feedburner.com/MarkusSchulzGlobalDJBroadcast?format=xml'),
        title='Global DJ Broadcast'))
    oc.add(DirectoryObject(
        key=Callback(AudioList,
            title='Paul van Dyk\'s VONYC Sessions Podcast', page=0,
            rssfeed='http://podcast.paulvandyk.com/feed.xml'),
        title='Paul van Dyk\'s VONYC Sessions Podcast'))
    oc.add(DirectoryObject(
        key=Callback(AudioList,
            title='Perfecto Podcast: featuring Paul Oakenfold', page=0,
            rssfeed='http://oakenfold.libsyn.com/rss'),
        title='Perfecto Podcast: featuring Paul Oakenfold'))
    oc.add(DirectoryObject(
        key=Callback(AudioList,
            title='Andy Moor\'s Moor Music Podcast', page=0,
            rssfeed='http://www.andymoor.com/moormusic.rss'),
        title='Andy Moor\'s Moor Music Podcast'))
    oc.add(PrefsObject(title='Preferences'))

    return oc

####################################################################################################
@route(PREFIX + '/audiolist', page=int, count=int)
def AudioList(title, rssfeed, page, count=0, header=None, message=None):
    # setup items_per_page based off prefs
    page_count = Prefs['page_count']
    if page_count == 'All':
        items_per_page = 1
        count_prefs = False
    else:
        count_prefs = True
        items_per_page = int(page_count)

    if page == 0:
        # get RSS as feed object, using feedparser
        feed = RSS.FeedFromURL(rssfeed)

        # check if the url is under Maintenance
        check_text = feed['feed']['summary']
        if 'Web Maintenance' in check_text:
            return MessageContainer('Warning', '%s Currently under "Web Maintenance"' %rssfeed)
        else:
            Log('saving RSS Feed object to Data')
            # save feed as python object so we can re-call feed for next page
            Data.SaveObject(title, feed)
    else:
        Log('loading RSS Feed object from Data')
        # load in our saved feed object for next page
        feed = Data.LoadObject(title)

    # setup container title
    entry_list = feed.entries
    total_count = len(entry_list)
    total_pages = int(total_count/items_per_page) + 1
    main_title = title
    if not total_pages == total_count and total_count > items_per_page:
        shift_page = page + 1
        if shift_page < total_pages:
            main_title = '%s | Page %i of %i' %(title, shift_page, total_pages)
        elif shift_page == total_pages:
            main_title = '%s | Page %i, Last Page' %(title, shift_page)

    oc = ObjectContainer(title2=main_title, header=header, message=message)

    next_pg = None
    # Get Sublist of entry_list based on paging
    if page == 0:
        count = total_count
        Log('entry list total count = %i' %total_count)
        # setup first page
        # check Prefs['page_count'] for valid #
        #   if "All" and not #, then return entire list and no next pg container
        if total_count > items_per_page and count_prefs:
            next_pg = page + 1
            new_count = total_count - items_per_page
            entry_list = entry_list[0:items_per_page]
    # setup pages after first page, but not last page
    elif count > items_per_page and page > 0:
        Log('entry list new count = %i' %count)
        if page == 1:
            start_num = items_per_page
        else:
            start_num = items_per_page * page
        end_num = start_num + items_per_page
        next_pg = page + 1
        new_count = count - items_per_page
        entry_list = entry_list[start_num:end_num]
    # setup last page
    elif page > 0:
        Log('string cut = [%i:%i]' %(count, total_count))
        entry_list = entry_list[total_count - count:total_count]

    # pull out feed title and thumb for global settings
    feed_title = feed['feed']['title']
    main_thumb = feed['feed']['image']['href']

    # parse entries for episodes and corresponding metadata
    for item in entry_list:
        item_keys = item.keys()
        url = item.enclosures[0]['url']
        title_text = item.title
        item_title = title_text.replace(feed_title, '').lstrip(': ')

        # clean episode titles
        if feed_title == title:
            if 'Paul Oakenfold:' in item_title:
                test = Regex('(Episode\ .+)').search(item_title)
                if test:
                    item_title = test.group(1).strip()
            else:
                item_title = item_title.replace('Planet Perfecto Podcast', 'Episode').strip()
        elif feed_title == title:
            item_title = 'Episode ' + item_title
        elif feed_title == title:
            test = Regex('(Episode\ .+)').search(item_title)
            if test:
                item_title = test.group(1).strip()
        elif feed_title == title:
            test = Regex('(\d+)').search(item_title)
            if test:
                item_title = 'Episode ' + test.group(1).lstrip('0 ').strip()

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
            if feed_title == title:
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
            'title': item_title, 'artist': artist, 'summary': summary, 'thumb': thumb,
            'oaa_date': originally_available_at, 'duration': duration, 'album': feed_title,
            'genres': genres, 'url': url
            }

        # www.moormusic.info URL is offline, they moved to moormusic.co, but not all ep are hosted
        # this will weed out the old URL host
        if not 'www.moormusic.info' in url:
            oc.add(CreateTrackObject(item_info=item_info))

    if not len(oc) > 0 and next_pg:
        header = title
        message = 'Skipping Page(s), No Valid Episode URL\'s'
        return AudioList(title=title, rssfeed=rssfeed, page=next_pg, count=new_count, header=header, message=message)

    if next_pg:
        oc.add(NextPageObject(
            key=Callback(AudioList, title=title, rssfeed=rssfeed, page=next_pg, count=new_count),
            title='Next Page>>'))

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
                audio_channels=2,
                optimized_for_streaming=True if Client.Product != 'Plex Web' else False
                )
            ]
        )

    if include_container:
        return ObjectContainer(objects=[track_object])
    else:
        return track_object
