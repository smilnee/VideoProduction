# Set up GitHub Copilot for video production

This template supplies instructions, a skill, prompts and a custom local
Camtasia MCP server with connection examples. It does not automatically install
dependencies, register servers, install MicroStation/Camtasia or provide a
GitHub Copilot subscription.
Use VS Code with GitHub Copilot Chat in Agent mode and approved MCP integrations.

## Get an authorized copy

The template is [smilnee/VideoProduction](https://github.com/smilnee/VideoProduction).
Request access from its owner; corporate email alone does not grant access.
If the repository is later transferred, use the administrator-confirmed URL.
Sign in locally with an authorized GitHub identity; do not paste a token into
Copilot chat or commit credentials. If corporate SSO is required, authorize
the Git/CLI credential through that organization's approved process.

Clone the approved repository or use its **Use this template** option if the
owner has enabled that GitHub setting. Repository copies do not automatically
inherit the original repository's access restrictions: choose a private,
approved destination and verify its access policy separately.

For an authorized account:

```powershell
gh auth login --hostname github.com
gh repo clone smilnee/VideoProduction
Set-Location .\VideoProduction
code .
```

Publishing and granting access are separate tasks; see [access requirements](ACCESS.md).

## Use in this template workspace

1. Open the authorized checkout in VS Code.
2. Use `/setup-video-production`, or open
   [the setup prompt](.github/prompts/setup-video-production.prompt.md) and choose
   **Chat: Run Prompt**. Allow only the setup/file operations you intend.
3. Follow the [Camtasia MCP connection guide](CAMTASIA-MCP.md) for the bundled
   server, dependency installation, VS Code/Copilot examples and verification.
   Approve installation/configuration separately; setup does not do it silently.
   Obtain MicroStation MCP setup from its approved provider. Keep secrets and
   live machine settings outside the repository.
4. Reload the workspace if new customizations are not listed.
5. Attach key-frame images, name the detail feature and use
   `/microstation-video` to request a film. Production then performs its own
   live-session checks; setup alone does not validate the connected applications.

## Paste this into Copilot in an existing project

Replace the checkout path before sending. This prompt installs workspace-scoped
customizations, not global user-profile settings.

> Set up this workspace's GitHub Copilot for MicroStation and Camtasia video
> production using the authorized VideoProduction checkout at
> `<LOCAL-TEMPLATE-CHECKOUT>`. Read and follow its
> `.github/prompts/setup-video-production.prompt.md`.
> Install the production skill with its reference files and both reusable
> prompts, plus the Camtasia MCP guide, server source/dependency manifest and
> inert connection examples. Merge a short routing section into my existing agent instructions;
> preserve other project rules, my README and any conflicting customizations.
> Discover the MicroStation and Camtasia MCP tools without operating either
> application. If Camtasia MCP is missing, follow `CAMTASIA-MCP.md` to propose
> a connection using the bundled server and resolved local paths. Ask separately
> before dependency installation, configuration changes or server startup.
> Do not invent a hosted URL or overwrite other MCP servers.
> Validate frontmatter, relative links and workspace discovery locations.
> Show how to use `/microstation-video` with my model, key frames and one
> detailed feature. Do not start recording, alter a model/timeline, modify
> global settings, publish files or request credentials in chat.

Use your own checkout path; no original author's machine path is required
by the production skill.

For a connection-only setup prompt and exact launch configuration, see
[Camtasia MCP setup](CAMTASIA-MCP.md#prompt-to-configure-this-connection).

## First production request

> Make a smooth, silent 25-second whole-monitor tour of my open MicroStation
> model using the attached key frames. Feature one detail I name and finish
> with the wider context. Use the production skill and MicroStation/Camtasia MCP.
> Do not change geometry. Append after my current Camtasia edit, preserving
> existing clips and settings. Test a short take first, inspect real movement
> and readable details, report remaining shimmer honestly, save/play the result
> and restore the original views. Provide video and editable-project links.
