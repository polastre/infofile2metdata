import argparse
from enum import Enum
from dateutil.parser import parse as dateparse
import utils
import os
import re

DEBUG = False
WRITE_TAGS = False

EXT = ".flac"
TITLE_RE = re.compile(r'^(d\dt){0,1}(?P<num>\d{1,2})[:\.\,\s]*(?P<name>(([\w\s\"\-\(\)\/\[\]<>.,?\'’^+#&])|(E\d*:))+)(\s*(([~!@#$%^&*+=?>])|(-->))+)*(((\s{2,}[-]{1,2}\s*)|\s+)[[{]{0,1}(?P<time>\d{1,2}[:\.]\d{2}([:\.]\d{2,3})?){0,1}[])]{0,1}){0,1}$')
# TITLE_RE = re.compile(r'^(d\dt){0,1}(?P<num>\d{1,2})[:\.\,\s]*(?P<name>([\w\s\"\-\(\)\/\[\]<>.,?\'’^>#&]|E:)+)(\s*(([~!@#$%^&*+=?>])|(-->))+)*(((\s{2,}[-]{1,2}\s*)|\s+)[[{]{0,1}(?P<time>\d{1,2}[:\.]\d{2}([:\.]\d{2,3})?){0,1}[])]{0,1}){0,1}$')
LOCATION_RE = re.compile(r'(?P<city>[\w\s\.]+)((,\s*)|(\s+))(?P<state>\w\.{0,1}\w\.{0,1})$')
DISC_RE = re.compile(r'^(\d{0,2}\s+((dis[ck])|(cd)))|(((dis[ck])|(cd))\s+\d{0,2})', re.I)

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"
ANSI_PASS = f"{GREEN}\u2713{RESET}"
ANSI_FAIL = f"{RED}\u2717{RESET}"

success = []
fail = []

def parse(path):
    global success, fail
    r = parseDir(path)
    # if an infofile was found, check if it passes checks
    if r.get('infofile') and r.get('info'):
        print(f"* {r['cwd']}")
        if DEBUG:
            print(r)
        if len(r['info']['tracks']) != len(r['files']):
            print(f"{ANSI_FAIL} Track length doesn't match number of files ({len(r['info']['tracks'])}:{len(r['files'])})")
            fail.append(r['cwd'])
        elif not r['info']['metadata']['venue'] or not r['info']['metadata']['location'] or not r['info']['metadata']['date']:
            print(f"{ANSI_FAIL} Metadata could not be parsed")
            fail.append(r['cwd'])
        else:
            print(f"{ANSI_PASS} {r['info']['metadata']['artist']}: {r['info']['metadata']['date'].strftime('%Y-%m-%d')}: {r['info']['metadata']['venue']}, {r['info']['metadata']['location']}")
            success.append(r['cwd'])
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
        if f.endswith(".txt") and f != 'shntool.txt' and not ".ffp" in f and not "ffp-" in f:
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
    """ Parse the infofile for album metadata and track names """
    def _format_loc(loc):
        """ Helper function to format localities """
        city = loc.group('city').strip()
        state = loc.group('state').strip()
        if len(state) == 2:
            state = state.upper()
        if city[0].islower():
            city = city[0].upper() + city[1:]
        return f"{city}, {state}"
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
    with open(filename, 'rb') as file_object:
        data = file_object.read()
        try:
            lines = data.decode('utf-8')
        except UnicodeDecodeError as e:
            lines = data.decode('cp1252')
        except ValueError:
            lines = data.decode('latin-1')
        except:
            return {}
        for line in lines.split("\n"):
            line = line.strip()
            if not line:
                continue
            linecount += 1
            if state == InfoState.INTRO:
                if linecount == 1:
                    END_DELIMIT = ['(', '[']
                    for e in END_DELIMIT:
                        line = line.split(e, 1)[0].strip()
                    if utils.NORMALIZE.get(line.lower()):
                        artist = utils.NORMALIZE[line.lower()]
                    else:
                        artist = line.title()
                    metadata['artist'] = artist
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
                    loc = LOCATION_RE.match(l1)
                    if loc:
                        metadata['location'] = _format_loc(loc)
                        continue
                    loc = LOCATION_RE.match(l2)
                    if loc:
                        metadata['venue'] = l1
                        metadata['location'] = _format_loc(loc)
                        continue
                    if l2.lower() in utils.STATES or l2.lower() in utils.COUNTRIES:
                        metadata['location'] = line
                        continue
                    if "," in l2 and (
                            l2.split(",",1)[1].strip().lower() in utils.STATES or
                            l2.split(",",1)[1].strip().lower() in utils.COUNTRIES):
                        metadata['venue'] = l1
                        metadata['location'] = l2
                        continue
                # formats like "Deer Creek-Noblesville, IN"
                if "-" in line and not metadata['location']:
                    l1, l2 = line.split("-",1)
                    l1 = l1.strip()
                    l2 = l2.strip()
                    loc = LOCATION_RE.match(l2)
                    if loc:
                        metadata['venue'] = l1
                        metadata['location'] = _format_loc(loc)
                        continue
                if not metadata['location'] and LOCATION_RE.match(line):
                    loc = LOCATION_RE.match(line)
                    metadata['location'] = _format_loc(loc)
                    continue
                if not metadata['venue']:
                    metadata['venue'] = line
                    continue
                if linecount >= 4:
                    state = InfoState.TRACK
            elif state == InfoState.TRACK:
                # Skip disc intros, eg "1 Disc" or "CD 1"
                # print(line)
                m = DISC_RE.search(line)
                if m and not 'intro' in line.lower() and not 'disco' in line.lower():
                    continue
                # if the line is a date, skip it
                try:
                    _date = dateparse(line)
                    continue
                except Exception as e:
                    pass
                # Extract track information via regex
                m = TITLE_RE.match(line)
                # print(m)
                if m:
                    name = m.group('name').strip(" -<>[]\t")
                    if name.islower():
                        name = name.title()
                    track = {
                      'num': int(m.group('num')),
                      'name': name,
                      'time': m.group('time'),
                      'track': tracknum,
                    }
                    tracknum += 1
                    tracks.append(track)
    # clean up venue and location formatting
    if metadata.get('venue') and metadata['venue'].islower():
        metadata['venue'] = metadata['venue'].title()
    metadata['tracktotal'] = len(tracks)
    return {
        'tracks': tracks,
        'metadata': metadata
    }

def matchTracksToFiles(info, files):
    """ match track info to the list of flac files """
    if not info.get('tracks') or len(info['tracks']) != len(files):
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
    global DEBUG, WRITE_TAGS, success, fail
    parser = argparse.ArgumentParser(description='Parse track info for live recordings.')
    parser.add_argument('path', nargs='?', default=os.getcwd())
    parser.add_argument('-w', '--write', action='store_true', help='write tags to flac files.')
    parser.add_argument('--debug', action='store_true', help='print debug information.')
    args = parser.parse_args()
    DEBUG = args.debug
    WRITE_TAGS = args.write
    r = parse(args.path)
    print(f"{len(success)}/{len(success)+len(fail)} succeeded")
    if len(fail) > 0:
        print("Failed:")
        fail_str = '\n'.join(fail)
        print(f"{fail_str}")
if __name__== "__main__":
    main()
