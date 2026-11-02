# User guide: start, customise and contribute

## Start with one prompt

Open the workspace you want to prepare and paste this into your AI coding agent:

> Using https://github.com/smilnee/VideoProduction, set up its
> MicroStation/Camtasia workflow in my workspace. Follow its setup guide and
> check the required applications, AI models and MCP connections. When complete,
> give me simple user instructions and a sample prompt.

The agent can obtain the public repository and prepare the workspace for you.
You do not need to clone it manually, know slash commands or fork it to try it.
Downloading requires no GitHub login. Running the workflow still requires
Windows, MicroStation, Camtasia and a compatible authenticated Copilot client
with access to the configured models.

The agent must preserve existing files/instructions and ask before software
installation, conflicting replacements or live MCP configuration/startup.
Setup is not permission to change model geometry, alter a timeline or record
your screen. Some actions, such as signing in, approving tools or reloading
agent discovery, may still need you.

## What the agent should give you

At the end of setup, expect:

- A short **Ready / Missing / Not verified** summary for applications, models,
  reasoning levels, MCP connections and agent discovery.
- The files installed or merged and where they live.
- Only the remaining actions you personally need to take, with clear reasons.
- Simple instructions for selecting the coordinator, attaching reference images
  and identifying the feature/monitor and Camtasia destination.
- A ready-to-paste plan-only prompt and a separate production prompt.
- Links to this guide and the relevant connection/troubleshooting instructions.

Missing model access or an unverified connection must not be reported as ready.
Static tests do not prove a running application is connected. The agent should
explain a blocker rather than silently choose a different model.

For detailed setup, see [Copilot setup](COPILOT-SETUP.md),
[Camtasia MCP](CAMTASIA-MCP.md) and [model routing](ORCHESTRATION.md).

## Try your first film

Use a copy of your model for initial testing. Attach useful reference/key-frame
images and identify the existing detail you want to feature. Start with a plan:

> Plan only: a smooth 25-second whole-monitor tour of my MicroStation model,
> featuring the existing detail I identify and finishing on a wider view.
> Preserve geometry and the current Camtasia edit. Show the proposed specialist
> routes, remaining prerequisites and acceptance checks. Do not start recording.

Once setup and the plan are agreed, a production request could be:

> Use the agreed plan to record the whole intended monitor, including
> MicroStation and the real agent panel. Feature my chosen detail, then finish
> wide. Append the silent 25-second tour to my current Camtasia edit, preserving
> all existing clips/settings and model geometry. Deliver 1920x1080 at 30fps.
> Test a short take first, inspect real movement and readable details, save/play
> the project, restore the original views and report any unresolved artifacts.

Only ask for modelling when you actually want geometry changes, with an exact
scope. A camera tour does not authorize rebuilding or replaying completed work.
The [production skill](.github/skills/microstation-camtasia-video/SKILL.md)
describes the preservation and quality checks.

## Do I need a fork?

| What you want to do | Best starting point | GitHub account needed? |
|---|---|---|
| Try the toolkit locally | Let your agent download/clone it | No, for the download |
| Use it in an existing project | Let the agent merge its workspace customizations | No, for copying public files |
| Create a separate GitHub project from it | GitHub's **Use this template** option | Yes |
| Propose improvements to the original toolkit | Fork, branch and pull request | Yes |

These are source-access requirements, not Copilot subscription requirements.
An independent template copy is not a fork and does not retain the same shared
Git history; a fork is the straightforward route for contributing back.

Forks of this public repository are public. Keep models, recordings, Camtasia
projects, personal paths, credentials, live MCP settings and company-confidential
information out of them. Use a separate approved private workspace/repository
for project data. See [visibility and access](ACCESS.md).

## Optional: contribute an improvement

Your AI agent can perform the Git steps; you still need an appropriate signed-in
GitHub account and approval before publishing anything.

1. **Fork:** open [smilnee/VideoProduction](https://github.com/smilnee/VideoProduction),
   choose **Fork** and create your copy under an approved account.
2. **Work separately:** clone your fork into a contribution checkout, not over
   an existing production workspace. Keep the original repository as `upstream`
   and your fork as `origin`; inspect existing remotes before changing them.
3. **Branch:** create a focused topic branch, for example
   `docs/setup-improvements`. Do not work directly on upstream `main`.
4. **Change and test:** make one clear improvement. Preserve model/effort defaults
   unless changing them is intentional; update their table and validator
   expectations together. With Node.js available, run:

   ```powershell
   node .\scripts\validate-orchestration.cjs
   node --test .\tests\orchestration.test.cjs
   git diff --check
   ```

5. **Review and push:** inspect the exact files and changes for secrets, personal
   paths and project data. Commit only the approved changes and push the topic
   branch to your fork, not the original repository. AI-assisted commits should
   follow the repository's co-author instructions.
6. **Open a pull request:** on GitHub choose **Contribute > Open pull request**
   from the fork, or **compare across forks** in the original repository.
   The destination/base is **smilnee/VideoProduction**, branch **main**; the
   source/compare is **your fork and topic branch**.
7. **Explain:** describe what changed, why, tests performed and limitations.
   Include screenshots/log excerpts only if approved and free of private data.
   The maintainer reviews the request and decides whether to merge it; submitting
   a pull request does not change the main repository.

An agent prompt for that process:

> Help me propose this improvement to https://github.com/smilnee/VideoProduction:
> [describe the change]. Inspect my GitHub identity and existing remotes without
> revealing credentials. Use my fork and a new topic branch, preserve unrelated
> work and run the relevant checks. Show me the exact changes for approval before
> pushing or opening a pull request to smilnee/VideoProduction main. Do not upload
> project data or change repository access.

To pick up later upstream changes, use **Sync fork** on your fork's `main`
branch, or ask your agent to fetch and merge upstream safely. Resolve conflicts
without discarding local work; do not force-reset a contribution branch.

No GitHub account or no wish to contribute code: send feedback privately to
the person who shared the toolkit, without attaching sensitive project data.
GitHub issues and pull requests themselves require sign-in.

For GitHub's detailed explanation, see
[contributing through forks and pull requests](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project).
