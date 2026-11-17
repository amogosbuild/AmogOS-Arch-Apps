# Review Pacman transactions with printable flags; --nosave is applied only by the privileged worker.
from . import pacman_catalog
from .runtime import StoreError, consume_plan, digest, emit, package_name, run, save_plan, stream, transaction_lock

PROTECTED = {
    'base','filesystem','glibc','linux-zen','pacman','archlinux-keyring',
    'systemd','systemd-sysvcompat','sudo','polkit','sddm','plasma-desktop',
    'amogos-arch-store','amogos-arch-system','amogos-arch-onboarding',
}
PRINT_FORMAT = '%r\t%n\t%v\t%s'


def install_target(name, repo):
    name=package_name(name)
    if not repo:
        return name
    if repo not in {item['id'] for item in pacman_catalog.repositories()}:
        raise StoreError('The selected Pacman repository is not enabled.')
    return f'{repo}/{name}'


def additions(targets, repair=False):
    command=['pacman','-Su','--noconfirm','--color','never']
    if not repair:
        command.append('--needed')
    result=run([*command,'--print','--print-format',PRINT_FORMAT,'--',*targets])
    local=pacman_catalog.installed()
    changes=[]
    for line in result.stdout.splitlines():
        if '\t' not in line:
            continue
        repo, name, version, size=line.split('\t')
        previous=local.get(name,'')
        action='install' if not previous else 'reinstall' if previous==version else 'update'
        changes.append(dict(id=name,action=action,fromVersion=previous,version=version,size=int(size),repo=repo,automatic=name not in targets and f'{repo}/{name}' not in targets))
    return command, changes


def resolve(request):
    operation=request.get('operation','install')
    name=request.get('id','')
    full=request.get('fullUninstall',False)
    if not isinstance(full,bool):
        raise StoreError('Invalid full uninstall option.')
    repo=request.get('repo','')
    if not isinstance(repo,str):
        raise StoreError('Invalid package repository.')
    if operation=='remove':
        name=package_name(name)
        if name in PROTECTED:
            raise StoreError('This package is required by your AmogOS system.')
        local=pacman_catalog.installed()
        if name not in local:
            raise StoreError('This package is not installed.')
        flag='-Rns' if full else '-R'
        command=['pacman',flag,'--noconfirm','--color','never','--',name]
        result=run(['pacman','-Rs' if full else '-R','--print','--print-format','%n','--',name])
        removed=sorted(set(line.strip() for line in result.stdout.splitlines() if line.strip()))
        if name not in removed or any(item not in local for item in removed):
            raise StoreError('The removal list could not be verified. Review the transaction again.')
        if PROTECTED.intersection(removed):
            raise StoreError('This removal would affect a package required by your AmogOS system.')
        changes=[dict(id=item,action='remove',fromVersion=local[item],version='',size=0,repo='',automatic=item!=name) for item in removed]
        note=('Remove the package and its unused dependencies. Package-owned configuration files are removed without creating .pacsave backups. Files in your home folder are kept.' if full else 'Remove this package if no installed package requires it. Modified package configuration may be kept as .pacsave files.')
    elif operation in ('upgrade-system','update-selected','install','repair','update'):
        targets=[] if operation in ('upgrade-system','update-selected') else [install_target(name,repo)]
        command, changes=additions(targets,repair=operation=='repair')
        if targets:
            command.extend(['--',*targets])
        note='Pacman installs pending system upgrades in the same transaction to keep Arch packages compatible.'
    else:
        raise StoreError('Unsupported Pacman operation.')
    changes.sort(key=lambda item:item['id'])
    return dict(source='pacman',operation=operation,id=name,repo=repo,fullUninstall=full,summary='Update AmogOS 2 Pro (Arch)' if not name else f'{operation.capitalize()} {name}',changes=changes,command=command,note=note,downloadBytes=sum(item['size'] for item in changes),spaceBytes=0,fingerprint=digest([command,changes]))


def plan(request):
    with transaction_lock():
        return save_plan(resolve(request))


def apply(request):
    with transaction_lock():
        previous=consume_plan(request.get('token'),'pacman')
        current=resolve(previous)
        if current['fingerprint']!=previous['fingerprint']:
            raise StoreError('Package versions or dependencies changed. Review the transaction again.')
        if current['changes']:
            stream([*current['command']])
        emit('Pacman transaction complete.',1,done=True)


def refresh():
    with transaction_lock():
        stream(['pacman','-Sy','--noconfirm','--color','never'])
        emit('Package indexes refreshed.',1,done=True)


def updates():
    _, items=additions([])
    for item in items:
        item.update(source='pacman',name=item['id'])
    return dict(items=items,rebootRequired=False,pendingConfiguration=[])
