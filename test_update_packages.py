import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


module = importlib.util.spec_from_file_location("updater", Path(__file__).with_name("update-packages.py"))
updater = importlib.util.module_from_spec(module)
module.loader.exec_module(updater)


class UpdatePackagesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.bundle = f"{'1' * 64}  bundle.tar.gz\n"

    def spec(self, name, depends=None, upstream=None, source=None):
        folder = self.root / "specs" / name
        folder.mkdir(parents=True)
        path = folder / f"{name}.spec"
        lines = [
            f"Name: {name}", "Version: 1.9", "Release: 3%{?dist}",
            f"URL: {upstream or updater.HYPRWM + name}",
            "Source0: " + (source or "%{url}/archive/v%{version}/%{name}-%{version}.tar.gz"),
            "Source1: https://example.org/bundle.tar.gz",
        ]
        if depends:
            lines.append(f"BuildRequires: pkgconfig({depends}) >= 1.0")
        path.write_text("\n".join(lines) + "\n")
        suffix = "xz" if source else "gz"
        path.with_name("sources").write_text(f"{'0' * 64}  {name}-1.9.tar.{suffix}\n" + self.bundle)
        return path

    def test_hypr_update_rebuilds_transitive_dependents_once(self):
        library = self.spec("library")
        toolkit = self.spec("toolkit", "library")
        app = self.spec("app", "toolkit")
        unrelated = self.spec("unrelated")
        blob = b"new library tarball"

        def fetch(url):
            if url.startswith("https://api.github.com/repos/hyprwm/"):
                tag = "v1.10" if "/library/" in url else "v1.9"
                return io.BytesIO(json.dumps({"tag_name": tag}).encode())
            self.assertEqual(url, updater.HYPRWM + "library/archive/v1.10/library-1.10.tar.gz")
            return io.BytesIO(blob)

        with patch.object(updater, "fetch", fetch):
            updater.update(self.root, "hyprland")
            self.assertEqual(updater.update(self.root, "hyprland"), [])
        self.assertIn("Version: 1.10\nRelease: 1%{?dist}", library.read_text())
        self.assertEqual(library.with_name("sources").read_text(),
                         f"{hashlib.sha256(blob).hexdigest()}  library-1.10.tar.gz\n" + self.bundle)
        for path in (toolkit, app):
            self.assertIn("Version: 1.9\nRelease: 4%{?dist}", path.read_text())
        self.assertIn("Release: 3%{?dist}", unrelated.read_text())

    def test_ffmpeg_ignores_prereleases_and_leaves_bundled_pins(self):
        path = self.spec("ffmpeg-full", upstream=updater.FFMPEG,
                         source="%{url}/releases/%{name}-%{version}.tar.xz")
        published = b'<a href="ffmpeg-1.10.tar.xz"> <a href="ffmpeg-2.0-rc1.tar.xz">'
        blob = b"new ffmpeg tarball"

        def fetch(url):
            if url == updater.FFMPEG + "/releases/":
                return io.BytesIO(published)
            self.assertEqual(url, updater.FFMPEG + "/releases/ffmpeg-full-1.10.tar.xz")
            return io.BytesIO(blob)

        with patch.object(updater, "fetch", fetch):
            updater.update(self.root, "ffmpeg")
        self.assertIn("Version: 1.10\nRelease: 1%{?dist}", path.read_text())
        self.assertEqual(path.with_name("sources").read_text(),
                         f"{hashlib.sha256(blob).hexdigest()}  ffmpeg-full-1.10.tar.xz\n" + self.bundle)


if __name__ == "__main__":
    unittest.main()
