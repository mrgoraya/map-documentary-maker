#!/usr/bin/env bash
# Re-download the photos and footage used in the film from Wikimedia Commons (with credits).
# Run from this folder: bash fetch_assets.sh
set -e
PY=~/.cache/map-documentary-maker/venv/bin/python
SK=../../skills/map-documentary-maker/scripts
$PY $SK/fetch_commons.py get "File:Ali Khamenei crop.jpg" p_khamenei
$PY $SK/fetch_commons.py get "File:Official Presidential Portrait of President Donald J. Trump (2025) (3x4 close cropped).jpg" p_trump
$PY $SK/fetch_commons.py get "File:U S Forces Launch Operation Epic Fury (997765).webm" v_epicfury_launch
$PY $SK/fetch_commons.py get "File:2026-10-10 HouthiAttacksOnSaudiAirport.jpg" i_riyadh_airport
$PY $SK/fetch_commons.py get "File:March 2026 Official Vice Presidential Portrait of JD Vance (3x4 cropped).jpg" p_vance
$PY $SK/fetch_commons.py get "File:Portrait of Mojtaba Khamenei (2).jpg" p_mojtaba
$PY $SK/fetch_commons.py get "File:Sidelines of Islamabad Talks 8.jpg" i_islamabad_talks
$PY $SK/fetch_commons.py get "File:2026 Badr bin Hamad Al Busaidi (cropped).jpg" p_albusaidi
$PY $SK/fetch_commons.py get "File:U S Forces Start Mine Clearance Mission in Strait of Hormuz (9609002).jpg" i_hormuz_mines
$PY $SK/fetch_commons.py get "File:USS Spruance launching Tomahawk during Operation Epic Fury.jpg" i_spruance_tomahawk
$PY $SK/fetch_commons.py get "File:USS Gerald R Ford supports Operation Epic Fury (9542704).jpg" i_ford
$PY $SK/fetch_commons.py get "File:USS Abraham Lincoln supports Operation Epic Fury (998118).webm" v_lincoln
