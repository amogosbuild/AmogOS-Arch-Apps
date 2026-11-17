# Installed software is listed locally and remains available when online catalogs are unreachable.
from . import pacman_catalog, appimages, appimage_catalog, flatpak_local
from .network import cached
from .runtime import StoreError


def pacman_items():
    return pacman_catalog.installed_items()


def images():
    values=[]
    for key,entry in appimages.reconcile().items():
        data=cached(appimage_catalog.API+"/content/data/"+key+"?format=json") or {}
        raw=next((v for v in data.get("data",[]) if str(v.get("id"))==key),dict(id=key,name=entry["name"],version=entry["version"]))
        item=appimage_catalog.normalize(raw,{key:entry})
        item.update(version=entry["version"],installedVersion=entry["version"],categories=entry.get("categories",item["categories"]))
        values.append(item)
    return values


def search(request):
    source=request.get("source","all")
    page=request.get("page",0)
    if type(page) is not int or not 0<=page<=1000000:
        raise StoreError("Invalid installed-software page.")
    jobs={"pacman":pacman_items,"flatpak":lambda:flatpak_local.listing("system")+flatpak_local.listing("user"),"appimage":images}
    if source!="all" and source not in jobs:
        raise StoreError("Choose a supported installed-software source.")
    query=str(request.get("query","")).strip().casefold()
    category=str(request.get("category",""))
    rows=[]
    warnings=[]
    totals={}
    for key,job in jobs.items():
        if source not in ("all",key):continue
        try:
            values=job()
            values=[v for v in values if (not query or query in " ".join(str(v.get(k,"")) for k in ("id","name","summary")).casefold()) and (not category or category in v.get("categories",[]))]
            totals[key]=len(values)
            rows.extend(values)
        except Exception as error:
            warnings.append(dict(source=key,message=str(error)))
    rows.sort(key=lambda v:(v["name"].casefold(),v["source"],v["id"],v.get("scope",""),v.get("branch","")))
    return dict(items=rows[page*24:(page+1)*24],totals=totals,warnings=warnings,page=page,total=len(rows),hasMore=(page+1)*24<len(rows))
