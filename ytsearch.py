import yt_dlp
from yt_dlp.utils import (
    DownloadError,
    ExtractorError,
    format_bytes,
    UnavailableVideoError,
)
import json
import socket

from yt_dlp.compat import (
    compat_http_client,
    compat_urllib_error,
    compat_HTTPError,
)

import os
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:1080'

def get_seconds(time_str):
    # split in hh, mm, ss
    if len(time_str.split(':'))<3:
        time_str="00:"+time_str
#     print('Time in hh:mm:ss:', time_str)
    hh, mm, ss = time_str.split(':')
    return int(hh) * 3600 + int(mm) * 60 + int(ss)

def longer_than_a_minute(info, *, incomplete):
    """Download only videos longer than a minute (or with unknown duration)"""
    duration = info.get('duration')
    if duration and duration < 60:
        return 'The video is too short'
def save_videos_yt_dlp(url,videopath,videoname,query=''):
    print('start downloading  yt dlp',videopath,videoname)
    urls=[]
    RETRIES = 3
    # ℹ️ See docstring of yt_dlp.YoutubeDL for a description of the options
    if videoname is None or videoname =='':
        outputtemplate ="%(id)s.%(ext)s"
    else:
        outputtemplate =videoname
    ydl_opts = {
        'format': 'bestaudio/best',
        # 'PATH': split_path(videopath),
        'outtmpl': f"{videopath}/{outputtemplate}",
        # 'proxy': 'socks://127.0.0.1:1080',
        'writesubtitles': 'true',
        # 'subtitleslangs': 'en', 
        
        # 'merge_output_format': 'mp4', 
        # 'match-filter': 'duration >=01:00:00',
        'noprogress': True
        # 'postprocessors': [{ # Embed metadata in video using ffmpeg. 'key': 'FFmpegMetadata', 'add_metadata': True, }, { # Embed thumbnail in file 'key': 'EmbedThumbnail', 'already_have_thumbnail': False, }
        # 'postprocessors': [{
        #     # Embed metadata in video using ffmpeg.
        #     # ℹ️ See yt_dlp.postprocessor.FFmpegMetadataPP for the arguments it accepts
        #     'key': 'FFmpegMetadata',
        #     'add_chapters': True,
        #     'add_metadata': True,
        # }],
        # 'logger': MyLogger(),
        # 'progress_hooks': [my_hook],
    }

# ydl_opts = { 'download_archive': 'data/archive.txt', 'paths': { 'home': '/downloads/test', 'temp': '/data' }, 'outtmpl': '%(uploader)s - %(title)s.%(ext)s', 'merge_output_format': 'mkv', 'noplaylist': 'true', 'writesubtitles': 'true', 'subtitleslangs': 'en', 'merge_output_format': 'mkv', 'postprocessors': [{ # Embed metadata in video using ffmpeg. 'key': 'FFmpegMetadata', 'add_metadata': True, }, { # Embed thumbnail in file 'key': 'EmbedThumbnail', 'already_have_thumbnail': False, }], }
    # Add custom headers
    yt_dlp.utils.std_headers.update({'Referer': 'https://www.google.com'})

    # ℹ️ See the public functions in yt_dlp.YoutubeDL for for other available functions.
    # Eg: "ydl.download", "ydl.download_with_info_file"


    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # ydl.add_post_processor(MyCustomPP())
        # ℹ️ ydl.sanitize_info makes the info json-serializable
        # print(json.dumps(ydl.sanitize_info(info)))

        try_num = 1
        while True:
            try:
                # We're not using .download here since that is just a shim
                # for outside error handling, and returns the exit code
                # instead of the result dict.
                if query=='':
                    res_dict = ydl.extract_info(url)
                    print('query',query)

                else:

                    res_dict=ydl.extract_info("ytsearch20:"+query, download=False, ie_key="YoutubeSearch")
                #     res_dict=ydl.extract_info("bilisearch20:"+query, download=False, ie_key="YoutubeSearch")

                entries=res_dict['entries']
                for e in entries:

                    seconds=get_seconds(e['duration_string'])

                    if seconds>3600:
                    
                        print(e['original_url'])
                        # "duration_string": "1:27:37",
                        # "fulltitle": "1080P\u9ad8\u6e05\u4fee\u590d \u9e26\u7247\u6218\u4e89\u5386\u53f2\u7535\u5f71\u300a\u6797\u5219\u5f90\u300b1959 The Opium Wars \u5927\u573a\u9762\u8fd8\u539f\u5386\u53f2\u6062\u5b8f\u4e4b\u611f | \u4e2d\u56fd\u8001\u7535\u5f71",
                        # webpage_url
                        print(e['fulltitle'])          
                        urls.append(e['original_url'])      
                        print(e['webpage_url'])
                        print(e['duration_string'])
                        ydl.download(e['original_url'])

            except (DownloadError, ExtractorError) as err:
                # Check if the exception is not a network related one
                if not err.exc_info[0] in (compat_urllib_error.URLError, socket.timeout, UnavailableVideoError, compat_http_client.BadStatusLine) or (err.exc_info[0] == compat_HTTPError and err.exc_info[1].code == 503):
                    raise

                if try_num == RETRIES:
                    print('%s failed due to network errors, skipping...')
                    return

                print('Retrying: {0} failed tries\n\n##########\n\n'.format(try_num))

                try_num += 1
            else:
                break
    return urls

# save_videos_yt_dlp('','./videos','','林则徐')


# from youtubesearchpython import VideosSearch

# videosSearch = VideosSearch('林则徐',limit = 10)
# videos=videosSearch.result()['result']
# for eachres in videos.items():

#         eachresdictobj = {
#                 "title": str(eachres.get("title")),
#                 "duration": str(eachres.get("duration")),
#                 "views": str(eachres.get("viewCount").get("short")),
#                 "channel": str(eachres.get("channel").get("name")),
#                 "urllink": f"https://www.youtube.com/watch?v={str(eachres.get('id'))}",
#         }


# print(get_seconds('24:50'))