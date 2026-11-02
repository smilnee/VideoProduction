# MicroStation + Camtasia video-production template

Reusable across architecture, infrastructure, engineering and other MicroStation
projects. Updated 2026-11-02 from the successful atrium recording and the later
full-screen reception tour/revision.

Private GitHub template:
[smilnee/VideoProduction](https://github.com/smilnee/VideoProduction).
Access is owner-only at initial publication; an `@bentley.com` login restriction
is **not** enforced on this personal repository. See [access requirements](ACCESS.md)
before granting or changing access.

## Start here

- [Project rules](AGENTS.md): safety, genuine footage and delivery standards.
- [Production skill](.github/skills/microstation-camtasia-video/SKILL.md):
  the repeatable capture, camera, editing and verification workflow.
- [Technical techniques](.github/skills/microstation-camtasia-video/references/production-techniques.md):
  native redraws, camera interpolation, timestamps, FFmpeg and Camtasia MCP.
- [Runnable sample prompt](.github/prompts/microstation-video.prompt.md):
  `/microstation-video`, or open it and use **Chat: Run Prompt**.
- [Copilot setup guide and paste-ready installation prompt](COPILOT-SETUP.md):
  use this to adopt the template in another project.
- [Camtasia MCP server and connection instructions](CAMTASIA-MCP.md):
  bundled Windows server, dependency setup, VS Code/Copilot configuration
  examples, trust, verification and troubleshooting.
- [Runnable setup prompt](.github/prompts/setup-video-production.prompt.md):
  `/setup-video-production` installs/validates workspace customizations only;
  it does not start recording or change the model/editor.
- [Private publication and Bentley access requirements](ACCESS.md):
  private visibility is not an email-domain login restriction.

Open this folder as a VS Code workspace with the MicroStation and Camtasia MCP
servers configured. Skills and prompts must be available in the active workspace;
placing this template beside another project does not globally install them.
For another project, follow the setup guide: copy the skill/references and
prompts, and merge routing rules into existing instructions rather than
overwriting them or replacing the project's README. Keep the skill and its
reference together. Reload the workspace if new customizations are not discovered.

This template includes guidance, customizations and the custom local
[Camtasia MCP server](integrations/camtasia/camtasia_mcp_server.py), not
MicroStation/Camtasia installers or a recorded-video bundle. Follow the
[connection guide](CAMTASIA-MCP.md) to install its dependencies and register it
after approval; cloning alone does not connect it. An approved MicroStation MCP
bridge is still a separate prerequisite.
FFmpeg/FFprobe are optional host-side capture/inspection tools when available.
Do not change applications or install dependencies merely to read these documents.
Keep models, footage,
Camtasia bundles, credentials and machine-specific MCP settings outside it;
the supplied ignore rules are a safeguard, not a substitute for reviewing uploads.

## Sample user prompt

> Using the currently open MicroStation model and my attached key-frame images,
> make a smooth 25-second camera tour showing this project's capabilities.
> Record the whole intended monitor, including the complete MicroStation UI and
> the real agent panel beside it. Focus briefly on one existing high-detail
> feature of my choice, include a readable close-up of its smallest important
> detail, then finish on the wider context image. Do not edit the model.
> Use MicroStation MCP for the cameras and Camtasia MCP to append the video
> after the currently open edit, preserving all existing clips and settings.
> Deliver 1920x1080 at 30fps, silent, with no added captions or titles.
> Test a short take first; prevent incomplete redraws and geometry popping.
> Check actual moving footage and delivered detail readability. If fine-edge
> shimmer remains, say so rather than claiming the video is flicker-free.
> Save and play the Camtasia project, restore the original MicroStation views,
> verify model preservation, and provide the video and editable-project links.

Attach the images and name the feature, for example a connection, machine,
road junction, facade joint or workstation keyboard. If the monitor aspect
ratio or existing project settings conflict with the requested output, resolve
that before recording or changing the project.

## What the evidence establishes

The atrium run delivered a 15-second ascent/reveal with verified preservation.
The later tour delivered 25 seconds, 750 actual completed camera poses and a
preserved existing Camtasia edit. Its keyboard legends measured 9-10 pixels in
decoded 1080p delivery frames. Full redraws removed large paving dropouts in
the inspected sequence, but fine screen-artwork edge aliasing remained.
Neither motion counts nor those successful checks certify universal no-flicker.

These are examples, not fixed model names, coordinates, units, clip IDs,
durations or gates for future projects. Do not replay their completed scripts.
