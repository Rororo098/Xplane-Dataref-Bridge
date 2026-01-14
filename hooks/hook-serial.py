from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all serial submodules (including Windows backends and port enumeration)
hiddenimports = collect_submodules('serial')

# Ensure critical components are included
hiddenimports += [
    'serial.SerialBase',
    'serial.serialutil',
    'serial.serialwin32',
    'serial.win32',
    'serial.threaded',
    'serial.rfc2217',
    'serial.serialcli',
    'serial.rs485',
    'serial.tools.list_ports',
    'serial.tools.list_ports_windows',
    'serial.tools.list_ports_posix',
    'serial.tools.list_ports_osx',
    'serial.urlhandler',
    'serial.urlhandler.protocol_socket',
    'serial.urlhandler.protocol_rfc2217',
    'serial.urlhandler.protocol_loop',
]

# Include any data files a serial package might ship
datas = collect_data_files('serial')