import json
import os
import re
import unicodedata

import ckanapi
import humanize
import requests
import tqdm


def safe_mkdir(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        pass
    return path


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def download_file(url, out_fd):
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        total = int(r.headers.get("content-length", 0))
        chunk_size = 1 << 20
        progress_bar = tqdm.tqdm(total=total, unit="iB", unit_scale=True)
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=chunk_size):
            progress_bar.update(len(chunk))
            out_fd.write(chunk)
        progress_bar.close()


CONFIG_FILE = "ckanmirror.json"


def mirror(destination, remote, package):
    resoures = package["resources"]

    tmp_dir = safe_mkdir(os.path.join(destination, "tmp"))
    remote_dir = safe_mkdir(os.path.join(destination, slugify(remote.address)))
    package_dir = safe_mkdir(os.path.join(remote_dir, slugify(package["id"])))

    for resource in resoures:
        resource_dir = safe_mkdir(os.path.join(package_dir, slugify(resource["id"])))

        package_fname = "package-{}.json".format(slugify(package["id"]))
        package_tmp = os.path.join(tmp_dir, package_fname) + ".tmp"
        package_dest = os.path.join(resource_dir, package_fname)

        meta_fname = "resource-{}.json".format(slugify(resource["id"]))
        meta_tmp = os.path.join(tmp_dir, meta_fname) + ".tmp"
        meta_dest = os.path.join(resource_dir, meta_fname)

        if os.access(meta_dest, os.R_OK):
            continue

        resource_metadata = remote.action.resource_show(id=resource["id"])
        with open(meta_tmp, "w") as f:
            json.dump(resource_metadata, f)
        with open(package_tmp, "w") as f:
            json.dump(package, f)

        data_fname = resource["url"].split("/")[-1]
        data_tmp = os.path.join(tmp_dir, data_fname) + ".tmp"
        data_dest = os.path.join(resource_dir, data_fname)
        with open(data_tmp, "wb") as f:
            print(resource["url"], humanize.naturalsize(resource["size"] or 0))
            download_file(resource["url"], f)

        os.rename(data_tmp, data_dest)
        os.rename(package_tmp, package_dest)
        os.rename(meta_tmp, meta_dest)


def cli():
    # we expect to find a ckanmirror.json file in the current directory
    if not os.access(CONFIG_FILE, os.R_OK):
        raise RuntimeError("{} not found in current directory".format(CONFIG_FILE))

    with open(CONFIG_FILE) as f:
        config = json.load(f)

    remote = ckanapi.RemoteCKAN(config["remote"], apikey=config["apikey"])
    package_id = config["package_id"]
    package = remote.action.package_show(id=package_id)
    destination = "."
    mirror(destination, remote, package)
