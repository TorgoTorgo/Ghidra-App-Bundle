# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

application = 'Ghidra.app'
appname = os.path.basename(application)
icon = os.path.join(application, 'Contents', 'Resources', 'Ghidra.icns')
badge_icon = icon
files = [ application ]

# Symlinks to create
symlinks = { 'Applications': '/Applications' }

# Where to put the icons
icon_locations = {
    appname:        (140, 120),
    'Applications': (500, 120)
    }

background = 'builtin-arrow'

show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
sidebar_width = 180

# Window position in ((x, y), (w, h)) format
window_rect = ((100, 100), (640, 280))

default_view = 'icon-view'

# General view configuration
show_icon_preview = False

# Set these to True to force inclusion of icon/list view settings (otherwise
# we only include settings for the default view)
include_icon_view_settings = 'auto'
include_list_view_settings = 'auto'

# .. Icon view configuration ...................................................

arrange_by = None
grid_offset = (0, 0)
grid_spacing = 100
scroll_position = (0, 0)
label_pos = 'bottom' # or 'right'
text_size = 16
icon_size = 128
