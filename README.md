# alfred-workflow-netlify

Alfred Workflow to browse [Netlify](https://www.netlify.com) sites via the [Netlify API](https://docs.netlify.com/api/get-started/).

## Commands

### `nf <query>` - search your Netlify sites

Live-filters your sites by name/domain as you type.

- `Enter` on a site - drill into its builds, most recent first, with 🟢/🔴/🟡 status and the failure reason on errors.
- `Shift+Enter` on a site - drill into its environment variables.
- `Cmd+Enter` on a site - open its Netlify dashboard/settings page.
- `Alt+Enter` on a site - open the live site.
- `Ctrl+Enter` on a site - trigger a new deploy.
- `Enter` on a build - open its build/log page.
- `Cmd+Enter` on a build - open that build's deploy preview.
- `Ctrl+Enter` on an active build - cancel it.
- `Enter` on an env var - copy `KEY=value` to the clipboard.
- `Cmd+Enter` on an env var - copy just the value.

## Install

1. Download the latest `Netlify.alfredworkflow` from [Releases](https://github.com/aleksgorbenko/alfred-workflow-netlify/releases).
2. Double-click it - Alfred will prompt to import.
3. Requires [Alfred](https://www.alfredapp.com) with a Powerpack license.

## Setup

1. Open the workflow in Alfred, click the `[x]` (Configure Workflow) button.
2. Paste your Netlify Personal Access Token into the **Netlify Personal Access Token** field (User Settings > Applications > Personal access tokens > New access token).

## Development

- Python 3.14, stdlib only.
- `src/nfapi/` - runtime scripts Alfred calls.
- `tools/` - dev-only scripts (bundle verification), not shipped.

```sh
make check    # lint + format check + tests
make build    # package dist/Netlify.alfredworkflow
make verify   # audit the built bundle for local paths, tokens, junk files
make release VERSION=v1.0.0
make sync-plist WORKFLOW_DIR=/path/to/installed/workflow   # pull info.plist edits back
make link-live WORKFLOW_DIR=/path/to/installed/workflow    # symlink src/ for live dev
```

## My Other Workflows

- [Discogs for Alfred](https://github.com/aleksgorbenko/alfred-workflow-discogs)
- [WaniKani for Alfred](https://github.com/aleksgorbenko/alfred-workflow-wanikani)
- [2Do for Alfred](https://github.com/aleksgorbenko/alfred-workflow-2do)
- [BunPro for Alfred](https://github.com/aleksgorbenko/alfred-workflow-bunpro)
- [Bandcamp for Alfred](https://github.com/aleksgorbenko/alfred-workflow-bandcamp)
- [config](https://github.com/aleksgorbenko/config) — index of all my workflows, plus macOS/iOS setup
