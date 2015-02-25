# -*- coding: utf-8 -*-
import soundcloud
import praw
import datetime
import logging
import requests
import sys
import pytz
import isoweek
import spotipy
import spotipy.util
import re
import time
import dateutil
import dateutil.parser

import warnings
#soundcloud sends tons of these..
warnings.filterwarnings("ignore", category=ResourceWarning)

FORMAT = '%(asctime)-15s %(levelname)-6s %(message)s'
DATE_FORMAT = '%b %d %H:%M:%S'
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)

handler = logging.StreamHandler()
handler.setFormatter(formatter)
fhandler = logging.FileHandler('/home/ubuntu/hearddit.log')
fhandler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.addHandler(fhandler)
logger.setLevel(logging.INFO)

def get_submissions(subreddit='electronicmusic',limit=100,session=None):
    if not session:
        r = praw.Reddit(user_agent='get_top; subreddit={0}'.format(subreddit))
    else:
        r = session
    sr = r.get_subreddit(subreddit).get_hot(limit=limit)
    return sr

def add_url_to_submissions_db(url, dbfname='/home/ubuntu/hearddit_submitted_links.txt'):
    with open(dbfname, 'a') as fout:
        fout.write(url + '\n')
    return

def url_was_already_submitted(url, dbfname='/home/ubuntu/hearddit_submitted_links.txt'):
    with open(dbfname, 'r') as fin:
        lines = [line.rstrip() for line in fin]
    return (url in lines)

def check_reposts_and_submit_url(creds_file, subreddit, title, playlist_url, username='heardditbot'):
    with open(creds_file,'r') as fin:
        d = dict( l.rstrip().split('=') for l in fin)
    r = praw.Reddit(user_agent='post_link; subreddit={0}'.format(subreddit))
    r.login(username=username,password=d[username])
    assert r.is_logged_in()

    submission_hash = playlist_url+'\t'+title

    logger.info("url_was_already_submitted: {}".format(url_was_already_submitted(submission_hash)))
    if not url_was_already_submitted(submission_hash):
        submission = r.submit(subreddit,title=title,url=playlist_url)
        add_url_to_submissions_db(submission_hash)
        submission.add_comment('''Hearddit builds playlists from links posted on music subreddits. Details: http://ryancompton.net/2014/12/23/hearddit/ ''')

    return

def soundcloud_login():
    with open('/home/ubuntu/soundcloud_creds.properties','r') as fin:
        d = dict( l.rstrip().split('=') for l in fin)
    client = soundcloud.Client(client_id=d['client_id'],
                            client_secret=d['client_secret'],
                            username=d['username'],
                           password=d['password'])
    return client

def create_soundcloud_playlist_from_urls(urls, playlist_name):
    """
    login to soundcloud and create a playlist on my account
    """
    client = soundcloud_login()

    #use soundcloud api to resolve links
    tracks = []
    for url in urls:
        if 'soundcloud' in url:
            logger.debug(url)
            try:
                tracks.append(client.get('/resolve', url=url))
            except requests.exceptions.HTTPError:
                logger.warning('soundcloud url not resolved: '+url)
    track_ids = [x.id for x in tracks]
    track_dicts = list(map(lambda id: dict(id=id), track_ids))
    logger.info("soundcloud track_dicts: {}".format(track_dicts))

    #get my playlists (this will 504 if I have too many playlists)
    logger.info('client.get(/me/playlists), will 504 if I have too many playlists')
    my_playlists = client.get('/me/playlists')

    #delete old playlists
    max_playlist_age = 21
    logger.info('delete playlists older than {} days'.format(max_playlist_age))
    dto = datetime.datetime.now() - datetime.timedelta(max_playlist_age)
    expired_pls = [pl for pl in my_playlists if
        dateutil.parser.parse(pl.fields()['created_at']).replace(tzinfo=None) < dto]
    for expired_pl in expired_pls:
        logger.warning('delete playlist {}'.format(expired_pl.uri))
        client.delete(expired_pl.uri)
    logger.info('done clearing expired playlists')

    #focus attention on new lists only
    my_playlists = [pl for pl in my_playlists if
        dateutil.parser.parse(pl.fields()['created_at']).replace(tzinfo=None) >= dto]

    #existing list urls
    old_list_urls = [p for p in my_playlists if p.fields()['title'] == playlist_name]
    if old_list_urls:
        # add tracks to playlist
        old_list_url = old_list_urls[0]
        client.put(old_list_url.uri, playlist={'tracks': track_dicts})
    else:
        # create the playlist
        client.post('/playlists', playlist={
            'title': playlist_name,
            'sharing': 'public',
            'tracks': track_dicts})

    #get the link to the list created
    logger.info('client.get(/me/playlists), will 504 if I have too many playlists')
    my_playlists = client.get('/me/playlists')
    new_list_url = [p.fields()['permalink_url'] for p in my_playlists
                    if p.fields()['title'] == playlist_name]

    if new_list_url:
        return new_list_url[0]
    else:
        logger.warning('no new soundcloud list')
    return

def spotify_login():
    scopes = 'playlist-modify-public'
    with open('/home/ubuntu/my_spotify_api_key.properties','r') as fin:
        d = dict( l.rstrip().split('=') for l in fin)
    token = spotipy.util.prompt_for_user_token(username='1210400091',
        scope=scopes,
        client_id=d['SPOTIPY_CLIENT_ID'],
        client_secret=d['SPOTIPY_CLIENT_SECRET'],
        redirect_uri=d['SPOTIPY_REDIRECT_URI']
        )
    logger.warning('got spotify token: {}'.format(token))

    return spotipy.Spotify(auth=token)

def search_spotify_for_a_title(title, sp):
    query = re.split('(\[|\()',title)[0] # title.split('[')[0]

    if len(query) > 5:  # search for 5+ char strings
        results = sp.search(q=query, type='track')
        if len(results['tracks']['items']) > 0:
            #check that the artist and title are indeed part of the query (Spotify's search is to aggressive with matches)
            hit_artist = results['tracks']['items'][0]['artists'][0]['name']
            hit_title = results['tracks']['items'][0]['name']
            if (hit_artist.lower() in query.lower()) and (hit_title.lower() in query.lower()):
                logger.info('hit accepted: query={0} \t title={1} \t artist={2}'.format(query, hit_title, hit_artist))
            else:
                logger.info('hit rejected: query={0} \t title={1} \t artist={2}'.format(query, hit_title, hit_artist))
            return results
        else:
            logger.debug('miss! {0}'.format(query))
    return

def create_spotify_playlist_from_titles(todays_titles, playlist_name):
    """
    login to spotify, search for titles, and create a playlist
    """
    logger.info("create_spotify_playlist_from_titles")
    sp = spotify_login()

    #try to map the submission titles to spotify tracks
    search_results = [search_spotify_for_a_title(x,sp) for x in todays_titles]
    search_results = [x for x in search_results if x and (len(x['tracks']['items']) > 0)]
    hits = [x['tracks']['items'][0] for x in search_results]

    #get all my playlists, check if playlist_name already there
    new_pl = None
    for my_pl in sp.user_playlists(user=sp.me()['id'])['items']:
        logger.info('my_pl: {}'.format(my_pl['name']))
        if my_pl['name'] == playlist_name:
            logger.warning('appending to {}'.format(my_pl))
            new_pl = sp.user_playlist(user=sp.me()['id'], playlist_id=my_pl['id'])
            break
    if not new_pl:
        logger.warning('new playlist!')
        new_pl = sp.user_playlist_create(user=sp.me()['id'],name=playlist_name,public=True)

    out_url = new_pl['external_urls']['spotify']
    logger.info(out_url)

    #get all tracks in the playlist
    new_new_pl = sp.user_playlist(sp.me()['id'], new_pl['uri'])

    old_track_uris = set([x['track']['uri'] for x in new_new_pl['tracks']['items']])
    for s in old_track_uris:
        logger.debug('old! {}'.format(s))

    new_track_uris = [hit['uri'] for hit in hits if hit['uri'] not in old_track_uris]
    for new_track_uri in new_track_uris:
        logger.debug('new! {}'.format(new_track_uri))

    #can only insert 100 tracks at a time...
    #http://stackoverflow.com/a/434328/424631
    def chunker(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    logger.warning('adding {0} new tracks to {1}'.format(len(new_track_uris), new_pl['name']))
    if len(new_track_uris) > 0:
        for sublist in chunker(new_track_uris,99):
            sp.user_playlist_add_tracks(sp.me()['id'],new_pl['uri'],sublist)
            time.sleep(7)
            logger.warning('added {0} new tracks to {1}'.format(len(sublist), new_pl['name']))

    return out_url


def main():
    monday = isoweek.Week(2015,0).thisweek().monday()

    subreddit=sys.argv[1]
    playlist_name = '/r/'+subreddit+' week of '+str(monday)
    botname='heardditbot'
    logger.info(subreddit + "\t" + playlist_name)

    #figure all the hot submissions on the target subreddit
    hot_links = list(get_submissions(subreddit=subreddit,limit=500))
    logger.info('number of submissions: {0}'.format(len(hot_links)))

    #parse out the urls, titles, and post times from the submissions
    urls = [(x.url, x.title, datetime.datetime.fromtimestamp(x.created)) for x in hot_links]
    todays_urls = [x[0] for x in urls if x[2].date() >= monday]
    todays_titles = [x[1] for x in urls if x[2].date() >= monday]
    logger.info("len(todays_urls): {0}".format(len(todays_urls)))
    logger.info("len(todays_titles): {0}".format(len(todays_titles)))

    #append to soundcloud playlist
    try:
        #logger.warning("NO SOUNDCLOUD!!!")
        new_soundcloud_list_url = create_soundcloud_playlist_from_urls(todays_urls, playlist_name)
        logger.info("new_soundcloud_list_url:  {}".format(new_soundcloud_list_url))
    except:
        logger.exception('create_soundcloud_playlist_from_urls exception...')

    #append to spotify playlist
    try:
        new_spotify_list_url = create_spotify_playlist_from_titles(todays_titles, playlist_name)
        logger.info("new_spotify_list_url:  {}".format(new_spotify_list_url))
    except:
        logger.exception("create_spotify_playlist_from_titles exception...")

    #post to reddit on Wednesdays (after the playlists get some stuff in them)
    today = datetime.datetime.now().date()
    wednesday = isoweek.Week(2015,0).thisweek().wednesday()
    if today == wednesday:
        #the subreddits I've already posted on
        allowed_subreddits = ['futurebeats', 'hiphopheads', 'listentothis']
        if (subreddit in allowed_subreddits) and (new_soundcloud_list_url is not None):
            link_title='Soundcloud playlist for '+playlist_name
            logger.info('posting '+link_title+' to '+subreddit+' url: '+new_soundcloud_list_url)
            check_reposts_and_submit_url(creds_file='/home/ubuntu/my_reddit_accounts.properties', subreddit=subreddit,
                    title=link_title, playlist_url=new_soundcloud_list_url, username=botname)

            logger.info('sleeping 10min for reddit ratelimits...')
            time.sleep(600)

            link_title='Spotify playlist for '+playlist_name
            logger.info('posting '+link_title+' to '+subreddit+' url: '+new_spotify_list_url)
            check_reposts_and_submit_url(creds_file='/home/ubuntu/my_reddit_accounts.properties', subreddit=subreddit,
                    title=link_title, playlist_url=new_spotify_list_url, username=botname)

    return

if __name__ == '__main__':
    main()
