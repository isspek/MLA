#!d:\benutzer\popik\desktop\git\mla\env-mla\scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'news-please==1.5.3','console_scripts','news-please'
__requires__ = 'news-please==1.5.3'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('news-please==1.5.3', 'console_scripts', 'news-please')()
    )
