---
name: repo-skill-publish
description: Encapsulate an asset from the current project (script, .md, model weights, agent, text content from the prompt) into a folder ready for repo-skill — generates skill.json, README.md and the files/ subfolder with generalized, secret-free copies. Use it when the user says "publish to repo-skill", "prepare an asset for repo-skill", "encapsulate this asset for repo-skill".
---

# repo-skill — Generate an asset folder

Encapsulate an asset **already present in the current project** (a script, a `.md` file, model
weights, an agent definition, or text content supplied in the prompt) into a **folder ready for
repo-skill**: metadata, guide and files, generalized and free of secrets.

This skill **only generates local files in the current project**. It does not publish, upload or
update anything.

## Output — the only thing you produce

Create, at the root of the current project, exactly this structure:

```
repo-skill-assets/<asset-slug>/
  skill.json     # asset metadata
  README.md      # self-contained mini guide
  files/         # copies of the asset files (generalized, no secrets)
```

`<asset-slug>` = the title in lowercase, spaces and symbols → hyphens (e.g. "Retry HTTP client" →
`retry-http-client`). For text-only assets, `files/` stays empty (create the folder anyway).

## Non-negotiable constraints

The skill **must never**:

- invoke a publishing CLI or script;
- write to `/tmp` or any other system temporary directory;
- write to `data/assets/`;
- write to `downloads/`;
- upload anything to any remote document store;
- update `catalog.json` or any catalog;
- produce a `.env.example` or any other env/secrets example file.

Every output lives **only** inside `repo-skill-assets/<asset-slug>/` in the current project.

## What the user must declare

Before generating, the user **must** provide — ask if it is not in the prompt:

1. **Source** — which files make up the asset (one or more paths) or, for text-only
   `guide`/`agent` assets, the explicit content to encapsulate.
2. **Asset name / Title** — how to title the asset (the `name` field).
3. **User name** — the person associated with the asset (the `author` field).
4. **Project name** — the project the asset was used in (the `project` field).
5. **Type** — one of: `code`, `model`, `guide`, `agent`.

If **source, asset name, user name, project name or type** is missing, **stop and ask**.
Do not make them up.

Optional (infer, confirm when unsure): `description`.

## Procedure

### 1. Validate sources and boundaries

- Check that the source paths exist and are readable.
- Do not include whole directories, caches, build output, downloads, `.git`, `.venv`,
  `node_modules`, logs or temporary files.
- Include only the minimal structure needed to understand and reuse the asset.

### 2. Copy into `files/` — never modify the originals

- Create `repo-skill-assets/<asset-slug>/files/`.
- Copy **only** the asset files there. Do not touch the original files of the producing project.
- Generalize and sanitize **the copies** in `files/`, not the sources.
- For text-only assets (`guide`/`agent`): no files, the content goes into the README.

### 2b. If the source is a script: include the files it needs at runtime

A script is rarely enough on its own. When the source is a script (type `code`/`agent`),
`files/` **must** also include the associated files needed to run it. Procedure:

1. **Read the script** to find: referenced paths, constants, default arguments, and every
   file read/loaded at runtime.
2. **Copy into `files/`** both the script and those associated files. Typical categories:
   - weights/models: `*.pt`, `*.pth`, `*.onnx`, `*.safetensors`, `*.pkl`, `*.joblib`;
   - data/config: `*.txt`, `*.md`, `*.json`, `*.yaml`, `*.yml`, `*.toml`, `*.csv`;
   - templates, prompts, tokenizers, vocabularies and local configs.
3. **Ask for confirmation** when a reference is ambiguous (dynamic path, file not found,
   doubt about whether a file belongs). Do not guess.
4. **List everything** in `skill.json` (`files`): the script plus every associated file.
5. **Document** in the `README.md` the role of each associated file.

If an associated file is very large (e.g. weights >~100MB) or the asset is essentially the
model, consider type `model`; when copying it is impractical, document in the README how to
obtain it instead of including it in `files/`.

Secrets and non-reusable artifacts stay excluded (see steps 1 and 4).

### 3. Generalize project-specific code

- Replace hard-coded paths, resource names, endpoints, IDs and tenant/project values with
  **clear placeholders** (`<TENANT_ID>`, `./path/to/your/file`, `PROJECT_NAME`) or parameters
  at the top of the file.
- Remove logic coupled to non-reusable internal details; keep the reusable core.
- If generalizing would distort the asset, leave it as is but **document** in the README the
  points that need adapting.

### 4. Remove every secret — non-negotiable rule

**Never include** `.env`, `.env.example`, API keys, secrets, tokens, passwords,
connection strings, certificates or credentials:

- Inspect every file in `files/` and the README for credentials.
- Replace sensitive values with placeholders (`<API_KEY>`, `<SECRET>`).
- **Exclude** every `.env`, `.env.example`, `*.pem`, `*.key`, credential file or config holding secrets.
- **Do not generate** a `.env.example`. Document the required variables in the README (names and
  purpose), not in an env file.
- Search at least for: `api_key`, `apikey`, `token`, `secret`, `password`, `client_secret`,
  `connectionString`, `BEGIN PRIVATE KEY`, bearer tokens, URLs with credentials, long
  high-entropy keys.
- If a secret cannot be removed without breaking the asset, **stop and warn the user**.

### 5. Write `skill.json`

Schema (the only allowed types are `code`, `model`, `guide`, `agent`):

```json
{
  "name": "<title>",
  "description": "<short description>",
  "type": "code|model|guide|agent",
  "author": "<person name>",
  "project": "<project name>",
  "image": "cover.png",
  "files": ["files/<file1>", "files/<file2>"]
}
```

- `files` lists the relative paths inside `files/`. Empty `[]` for text-only assets.
- `image` (**optional**) — cover image shown on the card. Path, relative to the asset folder,
  of a real image present in that folder (e.g. `cover.png` in `repo-skill-assets/<slug>/`, or
  `files/cover.png`). Allowed extensions: png/jpg/jpeg/webp/gif/svg. When missing or when the
  file does not exist, repo-skill falls back to the generic per-type thumbnail. Do not invent
  the image: include it only when the user provides one.
- Do not add transport fields (drive_item_id, size, id): repo-skill assigns those at import
  time, not this skill.

### 6. Write `README.md`

A self-contained, concise mini guide, covering:

- **What it does** and which problem it solves.
- **How to use it** (prerequisites, command/invocation, input/output).
- **Included files** and the role of each one.
- **Adaptation notes**: what the consumer has to customize.
- **Security**: secrets removed, or configuration to be supplied as variables/env.

Whoever downloads it must understand the asset without reading the original project.

## Final checklist

- [ ] The user declared source, asset name, user name, project name, type.
- [ ] Folder `repo-skill-assets/<asset-slug>/` created in the current project.
- [ ] `skill.json`, `README.md`, `files/` present.
- [ ] Files in `files/` are generalized copies; originals untouched.
- [ ] If the source is a script: files needed at runtime (weights, configs, templates, etc.) included in `files/`, listed in `skill.json` and documented in the README.
- [ ] No `.env`, `.env.example`, secret, key, token, password or credential.
- [ ] `files` in `skill.json` matches the actual content of `files/`.
- [ ] No writes outside `repo-skill-assets/`, no publishing, no uploads.

When done, report the generated path and the content of `skill.json` back to the user.
