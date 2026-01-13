# Hook file for qasync
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = [
    'qasync',
    'qasync.qtloop',
] + collect_submodules('qasync')