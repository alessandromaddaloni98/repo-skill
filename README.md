# repo-skill

**A team's knowledge is not lost because nobody writes it down. It is lost because it
gets written where nobody finds it again.**

A snippet in a chat thread, a model trained on the laptop of whoever trained it, a
guide in a wiki nobody has opened in months. The cost is not producing the asset: it
is remembering that it exists.

![From capture to browsing: the skill encapsulates a project asset into a folder with
skill.json, README and files; the folder lands in data/assets/, where the catalog makes
it browsable and downloadable.](docs/img/flow.svg)

## The insight

The right moment to capture a reusable asset is **not afterwards**, when it takes
discipline and time nobody has. It is **while you are building it** — inside the coding
agent that is already writing it, the one that already has the files, the dependencies
and the reason that code exists sitting in its context.

Three choices follow from that, and they hold up the whole project:

1. **A format before an application.** The core is not the app: it is `skill.json`, a
   minimal schema describing a reusable asset. Anyone can produce it, read it, or write
   another frontend for it.
2. **Capture lives in the agent.** Publishing is not opening a portal and filling in a
   form: it is one sentence to the agent that already has the context. A *skill*
   encapsulates the asset, generalizes it and strips its secrets.
3. **The package is complete, not a pointer.** What you download is ready to use —
   metadata, guide and files — not a link to something that may still exist.

This repo holds the standard and a **reference implementation** of both sides: the skill
that captures, and the catalog that makes the result findable.

## The standard: `skill.json`

Every asset is a folder. The folder is the unit of exchange:

```
<asset-slug>/
  skill.json     # metadata
  README.md      # self-contained mini guide
  files/         # the asset files, generalized and free of secrets
```

```json
{
  "name": "Retry HTTP client",
  "description": "HTTP client with exponential backoff and jitter.",
  "type": "code",
  "author": "your-name",
  "project": "project-name",
  "files": ["files/retry_client.py"],
  "image": "cover.png"
}
```

Four types, deliberately few: `code`, `model`, `guide`, `agent`.
`image` is optional; without it, the catalog falls back to a per-type thumbnail.

## The two sides

**Capture — the skill.** It is installed in the *producing* project. From a prompt it
generates the asset folder: it copies the files needed at runtime, replaces hard-coded
values with placeholders and removes every secret. It does not publish and does not
upload anything: it only produces local files.

The same skill ships in two formats, one per agent, with identical behavior:

| Agent | Path |
|---|---|
| Codex | [`.agents/repo-skill-publish/SKILL.md`](.agents/repo-skill-publish/SKILL.md) |
| Claude Code | [`.claude/skills/repo-skill-publish/SKILL.md`](.claude/skills/repo-skill-publish/SKILL.md) |

The two files differ **only** in the frontmatter, as their respective formats require;
the body is identical. When you change one, carry the same change over to the other.

**Browsing — the app.** A server-rendered Flask app reads the asset folders, shows them
as a browsable catalog with search and filters, highlights what is new and lets you
download the complete package.

## Setup

Requires **Python 3.10+** (tested on 3.13).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # the defaults are fine for running locally
python app.py
```

App on http://localhost:8515. The catalog starts **empty**: it fills up with the assets
you put in `data/assets/`.

## Configuration

All through `.env` (see `.env.example`). Very little is needed: `FLASK_ENV` and
`SECRET_KEY`. No remote storage and no credentials — the catalog is the set of folders
in `data/assets/`, read from disk.

## Publishing an asset

The intended path is the skill: you install it in the project you want to extract the
asset from, ask the agent to encapsulate it, and copy the generated folder into
`data/assets/`.

## Extending it

That last copy is the manual step, and it is the one worth automating. The natural
target is the storage a team already shares: a SharePoint document library, a OneDrive
folder, a shared drive. Put the asset folders there and the last mile closes — the skill
generates the folder, it lands in the shared location, and every teammate's catalog
picks it up without a `git pull` and without anyone touching this repo.

There are two ways in, and they cost very differently.

**Point the app at a synced folder.** If the shared storage is already mirrored to disk
by a sync client, nothing has to change conceptually: the asset folders are still
folders. Set `ASSETS_DIR` in [`app/config.py`](app/config.py) to that path — it is a
constant today, so making it read an environment variable is a one-line change.

**Read the remote API directly.** No sync client, at the cost of credentials and token
refresh (Microsoft Graph, in the SharePoint/OneDrive case). Listing the catalog is the
easy half: [`app/catalog_store.py`](app/catalog_store.py) is the single read point, and
everything upstream of it consumes normalized records. The other half is the download
path — [`app/blueprints/download.py`](app/blueprints/download.py) and
[`app/packager.py`](app/packager.py) still open the asset folder on disk through the
record's `_dir` to serve cover images, single files and the zipped package. A remote
store has to fetch those bytes too, so plan for both.

The same seam supports a database, an object store, or a catalog assembled from several
sources at once. `skill.json` is the contract, and it does not care where the folder
lives.

None of this ships here on purpose: this repo stays offline and dependency-light, so it
runs with nothing but Flask and a directory.

## Structure

```
app/            Flask application (factory, blueprints, templates, static)
data/assets/    asset folders <slug>/skill.json + files: the source of the catalog
data/catalog/   seen.json (the "new items" state)
downloads/      downloaded packages
docs/img/       documentation images
.agents/        capture skill, Codex format
.claude/skills/ capture skill, Claude Code format
```

## Status

A working reference implementation, not a finished product. The catalog is derived from
local files (no database) and there is no authentication. The step from generated folder
to catalog — the last mile of capture — is still manual: you copy the folder into
`data/assets/`. See [Extending it](#extending-it) on closing that gap with shared
storage.

## License

MIT — see [LICENSE](LICENSE).
