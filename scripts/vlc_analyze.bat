@ECHO off
REM Place this in your path to run this
SET PY_VLC_ANALYZE=

IF DEFINED PY_VLC_ANALYZE (
python \vlc_check_audio\vlc_analyze.py %*
) ELSE (
ECHO Failed to find vlc_analyze.py... location not set.
)
