# The dispatcher accepts fixed JSON actions and never accepts arbitrary privileged commands.
import json
import os
import pathlib
import sys

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from amogos_store import alternatives, aur, pacman_transactions, appimages, catalog, flatpak_transactions, inventory, updates, jobs
from amogos_store.runtime import StoreError

PRIVILEGED={"pacman-plan","pacman-apply","refresh","flatpak-plan","flatpak-apply","flatpak-source"}
STREAMED={"pacman-apply","flatpak-apply","refresh","appimage-install","appimage-remove","aur-apply"}


def main():
    if len(sys.argv)!=2:
        raise StoreError("Choose one App Store action.")
    action=sys.argv[1]
    raw=sys.stdin.buffer.read(65537)
    if len(raw)>65536:
        raise StoreError("The request is too large.")
    request=json.loads(raw or b"{}")
    if not isinstance(request,dict):
        raise StoreError("Use a JSON object request.")
    user_flatpak=action in ("flatpak-plan","flatpak-apply") and request.get("scope")=="user"
    if action in PRIVILEGED and os.geteuid()!=0 and not user_flatpak:
        raise StoreError("System changes require App Store authentication.")
    if action in jobs.ACTIONS and not user_flatpak and jobs.enabled():
        return jobs.start(action,request)
    if action=="aur-settings": return {"aurEnabled":aur.enabled()}
    if action=="aur-configure": return aur.configure(request.get("enabled"))
    if action=="aur-plan": return aur.plan(request)
    if action=="aur-apply": return aur.apply(request)
    if action=="transactions": return jobs.listing()
    if action=="catalog": return catalog.search(request)
    if action=="installed": return inventory.search(request)
    if action=="details": return catalog.details(request)
    if action=="alternatives": return alternatives.get(request)
    if action=="sources": return catalog.sources()
    if action=="updates":
        return updates.get()
    if action=="pacman-plan": return pacman_transactions.plan(request)
    if action=="pacman-apply": return pacman_transactions.apply(request)
    if action=="refresh": return pacman_transactions.refresh()
    if action=="flatpak-plan": return flatpak_transactions.plan(request)
    if action=="flatpak-apply": return flatpak_transactions.apply(request)
    if action=="flatpak-source": return flatpak_transactions.configure(request.get("enabled"))
    if action=="appimage-install": return appimages.install(request)
    if action=="appimage-remove": return appimages.remove(request.get("id"))
    if action=="launch": return catalog.launch(request)
    if action=="open-url": return catalog.open_link(request)
    raise StoreError("Unsupported App Store action.")


try:
    result=main()
    if result is not None:
        print(json.dumps(result),flush=True)
except Exception as error:
    action=sys.argv[1] if len(sys.argv)>1 else ""
    print(json.dumps(dict(error=True,message=str(error),done=False)),flush=True)
    raise SystemExit(1)
