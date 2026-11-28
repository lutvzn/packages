"""Update specs for one upstream group and print a pull request summary."""

import argparse
import hashlib
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


HYPRWM = "https://github.com/hyprwm/"
FFMPEG = "https://ffmpeg.org"
VERSION = r"[0-9]+(?:\.[0-9]+)+"


def fetch(url):
    request = Request(url, headers={"User-Agent": "adamite-pkgs-updater"})
    if url.startswith("https://api.github.com/") and (token := os.getenv("GH_TOKEN")):
        request.add_unredirected_header("Authorization", f"Bearer {token}")
    return urlopen(request, timeout=30)


def version_key(version):
    if not re.fullmatch(VERSION, version):
        raise ValueError(f"Unsupported version: {version!r}")
    return tuple(map(int, version.split(".")))


def latest_version(upstream):
    if upstream == FFMPEG:
        with fetch(f"{FFMPEG}/releases/") as response:
            index = response.read().decode()
        return max(re.findall(rf'href="ffmpeg-({VERSION})\.tar\.xz"', index), key=version_key)

    repo = upstream.removeprefix(HYPRWM)
    with fetch(f"https://api.github.com/repos/hyprwm/{repo}/releases/latest") as response:
        release = json.load(response)
    return release["tag_name"].removeprefix("v")


def field(spec, name):
    match = re.search(rf"^{name}:[ \t]+(\S+)[ \t]*$", spec, re.MULTILINE)
    if not match:
        raise ValueError(f"Missing or unsupported {name} in spec")
    return match


def replace(spec, match, value):
    start, end = match.span(1)
    return spec[:start] + value + spec[end:]


def source_url(spec, version):
    macros = {"url": field(spec, "URL")[1], "name": field(spec, "Name")[1], "version": version}
    url = re.sub(r"%\{(\w+)\}", lambda m: macros[m[1]], field(spec, "Source0?")[1])
    if not url.startswith("https://"):
        raise ValueError(f"Expected an HTTPS source URL: {url}")
    return url


def update_checksum(path, old_url, new_url):
    old_name = urlsplit(old_url).path.rsplit("/", 1)[-1]
    new_name = urlsplit(new_url).path.rsplit("/", 1)[-1]
    contents = path.read_text()
    pin = re.compile(rf"^[0-9a-f]{{64}}  {re.escape(old_name)}$", re.MULTILINE)
    if old_name == new_name or len(pin.findall(contents)) != 1:
        raise ValueError(f"Expected one versioned checksum for {old_name} in {path}")
    with fetch(new_url) as response:
        digest = hashlib.file_digest(response, "sha256").hexdigest()
    return pin.sub(f"{digest}  {new_name}", contents)


def update(root, group):
    paths = {path.stem: path for path in sorted((root / "specs").glob("*/*.spec"))}
    specs = {name: path.read_text() for name, path in paths.items()}
    upstreams = {name: field(spec, "URL")[1] for name, spec in specs.items()}
    selected = {
        name: url for name, url in upstreams.items()
        if (url.startswith(HYPRWM) if group == "hyprland" else name == "ffmpeg-full")
    }
    if not selected:
        raise ValueError(f"No specs found for {group}")
    with ThreadPoolExecutor(max_workers=4) as pool:
        releases = dict(zip(selected, pool.map(latest_version, selected.values())))

    updates = {}
    for name, new in releases.items():
        old = field(specs[name], "Version")[1]
        if version_key(new) > version_key(old):
            updates[name] = (old, new)

    # A version bump may change the ABI. Walk the in-repo pkg-config BuildRequires
    # transitively so no dependent RPM is reused with its old library requirements.
    affected = set(updates)
    pending = {
        name: set(re.findall(r"^BuildRequires:\s+pkgconfig\(([^)]+)\)", spec, re.MULTILINE))
        for name, spec in specs.items() if name not in affected
    }
    while dependents := {name for name, deps in pending.items() if deps & affected}:
        affected.update(dependents)
        for name in dependents:
            del pending[name]

    changes = {}
    summary = []
    for name in sorted(affected):
        path, spec = paths[name], specs[name]
        release = field(spec, "Release")
        match = re.fullmatch(r"([0-9]+)(%\{\?dist\})", release[1])
        if not match:
            raise ValueError(f"Unsupported Release in {path}: {release[1]}")
        if name in updates:
            old, new = updates[name]
            sources = path.with_name("sources")
            changes[sources] = update_checksum(sources, source_url(spec, old), source_url(spec, new))
            spec = replace(spec, release, f"1{match[2]}")
            spec = replace(spec, field(spec, "Version"), new)
            summary.append(f"- `{name}`: {old} → {new}")
        else:
            new_release = int(match[1]) + 1
            spec = replace(spec, release, f"{new_release}{match[2]}")
            summary.append(f"- Rebuild `{name}` (release {new_release}) against the updated dependencies")
        changes[path] = spec

    for path, contents in changes.items():
        path.write_text(contents)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=("hyprland", "ffmpeg"))
    for item in update(Path(__file__).resolve().parent, parser.parse_args().group):
        print(item)
