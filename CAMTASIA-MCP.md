# Connect Camtasia MCP to GitHub Copilot

The Camtasia MCP connection is a **local Python process using stdio**, not a
hosted URL. This repository includes the custom Windows server used for the
recording workflow:

- [Server source](integrations/camtasia/camtasia_mcp_server.py)
- [Dependency manifest](integrations/camtasia/requirements.txt)
- [VS Code configuration example](examples/camtasia-mcp.vscode.json)
- [Copilot portable/CLI configuration example](examples/camtasia-mcp.copilot.json)

This is a custom integration, not an official TechSmith, Bentley or GitHub
server. It reads/writes Camtasia project JSON and uses Windows UI Automation
for the editor and recorder. It can access local files, send input and capture
screens. Review the source and your organization's policy before trusting it;
do not blanket-auto-approve tools. No Camtasia MCP URL, port, API key or OAuth
token is required by this server.

## 1. Prerequisites

- Windows with a licensed, locally installed Camtasia editor and recorder.
  The production workflow was exercised with Camtasia **2024.1.9**; other
  releases/project schemas are not certified by this template.
- A local Windows checkout of this repository, and VS Code with GitHub Copilot
  Agent mode or a compatible Copilot CLI installation.
- Python **3.12**, tested here with **3.12.9**, and permission to create a
  virtual environment and install the listed dependencies. Do not copy another
  user's virtual environment.
- An interactive Windows desktop for subsequent editor/recorder operations.
  Run the server on the same Windows machine/user desktop as Camtasia, not in
  WSL, a Linux container, a cloud agent or an unrelated remote host.

MicroStation and its approved MCP bridge are separate prerequisites; this
server does not install or replace them. FFmpeg/FFprobe are separate optional
capture/media-inspection tools, not the Camtasia MCP transport.

## 2. Install the server dependencies

These are instructions for an approved installation, not permission for an
agent to install packages or change your machine just because it reads this guide.
From the repository root in PowerShell, after approval:

```powershell
Set-Location .\integrations\camtasia
py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
Set-Location ..\..
```

If the Python launcher is unavailable, use your approved Python 3.12 executable
instead of `py -3.12`. Inspect/reuse an existing environment rather than
overwriting one blindly. The manifest contains dependency ranges, not a full
lockfile. The observed working environment used `mcp==1.30.0`,
`pywinauto==0.6.9`, `pywin32==312`, `pillow==13.0.0` and `psutil==7.2.2`.
Those observations are not a guarantee about every version the ranges permit.

Keep `.venv`, live MCP settings, credentials, footage and projects uncommitted.
The [ignore rules](.gitignore) cover these local files.

## 3. Register the connection

Choose **one** configuration route for the active client/harness. Check for an
existing `camtasia` entry first; do not overwrite other servers, create conflicting
duplicates or copy your entire user configuration into this repository.
Examples are inert until explicitly installed and trusted.

### VS Code

1. Run **MCP: Add Server** from the Command Palette, and choose
   **Command (stdio)** or the equivalent local-command option.
2. Name the server `camtasia`. Set the executable to your checkout's
   `integrations\camtasia\.venv\Scripts\python.exe`, and pass your checkout's
   `integrations\camtasia\camtasia_mcp_server.py` as its sole argument.
   Use fully resolved paths, preserving paths containing spaces as one argument.
3. Choose the configuration destination supported by your installed VS Code and
   selected harness. Prefer workspace scope when appropriate; changing a user
   profile is a separate decision.
4. Review the command, source, permissions and trust prompt before enabling it.

The [VS Code JSON example](examples/camtasia-mcp.vscode.json) uses the observed
working VS Code `servers`/`type: stdio` format. When this checkout is the workspace
root, its `${workspaceFolder}` paths resolve without personal paths. To use it
with that format, merge its `camtasia` entry into `.vscode\mcp.json`; do not
replace an existing configuration file.

Current VS Code also supports the portable `mcpServers` format, depending on
version/harness. Some guided setup versions label `.vscode\mcp.json` as a
compatibility destination. Do not mix the formats:

| Destination | Top-level key | Path handling |
|---|---|---|
| Workspace `.vscode\mcp.json` or VS Code profile `mcp.json` | `servers` | VS Code variables such as `${workspaceFolder}` |
| Workspace-root `.mcp.json`, where supported | `mcpServers` | Use resolved Windows paths in our example |
| Copilot user `mcp-config.json` | `mcpServers` | Use resolved Windows paths in our example |

For the portable route, merge the
[portable example](examples/camtasia-mcp.copilot.json) instead, replacing
**both** `C:\REPLACE_WITH_YOUR_CHECKOUT` placeholders with the actual checkout.
Do not paste `${workspaceFolder}` from the VS Code example into a different
client's configuration. See the
[current VS Code configuration reference](https://code.visualstudio.com/docs/agents/reference/mcp-configuration)
and [guided setup](https://code.visualstudio.com/docs/agent-customization/mcp-servers)
for installed-version details.

### GitHub Copilot CLI

In an interactive session, run `/mcp add`. Enter `camtasia`, select **Local**
or **STDIO**, and supply the same absolute Python executable and script argument.
Review the tools exposed before saving. Alternatively, merge the
[portable example](examples/camtasia-mcp.copilot.json) into the supported
configuration, replacing both path placeholders.

The observed user configuration is
`%USERPROFILE%\.copilot\mcp-config.json`; `COPILOT_HOME`, if configured, changes
that location. Current clients can also support workspace-root `.mcp.json`.
The example's `type: local` is the observed working CLI value; current clients
also offer the standard `stdio` name. Its `tools: ["*"]` exposes all server
tools, including writes and UI input; exposure is not approval to execute them.
Keep per-call confirmation enabled, or restrict the tool list for initial checks.
See [GitHub's CLI setup instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers).

## 4. Start and verify without editing

1. In VS Code, select the intended Chat harness. Open **Chat: Open
   Customizations > MCP Servers**, or **MCP: List Servers**, and find `camtasia`.
   Approve starting this reviewed local server. Use **Start Server** and inspect
   **Show Output**/server output if it fails. In CLI, use `/mcp`.
2. Discover its tool definitions. Expect `camtasia_status`,
   `camtasia_get_project`, `camtasia_get_ui_state`,
   `camtasia_launch_recorder`, `camtasia_add_media` and the other tools documented
   in the [production reference](.github/skills/microstation-camtasia-video/references/production-techniques.md#camtasia-mcp-workflow).
   Tool discovery proves the MCP process responds, not that Camtasia is open.
3. With approval for local read-only inspection, call `camtasia_status`.
   Inspect installation/process/project information locally; it can include
   personal file paths and recent projects. Do not publish that output.
   If Camtasia is not running, report that state instead of launching it silently.
4. If the editor is already open and UI inspection is approved, use
   `camtasia_get_ui_state` to confirm the intended editor/project. Read a known
   project with `camtasia_get_project` only when its path is confirmed.

Do not record, send keys, click, capture the desktop, launch/switch projects or
edit files to prove a connection. Do not call write tools as a setup test.
If you start the script manually in a terminal, it waits for MCP protocol input;
silence is not a successful handshake. Let the MCP client manage that process.

## 5. Production safeguards

Follow the [production skill](.github/skills/microstation-camtasia-video/SKILL.md).
Before project-file writes, save through Camtasia, verify an independent backup,
switch away from the target project and confirm it is closed. Keep `force` false;
never bypass the open-project protection. The server's one-step `.tscproj.bak`
does not replace a separate pre-edit backup. `.trec` import and export use the
supported editor UI route. Preserve existing clips/settings and verify playback
and native save afterward.

## Troubleshooting

| Symptom | Check |
|---|---|
| No Camtasia tools | Correct harness, enabled/trusted server, config destination/top-level key and server output; reload discovery after configuration changes |
| Executable/script not found | Both resolved paths, correct workspace root, JSON backslash escaping and virtual environment creation |
| `ModuleNotFoundError` | Install the manifest into the same virtual environment used by the server command, not another Python |
| Server responds but no editor | Installation and process state are separate; obtain approval before opening Camtasia |
| UI controls unavailable | Same interactive Windows desktop/user, no blocking dialogs, matching permissions and compatible Camtasia version; do not elevate blindly |
| Project edit refused | Save/backup and close the target project properly; do not set `force=True` |
| Organization blocks custom MCP | Obtain administrator approval; do not bypass allowlists or policy |

## Prompt to configure this connection

> Read `CAMTASIA-MCP.md` in my authorized VideoProduction checkout. Inspect the
> bundled server, requirements and configuration examples. Check my existing
> Camtasia MCP configuration without revealing secrets. Resolve the executable
> and script paths for this machine and propose the correct format for my
> VS Code/Copilot harness. Ask before installing dependencies, changing settings,
> enabling or starting the server; preserve other servers and avoid duplicates.
> After approval, verify MCP startup/tool discovery and separately request any
> read-only Camtasia status check. Do not record, move cameras, send input, launch
> or switch projects, capture the screen, or edit the model/timeline.
