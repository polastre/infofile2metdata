import argparse
from enum import Enum
from dateutil.parser import parse as dateparse
import os
import re

DEBUG = False
WRITE_TAGS = False

EXT = ".flac"
TITLE_RE = re.compile(r'^(d\dt){0,1}(?P<num>\d{1,2})[:\.\,\s]*(?P<name>([\w\s\"\-\(\)\/\[\]<>.,?\'^>#&]|E:)+)(\s*[~!@#$%^&*+=?>]+)*(((\s{2,}[-]{1,2}\s*)|\s+)[[{]{0,1}(?P<time>\d{1,2}[:\.]\d{2}([:\.]\d{2,3})?){0,1}[])]{0,1}){0,1}$')
LOCATION_RE = re.compile(r'([\w\s\.]+)(,){0,1} (\w\.{0,1}\w\.{0,1})$')

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"
ANSI_PASS = f"{GREEN}✓{RESET}"
ANSI_FAIL = f"{RED}✗{RESET}"

def parse(path):
    r = parseDir(path)
    # if an infofile was found, check if it passes checks
    if r['infofile'] and r['info']:
        print(f"* {r['cwd']}")
        if DEBUG:
            print(r)
        if len(r['info']['tracks']) != len(r['files']):
            print(f"{ANSI_FAIL} Track length doesn't match number of files ({len(r['info']['tracks'])}:{len(r['files'])})")
        elif not r['info']['metadata']['venue'] or not r['info']['metadata']['location'] or not r['info']['metadata']['date']:
            print(f"{ANSI_FAIL} Metadata coult not be parsed")
        else:
            print(f"{ANSI_PASS} {r['info']['metadata']['artist']}: {r['info']['metadata']['date'].strftime('%Y-%m-%d')}: {r['info']['metadata']['venue']}, {r['info']['metadata']['location']}")
            if WRITE_TAGS:
                for t in r['info']['tracks']:
                    writeMetaFlac(t)
    # otherwise recurse into the directories until we find something or end
    else:
        for d in r['dirs']:
            q = parse(d)
    return r

def parseDir(path):
    filelist = os.listdir(path)
    infofile, info = None, None
    dirs = []
    files = []
    # check for a .txt file
    for f in filelist:
        f_lower = f.lower()
        if f.endswith(".txt") and not ".ffp" in f:
            infofile = os.path.join(path, f)
        if f.endswith(EXT):
            files.append(os.path.join(path, f))
    # check for subdirectories
    for f in filelist:
        _path = os.path.join(path, f)
        if os.path.isdir(_path):
            dirs.append(_path)
    if infofile and dirs:
        for d in dirs:
            sublist = os.listdir(d)
            for f in sublist:
                if f.lower().endswith(EXT):
                    files.append(os.path.join(d, f))
    files.sort()
    dirs.sort()
    if infofile:
        info = parseInfoFile(infofile)
        info = matchTracksToFiles(info, files)
    return {
        'infofile': infofile,
        'files': files,
        'dirs': dirs,
        'info': info,
        'cwd': os.path.basename(os.path.normpath(path))
    }

class InfoState(Enum):
    INTRO = 1
    TRACK = 2

def parseInfoFile(filename):
    linecount = 0
    tracknum = 1
    state = InfoState.INTRO
    tracks = []
    metadata = {
        'date': None,
        'artist': None,
        'venue': None,
        'location': None,
        'tracktotal': 0,
    }
    with open(filename, 'r') as file_object:
        for line in file_object.readlines():
            # linecount += 1
            line = line.strip()
            if not line:
                continue
            linecount += 1
            if state == InfoState.INTRO:
                # if DEBUG:
                #     print(f"{linecount}: {line}")
                if linecount == 1:
                    metadata['artist'] = line
                    continue
                if not metadata['date']:
                    try:
                        metadata['date'] = dateparse(line)
                        continue
                    except Exception as e:
                        pass
                if "," in line and not metadata['location']:
                    l1, l2 = line.split(",",1)
                    l1 = l1.strip()
                    l2 = l2.strip()
                    if LOCATION_RE.match(l1):
                        metadata['location'] = l1
                        continue
                    if LOCATION_RE.match(l2):
                        metadata['venue'] = l1
                        metadata['location'] = l2
                        continue
                if not metadata['location'] and LOCATION_RE.match(line):
                    metadata['location'] = line
                    continue
                if not metadata['venue']:
                    metadata['venue'] = line
                    continue
                if linecount >= 4:
                    state = InfoState.TRACK
            elif state == InfoState.TRACK:
                m = TITLE_RE.match(line)
                # print(line)
                # print(m)
                if m:
                    track = {
                      'num': int(m.group('num')),
                      'name': m.group('name').strip(" -<>[]\t"),
                      'time': m.group('time'),
                      'track': tracknum,
                    }
                    tracknum += 1
                    tracks.append(track)
    metadata['tracktotal'] = len(tracks)
    return {
        'tracks': tracks,
        'metadata': metadata
    }

def matchTracksToFiles(info, files):
    """ match track info to the list of flac files """
    if len(info['tracks']) != len(files):
        return info
    for i, f in enumerate(files):
        track = info['tracks'][i]
        track['file'] = f
        track['vorbis'] = toVorbis(info['metadata'], info['tracks'][i])
        track['tagfile'] = f"{os.path.splitext(f)[0]}.vorbis"
    return info

def toVorbis(metadata, track):
    """ convert the track and album metadata into tag vorbis for metaflac """
    date_string = metadata['date'].strftime("%Y-%m-%d")
    year_string = metadata['date'].strftime("%Y")
    return f"""ARTIST={metadata['artist']}
ARTISTSORT={metadata['artist']}
ALBUMARTIST={metadata['artist']}
ALBUMARTISTSORT={metadata['artist']}
ALBUM={date_string}: {metadata['venue']}, {metadata['location']}
TITLE={track['name']}
TRACKNUMBER={track['track']}
TRACKTOTAL={metadata['tracktotal']}
YEAR={year_string}
DATE={date_string}
ORIGINALDATE={date_string}
LOCATION={metadata['venue']}, {metadata['location']}
RELEASESTATUS=bootleg
"""

def writeMetaFlac(track):
    """ Write the vorbis content to the flac file """
    f = open(track['tagfile'], "w")
    f.write(track['vorbis'])
    f.close()

def main():
    global DEBUG, WRITE_TAGS
    parser = argparse.ArgumentParser(description='Parse track info for live recordings.')
    parser.add_argument('path', nargs='?', default=os.getcwd())
    parser.add_argument('-w', '--write', action='store_true', help='write tags to flac files.')
    parser.add_argument('--debug', action='store_true', help='print debug information.')
    args = parser.parse_args()
    DEBUG = args.debug
    WRITE_TAGS = args.write
    r = parse(args.path)

if __name__== "__main__":
    main()
