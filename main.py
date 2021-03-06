import bs4 as bs
import argparse
import pafy
import sys
import os
import re

if sys.version_info[:2] >= (3, 0):
    import urllib.request
else:
    from six.moves import urllib


def argument_parser():
    # Defining the arguments to be passed in the command line. [flow: analyze_arguments]
    parser = argparse.ArgumentParser(description="YouTube Downloader (Unofficial)")
    parser.add_argument('type', type=str, help="single/multiple/playlist/profile")
    parser.add_argument('url', type=str, help="link to the original video on YouTube")
    parser.add_argument('-a', '--audio', action='store_true', default=False, help="audio only mode")
    parser.add_argument('-o', '--output', type=str, default=None, help="download location")
    parser.add_argument('-m', '--maxquality', action='store_true', default=False,
                        help="download video(s) in the best quality available")
    parser.add_argument('--silent', action='store_true', default=False, help="silent operations")
    # --silent is ATM supported only for 'playlist' mode.
    args = parser.parse_args()
    sys.stdout.write(str(analyze_arguments(args)))


def analyze_arguments(args):
    # Analyzing the arguments passed and identifying them.
    if not re.match("https?://www.youtube.com/", args.url):
        print("The URL is invalid.")
    elif args.type == 'multiple' and args.url[-3:] != 'txt':
        print("The file type is not supported.")
    elif not os.path.exists(args.output):
        print("The path does not exist.")
        sys.exit()
    else:
        if args.type == 'single':
            download_single(args)
        elif args.type == 'multiple':
            download_multiple(args)
        elif args.type == 'playlist':
            download_playlist(args)
        elif args.type == 'description':
            download_description(args)
            # elif args.type == 'profile':
            # download_profile(args)


def download_single(args):
    # For downloading a single video.
    video_description(args.url)

    if not args.maxquality:
        stream = list_streams(args)
    else:
        stream = pafy.new(args.url).getbest()
    start_download(stream, args.output)


def download_multiple(args):
    # For downloading multiple videos.
    with open(args.url) as file:
        data = file.read().split('\n')
    for url in data:
        video_description(url)


def download_playlist(args):
    # For extracting the URLs of all the videos in a playlist and downloading it one after another.
    sauce = urllib.request.urlopen(args.url).read()
    soup = bs.BeautifulSoup(sauce, 'lxml')
    urls = set([i.get('href') for i in soup.find_all('a') if 'index=' in i.get('href')])

    print()
    print("This playlist contains {} videos.".format(len(urls)))
    print()

    for skel in urls:
        url = 'https://www.youtube.com' + skel

        if not args.silent:
            video_description(url)

        if url.count("https") > 1:
            url = url[23:]
        video = pafy.new(url)

        if not args.maxquality:
            stream = list_streams(args)
        else:
            stream = video.getbest()
        start_download(stream, path=args.output, title=video.title)
        print()


def download_description(args):
    # Download video description.

    if '.txt' not in args.url:
        sauce = urllib.request.urlopen(args.url).read()
        soup = bs.BeautifulSoup(sauce, 'lxml')

        date = soup.find('strong', {'class': 'watch-time-text'})
        description = soup.find('p', {'class': '', 'id': 'eow-description'})

        with open('{}\description.txt'.format(args.output), 'a') as file:
            file.write('{}\n\n{}\n\n\n'.format(date.text, description.text))


def video_description(url):
    # Get the description of video in the URL.

    video = pafy.new(url.strip())
    views = video.viewcount

    if views >= 1000:
        views = "{}k".format(round(views / 1000, 2))
    elif views >= 100000:
        views = "{}m".format(round(views / 100000), 2)

    print("""
\tVideo Description: 
\t------------------
\tTitle        : {}
\tAuthor       : {}
\tDuration     : {}
\tRating       : {}
\tViews        : {} \n""".format(video.title, video.author,
                                 video.duration, round(video.rating, 2),
                                 views))
    print()


def list_streams(args):
    # Listing the streams available for download.
    print('\n', '\t', 'Available Streams: ', '\n')

    video = pafy.new(args.url)

    if args.audio:
        streams = video.audiostreams
    else:
        streams = video.streams

    print("\t    %5s | %10s" % ("stream", "resolution"))
    print("\t-- + ----- + ----------")

    for index, stream in enumerate(streams):
        print("\t%2s    %5s  %10s" % (index, str(stream).split(':')[-1].split('@')[0],
                                      str(stream).split(':')[-1].split('@')[1]))
    print()

    while True:
        try:
            choice = int(input("Choice? "))
        except KeyboardInterrupt:
            print("Program terminated.")
            sys.exit()
        except ValueError:
            print("The input is invalid.")
        else:
            if not 0 <= choice <= len(streams):
                print("The choice is invalid.")
            else:
                return streams[choice]


def start_download(stream, path, title=None):
    # For downloading a single video.
    if path is None:
        path = os.getcwd()

    if title is None:
        stream.download(filepath=path)
    else:
        try:
            stream.download(filepath="{}\{}.{}".format(path, title, str(stream).split('@')[0][-3:]))
        except:
            pass
            # Only the playlist cases.


if __name__ == '__main__':
    argument_parser()
