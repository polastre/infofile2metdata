#!/usr/bin/env bash
IFS=$'\n'

convert=0
tag=0
clean=0
clean_f=0
verbose=0

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -c|--convert) convert=1 ;;
        -t|--tag) tag=1 ;;
        -x|--clean) clean=1 ;;
        -xf|--cleanforce) clean_f=1 ;;
        -v|--verbose) verbose=1 ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

convert () {
  # Convert SHN to FLAC
  for f in $(find . -name '*.shn'); do
    if [ ! -f ${f/%.shn/.flac} ]; then
      if [ $verbose == 1 ]; then
        echo "converting $f"
      fi
      ffmpeg -i "$f" "${f/%.shn/.flac}" ;
    fi
  done
  for f in $(find . -name '*.m4a'); do
    if [ ! -f ${f/%.m4a/.flac} ]; then
      if [ $verbose == 1 ]; then
        echo "converting $f"
      fi
      ffmpeg -i "$f" "${f/%.m4a/.flac}" ;
    fi
  done
}

tag () {
  # Write VORBIS data to FLAC
  for f in $(find . -name '*.flac'); do
    if [ -f ${f/%.flac/.vorbis} ]; then
      if [ $verbose == 1 ]; then
        echo "writing tags to $f"
      fi
      metaflac --preserve-modtime --remove-all-tags --import-tags-from="${f/%.flac/.vorbis}" "$f" ;
    fi
  done
}

clean () {
  for f in $(find . -name '*.flac'); do
    # delete m4a if there's a vorbis, since it is correctly processed
    if [ -f "${f/%.flac/.vorbis}" ] && [ -f "${f/%.flac/.m4a}" ]; then
      if [ $verbose == 1 ]; then
        echo "delete ${f/%.flac/.m4a}"
      fi
      rm -f "${f/%.flac/.m4a}" ;
    fi
    # delete shn if there's a vorbis, since it is correctly processed
    if [ -f "${f/%.flac/.vorbis}" ] && [ -f "${f/%.flac/.shn}" ]; then
      if [ $verbose == 1 ]; then
        echo "delete ${f/%.flac/.shn}"
      fi
      rm -f "${f/%.flac/.shn}" ;
    fi
    # delete vorbis if they are standalone and there is no corresponding SHN/M4A
    if [ -f "${f/%.flac/.vorbis}" ] && [ ! -f "${f/%.flac/.shn}" ] && [ ! -f "${f/%.flac/.m4a}" ]; then
      if [ $verbose == 1 ]; then
        echo "delete ${f/%.flac/.vorbis}"
      fi
      rm -f "${f/%.flac/.vorbis}" ;
    fi
  done
}

force_clean () {
  for f in $(find . -name '*.shn'); do
    if [ -f "${f/%.shn/.flac}" ]; then
      if [ $verbose == 1 ]; then
        echo "delete $f"
      fi
      rm -f "$f" ;
    fi
  done
  for f in $(find . -name '*.m4a'); do
    if [ -f "${f/%.m4a/.flac}" ]; then
      if [ $verbose == 1 ]; then
        echo "delete $f"
      fi
      rm -f "$f" ;
    fi
  done
  for f in $(find . -name '*.flac'); do
    if [ -f "${f/%.flac/.vorbis}" ]; then
      if [ $verbose == 1 ]; then
        echo "delete ${f/%.flac/.vorbis}"
      fi
      rm -f "${f/%.flac/.vorbis}" ;
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
if [ $clean_f == 1 ]; then
  force_clean ;
fi

exit 0 ;
