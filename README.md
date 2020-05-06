# Infofile Parser for Live Concerts

Live concerts are typically distributed in FLAC or shorten (SHN) format. The taper of the show includes a text file with the track listing and information about the show. This information is not typically stored in the metadata of the audio files themselves, making the files difficult to index, navigate and playback. Even if the audio files have metadata, the formatting is inconsistent.

Included are tools that I wrote to assist me with live concert library management. These tools are part of my workflow:
1. Convert SHN files to FLAC files.
1. Read infofiles to collect metadata about the live show.
1. Write that metadata into files in VORBIS_COMMENT format for FLAC.
1. Write the metadata to the FLAC files.
1. Clean up SHN and metadata files after processing is complete.

These tools only require Python and a Bash shell. No additional libraries are needed.

## Example Usage

These commands can be done within a live show folder, or from a root directory holding many live show folders.

Convert SHN to FLAC:

```
./process -c -v
```

Generate metadata file infofiles:

```
python parseinfo.py -w
```

Write metadata tags to FLAC files:

```
./process -t -v
```

Clean up SHN and metadata (**Warning this is distructive and will delete your SHN files if they exist**):

```
./process -x -v
```

## Requirements

You must have `ffmpeg` installed, which also includes `metaflac`.
