# Read Pacman's repository databases and keep browse pages independent of privileged transactions.
import pathlib
import re
import tarfile
from functools import lru_cache

from .runtime import StoreError, package_name, run

DB = pathlib.Path('/var/lib/pacman')
PAGE_SIZE = 24
CATEGORIES = {
    'AudioVideo': ('audio', 'video', 'multimedia', 'media player', 'music'),
    'Development': ('development', 'compiler', 'programming', 'debugger', 'editor'),
    'Game': ('game', 'games', 'gaming', 'emulator'),
    'Graphics': ('graphics', 'drawing', 'photo', 'paint', '3d modeling'),
    'Network': ('internet', 'browser', 'network', 'messaging', 'email'),
    'Office': ('office', 'spreadsheet', 'document', 'word processor'),
    'Utility': ('utility', 'utilities', 'file manager', 'archive', 'terminal'),
}


def fields(data):
    return {
        key: value.splitlines()
        for key, value in re.findall(r'^%([A-Z0-9]+)%\n(.*?)(?=\n\n|\Z)', data.rstrip('\n'), re.M | re.S)
    }


def repositories():
    return [
        dict(id=name, name=name, trusted='Never' not in run(['pacman-conf','--repo',name,'SigLevel'],check=False).stdout.split())
        for name in run(['pacman-conf','--repo-list']).stdout.splitlines()
        if re.fullmatch(r'[a-zA-Z0-9_.-]+',name)
    ]


@lru_cache(maxsize=12)
def read_database(path, modified, size):
    entries = {}
    with tarfile.open(path, 'r:*') as archive:
        for member in archive:
            if not member.isfile() or not member.name.endswith('/desc') or member.size > 262144:
                continue
            raw = fields(archive.extractfile(member).read().decode('utf-8', 'replace'))
            if raw.get('NAME') and raw.get('VERSION'):
                entries[raw['NAME'][0]] = raw
    return entries


def database(repo):
    path = DB/'sync'/f'{repo}.db'
    try:
        stat = path.stat()
    except FileNotFoundError:
        return {}
    return read_database(path, stat.st_mtime_ns, stat.st_size)


def installed():
    output = run(['pacman','-Q'],check=False).stdout
    return dict(line.split(maxsplit=1) for line in output.splitlines() if ' ' in line)


def categories(description, groups=()):
    text = ' '.join((description,*groups)).lower()
    return [category for category, words in CATEGORIES.items() if any(re.search(r'\b'+word+r'\b',text) for word in words)] or ['System']


def component_metadata():
    return {
        'vlc': {'name':'VLC Media Player','desktopId':'vlc.desktop'},
        'firefox': {'name':'Firefox','desktopId':'org.mozilla.firefox.desktop'},
        'gimp': {'name':'GIMP','desktopId':'gimp.desktop'},
        'krita': {'name':'Krita','desktopId':'org.kde.krita.desktop'},
        'steam': {'name':'Steam','desktopId':'steam.desktop'},
        'discord': {'name':'Discord','desktopId':'discord.desktop'},
        'amogos-arch-store': {'name':'AmogOS Arch App Store','desktopId':'amogosarch.appstore.desktop'},
    }


def normalize(repo, raw, local):
    name = raw['NAME'][0]
    version = raw['VERSION'][0]
    summary = raw.get('DESC',[''])[0]
    meta = component_metadata().get(name,{})
    return dict(
        id=name,name=meta.get('name',name),source='pacman',repo=repo,
        version=version,summary=summary,description=summary,homepage=raw.get('URL',[''])[0],
        categories=categories(summary,raw.get('GROUPS',[])),installed=name in local,
        installedVersion=local.get(name,''),size=int(raw.get('CSIZE',['0'])[0]),
        desktopId=meta.get('desktopId',''),license=', '.join(raw.get('LICENSE',[])),
        architecture=raw.get('ARCH',[''])[0],dependencies=raw.get('DEPENDS',[]),
    )


def catalog(query, repo, category, page):
    repos=[entry['id'] for entry in repositories()]
    if repo and repo not in repos:
        raise StoreError('The selected Pacman repository is not enabled.')
    local=installed()
    query=query.casefold()
    rows={}
    for source in ([repo] if repo else repos):
        for name, raw in database(source).items():
            if name in rows:
                continue
            summary=raw.get('DESC',[''])[0]
            if query and query not in (name+' '+summary).casefold():
                continue
            if category and category not in categories(summary,raw.get('GROUPS',[])):
                continue
            rows[name]=(source,raw)
    keys=sorted(rows,key=lambda name:(name!=query,not name.startswith(query),name))
    return [normalize(*rows[name],local) for name in keys[page*PAGE_SIZE:(page+1)*PAGE_SIZE]],len(keys),False


def alternatives(name):
    name=package_name(name)
    local=installed()
    return [normalize(repo['id'],item,local) for repo in repositories() if (item:=database(repo['id']).get(name))]


def local_fields(name, version):
    folder=DB/'local'/f'{name}-{version.split(":",1)[-1]}'
    try:
        return fields((folder/'desc').read_text())
    except FileNotFoundError:
        return {'NAME':[name],'VERSION':[version]}


def installed_items():
    local=installed()
    return [normalize('',local_fields(name,version),local) for name,version in local.items()]


def details(name, repo=''):
    choices=alternatives(name)
    chosen=next((item for item in choices if not repo or item['repo']==repo),None)
    if chosen is None and not repo:
        local=installed()
        if name in local:
            chosen=normalize('',local_fields(name,local[name]),local)
    if chosen is None:
        raise StoreError('This package is no longer available from the selected source.')
    return dict(chosen,pacmanChoices=choices)
