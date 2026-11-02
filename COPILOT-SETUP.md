# Set up GitHub Copilot for video production

This template supplies instructions, a skill, model-bound specialist agents,
an orchestrator, prompts and a custom local
Camtasia MCP server with connection examples. It does not automatically install
dependencies, register servers, install MicroStation/Camtasia or provide a
GitHub Copilot subscription.
Use VS Code with GitHub Copilot Chat in Agent mode and approved MCP integrations.

## Start with one prompt

No manual clone or slash-command knowledge is needed. Paste this into your
AI agent in the workspace you want to prepare:

> Download https://github.com/smilnee/VideoProduction and set up its
> MicroStation/Camtasia AI workflow in my current workspace. Read the
> repository's setup guide and follow its setup prompt. Preserve my existing
> files and instructions. Check the required applications, AI models and MCP
> connections; ask before installing software or changing live settings.
> Finish with a plan-only example. Do not edit a model, change a timeline or
> start recording.

Use an existing local copy if present; otherwise the agent can clone the public
HTTPS repository or download its ZIP without a GitHub account. If it cannot
retrieve files or prepare the workspace, it must report that prerequisite.
It must not claim model routing is active before the client discovers the agents.

## Get a public copy

The template is [smilnee/VideoProduction](https://github.com/smilnee/VideoProduction).
Reading, cloning or downloading this public repository requires no GitHub login.
GitHub Copilot itself still needs an authenticated account/subscription or
applicable entitlement, plus access to the configured models. Public source
availability does not remove application licences or organization MCP policies.
Do not paste tokens into chat or commit credentials.

If creating a new GitHub repository through **Use this template**, GitHub
authentication is required. Choose an approved destination/visibility separately;
this public template does not authorize publishing your models or recordings.

Optional manual download with Git:

```powershell
git clone https://github.com/smilnee/VideoProduction.git
Set-Location .\VideoProduction
code .
```

Without Git, use GitHub's **Code > Download ZIP**, then extract locally.
Publishing and write access remain separate tasks; see [access requirements](ACCESS.md).

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
5. Follow the [orchestration guide](ORCHESTRATION.md): select the Copilot harness
   and **vp-orchestrator**, verify model/effort support, then try
   `/orchestrate-video` with a plan-only request. No live application action is
   required for that test. Use Node.js for the optional static validation/tests.
6. Attach key-frame images, name the detail feature and use
   `/microstation-video` to request a film. Production then performs its own
   live-session checks; setup alone does not validate the connected applications.

## Paste this into Copilot in an existing project

Replace the checkout path before sending. This prompt installs workspace-scoped
customizations, not global user-profile settings.

> Set up this workspace's GitHub Copilot for MicroStation and Camtasia video
> production using the authorized VideoProduction checkout at
> `<LOCAL-TEMPLATE-CHECKOUT>`. Read and follow its
> `.github/prompts/setup-video-production.prompt.md`.
> Install the production skill with its reference files, all three reusable
> prompts, all twelve vp-* custom-agent profiles, ORCHESTRATION.md and its
> validation script/tests, plus the Camtasia MCP guide, server source/dependency manifest and
> inert connection examples. Include ACCESS.md while distinguishing the
> original template's access from my target repository's actual policy.
> Merge a short routing section into my existing agent instructions;
> preserve other project rules, my README and any conflicting customizations.
> Discover the MicroStation and Camtasia MCP tools without operating either
> application. If Camtasia MCP is missing, follow `CAMTASIA-MCP.md` to propose
> a connection using the bundled server and resolved local paths. Ask separately
> before dependency installation, configuration changes or server startup.
> Do not invent a hosted URL or overwrite other MCP servers.
> Validate frontmatter, relative links and workspace discovery locations.
> Adapt copied links to my actual instruction-file location; do not create
> competing instructions or overwrite my README to satisfy template links.
> Preserve the approved model/reasoning routes. Explain that missing model
> entitlement or unsupported effort controls block production, not justify Auto.
> Show how to use `/microstation-video` with my model, key frames and one
> detailed feature. Do not start recording, alter a model/timeline, modify
> global settings, publish files or request credentials in chat.

Use your own checkout path; no original author's machine path is required
by the production skill.
The generic setup prompt is a bootstrap operation before the new agents are
discoverable, not proof that model-routed dispatch already works. Once installed,
route supporting work through `/orchestrate-video` as well.

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
