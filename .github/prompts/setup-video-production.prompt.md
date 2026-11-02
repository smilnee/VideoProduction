---
description: "Set up this workspace's GitHub Copilot with the MicroStation/Camtasia video-production rules, skill and prompts without starting recording or changing applications."
agent: "agent"
---

Set up the current workspace for MicroStation and Camtasia video production
using an authorized local checkout of the VideoProduction template.
This is setup only: do not record, edit a model, move cameras, change a timeline,
install software, publish files or change repository access.

1. Establish the local template checkout and target workspace. Use the current
   folder if it is the template; otherwise ask for the checkout location if it
   is not supplied. Do not fetch a guessed GitHub repository or ask for tokens.
2. Read the template's [rules](../../AGENTS.md),
   [overview](../../README.md) and
   [production skill](../skills/microstation-camtasia-video/SKILL.md).
   Read the [Camtasia MCP connection guide](../../CAMTASIA-MCP.md) for the
   bundled server and verified configuration formats.
   Read the [orchestration guide](../../ORCHESTRATION.md) for approved routes
   and runtime compatibility. This generic prompt bootstraps the profiles;
   it does not prove they are already loaded or model-routed.
   Inspect the target workspace's existing Copilot/agent instructions before
   changing any customization. Preserve unrelated work and stricter rules.
3. If this workspace is already the template, validate the existing files rather
   than duplicating them. Otherwise install only:
   - `.github/skills/microstation-camtasia-video/`, including its references.
   - `.github/prompts/microstation-video.prompt.md`.
   - `.github/prompts/setup-video-production.prompt.md`.
   - `.github/prompts/orchestrate-video.prompt.md`.
   - `.github/agents/vp-*.agent.md` (all twelve profiles).
   - `ORCHESTRATION.md`.
   - `ACCESS.md` (retain the original-template disclaimer; adapt any target
     publication instructions to the actual authorized repository).
   - `scripts/validate-orchestration.cjs` and `tests/orchestration.test.cjs`.
   - `CAMTASIA-MCP.md`.
   - `integrations/camtasia/camtasia_mcp_server.py` and `requirements.txt`.
   - `examples/camtasia-mcp.vscode.json` and `camtasia-mcp.copilot.json`.
   Compare destination files first. Merge compatible customizations; ask before
   replacing conflicting instructions. Never copy models, recordings, projects,
   credentials or machine-specific MCP configuration.
   Carry forward ignore rules for virtual environments and live MCP settings
   into the target's existing `.gitignore` without replacing unrelated rules.
   Do not copy a virtual environment or turn the inert examples into active
   connections during this customization-only setup.
4. Integrate a short video-production section into the target's existing
   `AGENTS.md` or `.github/copilot-instructions.md`, following its conventions.
   If neither exists, create `AGENTS.md`. Do not add a competing always-on file
   or replace its README. Link to the installed skill using a correct relative
   path. Carry forward native-MCP-only model/view operations, camera-only scope
   unless separately authorized, genuine whole-monitor footage, model/timeline
   preservation and honest PASS/unresolved quality reporting.
   Link the orchestrator and carry forward exact model/effort routing,
   independent QA and single-controller application/desktop discipline.
   Adapt copied links to the target's actual instruction file, including when
   it uses `.github/copilot-instructions.md` rather than root `AGENTS.md`.
   Do not add a competing always-on file or replace the target README merely
   to satisfy a template link. Revalidate every copied local link afterward.
5. Discover whether MicroStation and Camtasia MCP tool definitions are available,
   without invoking tools that operate the live applications. Check approved
   user-supplied server configuration if needed without displaying secrets.
   If Camtasia MCP is missing, use the bundled guide/examples to propose the
   appropriate configuration, resolving paths from the actual checkout.
   Do not invent a hosted server URL or a MicroStation bridge configuration.
   Ask separately before installing dependencies, modifying live MCP settings,
   enabling or starting a server. Report missing prerequisites, not success.
   Tool discovery alone does not prove a running application/bridge is connected.
6. Validate skill name/folder matching, YAML frontmatter, descriptions, resource
   links, prompt placement and all twelve approved model/effort profiles.
   If Node.js is already available, run the supplied validator and tests.
   Do not install Node/packages just for this bootstrap without separate approval.
   Explain that workspace customizations are not
   automatically installed globally. Suggest reloading VS Code if discovery
   has not refreshed; report runtime discovery as unverified unless observed.
   Explain that the Copilot harness must honour model and reasoning-effort.
   Do not claim fallback/harness compatibility or app connections from static tests.
7. Show the installed files, any remaining prerequisites and how to invoke
   `/microstation-video` with key frames and a named detail feature. Link the
   Camtasia connection guide and its connection-only setup prompt.
   Also show `/orchestrate-video` with a plan-only example and the model table.

Do not silently enable MCP servers, grant tool permissions or modify the user's
global Copilot settings. Ask separately for any required personal installation.
