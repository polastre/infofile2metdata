#!/usr/bin/env bash

convert=0
tag=0
clean=0
verbose=0

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -c|--convert) convert=1 ;;
        -t|--tag) tag=1 ;;
        -x|--clean) clean=1 ;;
        -v|--verbose) verbose=1 ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

convert () {
  # Convert SHN to FLAC
  for f in **/*.shn; do
    if [ ! -f ${f/%.shn/.flac} ]; then
      if [ $verbose == 1 ]; then
        echo "converting $f"
      fi
      ffmpeg -i "$f" "${f/%.shn/.flac}" ;
    fi
  done
}

tag () {
  # Write VORBIS data to FLAC
  for f in **/*.flac; do
    if [ -f ${f/%.flac/.vorbis} ]; then
      if [ $verbose == 1 ]; then
        echo "writing tags to $f"
      fi
      metaflac --preserve-modtime --remove-all-tags --import-tags-from="${f/%.flac/.vorbis}" "$f" ;
    fi
  done
}

clean () {
  for f in **/*.shn; do
    if [ -f ${f/%.shn/.flac} ]; then
      if [ $verbose == 1 ]; then
        echo "delete $f"
      fi
      rm -f $f ;
    fi
  done
  for f in **/*.flac; do
    if [ -f ${f/%.flac/.vorbis} ]; then
      if [ $verbose == 1 ]; then
        echo "delete $f"
      fi
      rm -f ${f/%.flac/.vorbis} ;
    fi
  done
}

if [ $convert == 1 ]; then
  convert ;
fi

if [ $tag == 1 ]; then
  tag ;
fi

if [ $clean == 1 ]; then
  clean ;
fi

exit 0 ;
