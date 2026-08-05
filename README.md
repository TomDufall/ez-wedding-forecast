# ez-wedding-forecast
Pulling Met Office data for an event forecast

## GitHub Pages Static Hosting Setup

This repository is set up to publish from the `docs` folder on branch `main`.

### Current structure

```text
/
|-- docs/
|   |-- index.html  # Root page at /
|   |-- json        # JSON document at /json
|   |-- .nojekyll   # Ensures extensionless files are served as-is
|-- scripts/
|   |-- preview.ps1 # Local static preview helper
|-- README.md
```

### What is implemented

- `docs/index.html` loads `GET /json` and displays `siteMessage` from that JSON.
- `docs/json` currently contains one sample config value:

```json
{
  "siteMessage": "Hello from GitHub Pages JSON"
}
```

## Configure Repo Settings (GitHub)

1. Push these files to the `main` branch.
2. Open your repository on GitHub.
3. Go to `Settings` -> `Pages`.
4. Under `Build and deployment`:
	 - `Source`: `Deploy from a branch`
	 - `Branch`: `main`
	 - `Folder`: `/docs`
5. Click `Save`.

After deployment completes, the URLs will be:

- Root page: `https://<owner>.github.io/ez-wedding-forecast/`
- JSON endpoint: `https://<owner>.github.io/ez-wedding-forecast/json`

If JSON changes are cached during testing, do a hard refresh in the browser.

## Local Preview

From repository root, choose the command that matches your terminal.
Both preview scripts now auto-open the root page in your default browser.

PowerShell:

```powershell
./scripts/preview.ps1
```

PowerShell with custom port:

```powershell
./scripts/preview.ps1 -Port 5500
```

PowerShell without opening browser:

```powershell
./scripts/preview.ps1 -NoOpen
```

Bash (Git Bash/WSL/macOS/Linux):

```bash
./scripts/preview.sh
```

Bash with custom port:

```bash
./scripts/preview.sh 5500
```

Bash without opening browser:

```bash
./scripts/preview.sh --no-open
```

Then open:

- `http://localhost:8080/` (default)
- `http://localhost:5500/` (if using `-Port 5500`)
