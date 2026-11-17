# Direct AUR builds are opt-in and run makepkg as the user's own unprivileged account.
import os
import pathlib
import re
import tempfile
import urllib.parse

from . import network, pacman_catalog
from .runtime import StoreError, emit, package_name, run, stream, user_state

API='https://aur.archlinux.org/rpc/v5'


def enabled():
    return os.geteuid()!=0 and (user_state()/'enable-aur').is_file()


def configure(value):
    if type(value) is not bool:
        raise StoreError('Choose whether to enable the AUR.')
    path=user_state()/'enable-aur'
    if value:
        path.touch(mode=0o600)
    else:
        path.unlink(missing_ok=True)
    return {'aurEnabled':value}


def require_enabled():
    if not enabled():
        raise StoreError('Enable direct AUR access in App Store Settings first.')


def fetch(endpoint):
    require_enabled()
    payload=network.fetch(API+endpoint)
    if not isinstance(payload,dict) or payload.get('type')=='error':
        raise StoreError('The AUR service could not answer the request.')
    return payload.get('results',[])


def normalize(item,local):
    name=item['Name']
    summary=item.get('Description') or 'Community package from the AUR'
    return dict(id=name,name=name,source='aur',repo='aur',summary=summary,description=summary,
        version=item['Version'],installed=name in local,installedVersion=local.get(name,''),
        categories=pacman_catalog.categories(summary),packageBase=item['PackageBase'],
        homepage='https://aur.archlinux.org/packages/'+name,license='AUR package recipe',
        maintainer=item.get('Maintainer') or 'Orphaned',size=0)


def search(query,category,page):
    if len(query)<2:
        return [],0,False
    local=pacman_catalog.installed()
    rows=[normalize(item,local) for item in fetch('/search/'+urllib.parse.quote(query,safe='')+'?by=name-desc')]
    rows=[item for item in rows if not category or category in item['categories']]
    rows.sort(key=lambda item:(item['id']!=query,not item['id'].startswith(query),item['id']))
    return rows[page*24:(page+1)*24],len(rows),False


def details(name):
    name=package_name(name)
    rows=fetch('/info?'+urllib.parse.urlencode({'arg[]':name}))
    if not rows:
        raise StoreError('This package is unavailable in the AUR.')
    return normalize(rows[0],pacman_catalog.installed())


def clone(base,work):
    run(['git','clone','--depth','1','--','https://aur.archlinux.org/'+package_name(base)+'.git',str(work)],timeout=60)
    commit=run(['git','-C',str(work),'rev-parse','HEAD']).stdout.strip()
    return commit


def plan(request):
    item=details(request.get('id'))
    with tempfile.TemporaryDirectory(prefix='amogos-aur-') as temporary:
        work=pathlib.Path(temporary)/'recipe'
        commit=clone(item['packageBase'],work)
        recipe=work/'PKGBUILD'
        if recipe.is_symlink() or not recipe.is_file() or recipe.stat().st_size>65536:
            raise StoreError('The AUR recipe cannot be safely displayed for review.')
        source=recipe.read_text(errors='replace')
    change=dict(id=item['id'],action=request.get('operation','install'),version=item['version'],fromVersion=item['installedVersion'],repo='aur')
    return dict(source='aur',id=item['id'],summary=item['name'],changes=[change],commit=commit,recipe=source,
        note='Review the PKGBUILD and its referenced files before continuing. The recipe runs with your desktop user permissions.')


def apply(request):
    require_enabled()
    name=package_name(request.get('id'))
    commit=request.get('commit','')
    if not isinstance(commit,str) or not re.fullmatch('[0-9a-f]{40}',commit):
        raise StoreError('Review the package recipe before installing.')
    item=details(name)
    with tempfile.TemporaryDirectory(prefix='amogos-aur-') as temporary:
        work=pathlib.Path(temporary)/'recipe'
        if clone(item['packageBase'],work)!=commit:
            raise StoreError('The AUR recipe changed. Review the new version first.')
        config=pathlib.Path(temporary)/'makepkg.conf'
        config.write_text('source /etc/makepkg.conf\nPACMAN_AUTH=(pkexec /usr/libexec/amogos-arch-makepkg-pacman)\n')
        emit('Building '+name+' with makepkg.')
        stream(['sh','-c','cd "$1" && exec makepkg --config "$2" --syncdeps --install --noconfirm','makepkg',str(work),str(config)],timeout=7200)
    if name not in pacman_catalog.installed():
        raise StoreError('makepkg finished, but the selected package is not installed.')
    emit('AUR package installed.',1,done=True)
