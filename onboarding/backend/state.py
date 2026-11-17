# Keep onboarding state and the SDDM handoff in root-owned files.
import json
import os
import pathlib
import pwd
import re
import subprocess
import tempfile

ROOT=pathlib.Path('/var/lib/amogos-arch-onboarding')
TEMP_USER='amogos-setup'
TEMP_HOME='/home/'+TEMP_USER
LIVE_USER='amogos-live'
SDDM=pathlib.Path('/etc/sddm.conf.d')
SESSIONS={'plasma':'plasma.desktop','gnome':'gnome.desktop','lxqt':'lxqt.desktop'}


def command(*args, **kwargs):
    return subprocess.run(args,check=True,text=True,**kwargs)


def account(name):
    try:
        return pwd.getpwnam(name)
    except KeyError:
        return None


def atomic(path,text,mode=0o600):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,temporary=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name+'.')
    try:
        with os.fdopen(fd,'w') as output:
            output.write(text)
            os.fchmod(output.fileno(),mode)
        os.replace(temporary,path)
    finally:
        pathlib.Path(temporary).unlink(missing_ok=True)


def record(path,value):
    atomic(path,json.dumps(value)+'\n')


def read(path):
    return json.loads(path.read_text()) if path.is_file() else {}


def autologin(user,desktop,path):
    atomic(path,f'[Autologin]\nUser={user}\nSession={SESSIONS[desktop]}\nRelogin=false\n',0o644)


def validate(data):
    if not isinstance(data,dict):
        raise ValueError('Provide valid onboarding settings.')
    name,username,password,theme=(data.get(key) for key in ('name','username','password','theme'))
    if not isinstance(name,str) or not 1<=len(name.strip())<=80 or re.search(r'[:\x00-\x1f\x7f]',name):
        raise ValueError('Enter a valid full name.')
    if not isinstance(username,str) or not re.fullmatch(r'[a-z_][a-z0-9_-]{0,30}',username) or username in (TEMP_USER,LIVE_USER,'root'):
        raise ValueError('Choose a valid username.')
    if not isinstance(password,str) or not 8<=len(password)<=1024 or re.search(r'[\x00\r\n]',password):
        raise ValueError('Use a password with at least eight characters and no line breaks.')
    if theme not in ('light','dark') or any(type(data.get(key)) is not bool for key in ('autoLogin','largerText','highContrast')):
        raise ValueError('Choose valid appearance and login options.')
    return name,username,password,theme
