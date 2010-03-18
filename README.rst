uNotify
=========

uNotify monitors your uTorrent downloads and executes commands when a download
completes.


Requirements
------------

* Python 2.6 (or 2.4/2.5 + simplejson)
* uTorrent with WebUI enabled


Usage
-----

1. Install `uTorrent <http://www.utorrent.com/>`_ and enable the `WebUI <http://www.utorrent.com/documentation/webui>`_.
2. Copy ``config.py.example`` to ``config.py`` and edit the file.
3. Make sure you've entered the correct host and port and the same username and password as in uTorrent.
4. Run the script.


If you're a windows user and hate having a cluttered taskbar you can use
`AppTrayer <http://github.com/liato/AppTrayer>`_ (or a similar app) to minimize
uNotify to the system tray:

    apptrayer.exe --icon=C:\\path\\to\\uNotify\\unotify.ico python X:\\path\\to\\uNotify\\unotify.py


If you're a linux or mac user you can simply use:

    ./unotify.py &

    
License
-------

MIT.
