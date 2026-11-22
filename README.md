# packages

RPMs for software that isn't in the Fedora repos, built from pinned upstream
sources on GitHub Actions and published as a signed dnf repository on GitHub
Pages. It exists so [Ruizite](https://github.com/lutvzn/ruizite) doesn't depend
on other people's COPRs.

| Package | Version | Notes |
|---|---|---|
| `hyprland` | 0.57.2 | No hyprpm/plugin headers, no UWSM session, no default wallpapers (saves 48 MB) |
| `aquamarine` | 0.16.0 | |
| `hyprcursor` | 0.1.14 | |
| `hyprgraphics` | 0.6.0 | |
| `hyprlang` | 0.6.8 | |
| `hyprutils` | 0.14.4 | Newer than Fedora's 0.7.1 and replaces it |
| `hyprwire` | 0.3.1 | |
| `hyprland-protocols-devel` | 0.8.0 | Build-only |
| `hyprwayland-scanner-devel` | 0.4.6 | Build-only. Fedora's 0.4.2 generates code GCC 16 rejects |

Built for the Fedora release Anatase uses (currently 45), x86_64.

## Trust

- **Sources**: every source tarball has a SHA-256 in `specs/<package>/sources`.
  `build.sh` refuses to build a source without one, so a version only changes
  through a reviewed commit.
- **Build**: a clean `fedora:45` container on GitHub Actions, with actions
  pinned to commit SHAs. Build dependencies come only from Fedora.
- **Signing**: RPMs and `repomd.xml` are signed with the key in
  [`RPM-GPG-KEY-lutvzn-packages`](./RPM-GPG-KEY-lutvzn-packages):

  ```
  A7CC 0893 6B30 B427 873E  2B2D 15DF 8D57 EA7D 3A64
  ```

  The private key only exists as the `GPG_PRIVATE_KEY` Actions secret. If it's
  ever lost or leaked, generate a new one, replace the public key and
  fingerprint here and in the workflow, and update the pinned key in Ruizite.

## Using the repository

In a Containerfile, pin the key from this repo and limit the repo to the
packages you need:

```dockerfile
RUN --mount=type=bind,source=keys/lutvzn-packages.gpg,target=/tmp/lutvzn-packages.gpg \
    dnf -y install --setopt=install_weak_deps=False \
        --repofrompath='lutvzn,https://lutvzn.github.io/packages/fedora/$releasever/$basearch/' \
        --setopt=lutvzn.gpgcheck=1 \
        --setopt=lutvzn.repo_gpgcheck=1 \
        --setopt=lutvzn.gpgkey=file:///tmp/lutvzn-packages.gpg \
        --setopt=lutvzn.includepkgs='hyprland,aquamarine,hyprcursor,hyprgraphics,hyprlang,hyprutils,hyprwire' \
        hyprland
```

On a regular Fedora system:

```bash
sudo curl -o /etc/yum.repos.d/lutvzn-packages.repo https://lutvzn.github.io/packages/lutvzn-packages.repo
```

## Adding or updating a package

1. Add or edit `specs/<name>/<name>.spec`.
2. Put the SHA-256 of every source in `specs/<name>/sources`
   (`sha256sum <file> > sources`).
3. Add the name to `PACKAGES` in `build.sh`, after anything it builds against.
4. Push to `main`. The workflow builds every package, signs them and publishes
   the repository.

To build locally without publishing:

```bash
podman run --rm -v "$PWD:/src:Z" -w /src registry.fedoraproject.org/fedora:45 ./build.sh
```

When Anatase moves to a new Fedora release, change the container in
`.github/workflows/build.yml` and run the workflow again.
