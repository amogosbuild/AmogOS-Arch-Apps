# Enforce one comment per maintained source file and keep deployment details out of Git.
import pathlib
import re
import subprocess
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
SLASH={'.dart','.cc','.h','.js','.jsonc','.rules'}
HASH={'.py','.sh','.yaml','.yml','.conf','.ini','.service','.desktop','.hook','.script','.plymouth','.cmake','.theme','.gitignore'}
NAMES={'CMakeLists.txt','PKGBUILD','defaults','prepare','finish','cleanup','start','session','post-install'}
files=subprocess.check_output(['git','-C',str(ROOT),'ls-files','-z','--cached','--others','--exclude-standard']).decode().split('\0')
count=0
errors=[]
for name in sorted(set(files)):
    path=ROOT/name
    if not name or not path.is_file() or path.is_symlink() or path.name.startswith('generated_') or path.name=='pubspec.lock':
        continue
    if path.suffix not in SLASH | HASH | {'.policy'} and path.name not in NAMES and not (path.parent.name=='packaging' and not path.suffix):
        continue
    source=path.read_text(encoding='utf-8')
    if path.suffix in SLASH:
        pattern=r'(?m)^[ \t]*//[^\n]*(?:\n|$)'
        marker='// '
    elif path.suffix=='.policy':
        pattern=r'<!--[^\n]*-->(?:\n|$)'
        marker='<!-- '
    else:
        pattern=r'(?m)^[ \t]*#[^\n]*(?:\n|$)'
        marker='# '
    comments=list(re.finditer(pattern,source))
    if '--normalize' in sys.argv and len(comments)!=1 and path.suffix!='.policy':
        if comments:
            for comment in reversed(comments[1:]):
                source=source[:comment.start()]+source[comment.end():]
        else:
            label=path.stem.replace('_',' ').replace('-',' ')
            source=f'{marker}AmogOS Arch {label}.\n'+source
        path.write_text(source,encoding='utf-8')
        comments=list(re.finditer(pattern,source))
    if len(comments)!=1:
        errors.append(f'{name}: {len(comments)} comments')
    if re.search(r'/(?:srv)/[A-Za-z0-9_.-]+|(?i:[A-Z]:[/\\]Users[/\\][A-Za-z0-9_.-]+)',source):
        errors.append(f'{name}: private build path')
    count+=1
if errors:
    raise SystemExit('\n'.join(errors))
print(f'Checked one comment in {count} maintained files.')
