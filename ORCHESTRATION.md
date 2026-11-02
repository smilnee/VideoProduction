# Model-routed production orchestration

This is a native Copilot custom-agent workflow, not another controller service.
It uses the approved models and reasoning levels, dispatches only needed roles
and preserves the [production rules](AGENTS.md) and
[evidence-based skill](.github/skills/microstation-camtasia-video/SKILL.md).
No leases, READY/GO protocol, proxies or heartbeat process are required.

## Start

1. Open a workspace containing these agents, prompts and references. In VS Code,
   select the **Copilot harness** and reload discovery if needed. Use a client
   supporting custom-agent `model` and `reasoning-effort`.
2. Select **vp-orchestrator**, or run
   [/orchestrate-video](.github/prompts/orchestrate-video.prompt.md) with your
   task, key frames and named detail. The existing
   [/microstation-video](.github/prompts/microstation-video.prompt.md) also uses
   this coordinator for its 25-second camera-only sample.
3. First try: **"Plan only: a 25-second whole-monitor tour, one keyboard detail,
   then exterior context. Show specialist routes and acceptance checks.
   Do not operate applications or start recorders."**
4. For actual production, configure the separate approved MicroStation bridge
   and [Camtasia MCP connection](CAMTASIA-MCP.md), then request the film.
   Installing this framework does not authorize modelling or start production.

Copilot CLI can start the coordinator from the workspace:

```powershell
copilot --agent vp-orchestrator --model gpt-6.1-sol --reasoning-effort high
```

Keep normal tool/path permissions. Do not add blanket allow-all flags.
This workflow targets local Windows application sessions, not GitHub's cloud
agent, WSL or a remote container. See
[custom-agent fields](https://code.visualstudio.com/docs/agents/reference/custom-agent-file-reference)
and [subagents](https://code.visualstudio.com/docs/agents/run/subagents).

## Approved routing

The linked profiles are executable configuration. `xhigh` means **Extra high**.
No model fallback arrays or Auto routing are configured.

| Role | Agent | Model | Reasoning |
|---|---|---|---|
| Coordinator / production planning | [vp-orchestrator](.github/agents/vp-orchestrator.agent.md) | gpt-6.1-sol | high |
| MicroStation 3D modelling | [vp-modelling](.github/agents/vp-modelling.agent.md) | gpt-6-astra | xhigh |
| Camtasia editing | [vp-camtasia](.github/agents/vp-camtasia.agent.md) | gpt-6.1-sol | xhigh |
| Reference research | [vp-reference](.github/agents/vp-reference.agent.md) | gpt-6-astra | high |
| MicroStation cameras / rendering | [vp-camera](.github/agents/vp-camera.agent.md) | gpt-6-astra | xhigh |
| Screen recording / performance | [vp-capture](.github/agents/vp-capture.agent.md) | gpt-6.1-sol | medium |
| Media processing / encoding | [vp-media](.github/agents/vp-media.agent.md) | gpt-6.1-sol | high |
| Geometry / preservation QA | [vp-geometry-qa](.github/agents/vp-geometry-qa.agent.md) | gpt-6-astra | xhigh |
| Video / timeline QA | [vp-video-qa](.github/agents/vp-video-qa.agent.md) | gpt-6.1-sol | xhigh |
| MCP / framework engineering | [vp-integration](.github/agents/vp-integration.agent.md) | gpt-6.1-sol | high |
| Documentation / handoffs | [vp-documentation](.github/agents/vp-documentation.agent.md) | gpt-6.1-sol | medium |
| GitHub publication / access | [vp-publication](.github/agents/vp-publication.agent.md) | gpt-6.1-sol | medium |

Use xhigh for unresolved media synchronization/recovery, repeated failures or
consequential integration design decisions. Actual access-policy changes use
high, with separate authorization. The coordinator must request a supported
explicit per-invocation effort override; if the host cannot do that, stop for an
explicit profile/client configuration change. Do not rewrite defaults silently.

### Runtime compatibility is a gate

- Both models and the selected effort must be available to the signed-in user.
  Model availability, cost-tier restrictions and organization policies vary.
- Dispatch by exact custom-agent name. Where the host exposes explicit model/
  reasoning arguments, supply the matching approved values to avoid conflicting
  user-profile subagent defaults. Otherwise verify the effective profile.
- Do not silently inherit a different model/effort, use Auto or proceed after a
  rejected route. A worker repeating its model name is not runtime proof.
  Inspect host dispatch/session metadata or controls; report what is unverified.
- Native Copilot supports `reasoning-effort`. Other harnesses, converted plugin
  agents and older clients can ignore fields. Do not claim identical enforcement
  there. Tool availability and applicable permission prompts still need checking.
- Profiles deliberately omit the editor-only `target` field, which the tested
  CLI warns it ignores. Select the Copilot harness explicitly in VS Code;
  discovery of a file alone is not proof of compatible execution.
- MCP server IDs are host-specific. Profiles include the observed
  `bentley-mstn`, `bentley-microstation-2026`, `MicroStation MCP` and `camtasia`
  IDs. If yours differ, explicitly map the relevant profile tool names before
  production; never enable all unrelated tools to work around missing ones.
  Use one approved MicroStation connection throughout a job.

## Workflow and evidence gates

Run only the applicable stages, not all twelve agents every time:

1. **Contract and evidence:** coordinator establishes scope, output, destination
   and saved authority; reference specialist resolves substantial visual/API
   questions. A camera tour is not authorization to create geometry.
2. **Protect and test:** native/app specialists inspect current state and create
   required backups/snapshots. Capture plus camera specialists prove a short
   representative genuine take and estimate production time.
3. **Record:** capture starts and proves responsiveness before one modelling or
   camera specialist changes the scene. For new construction, preserve its real
   baseline and stage coverage. Record completed native poses/holds; reconcile
   timeouts before another write.
4. **Process:** after take closure/coverage checks, media specialist selects
   chronological completed footage and verifies exact outputs. Missing actual
   construction remains missing, never recreated from completed geometry.
5. **Edit:** Camtasia specialist preserves original clips/settings, edits only
   the authorized interval, then reopens, plays, saves and reads back the result.
6. **Independent acceptance:** fresh geometry/preservation and video QA jobs
   verify relevant requirements against immutable evidence and actual delivered
   pixels/playback. A builder's successful dispatch or self-review is insufficient.
7. **Close:** relevant app specialist restores presentation and stops owned
   helpers; QA verifies the final state. Deliver video/editable-project links
   and explicit PASS/unresolved results. Documentation/publication run only if
   requested or directly required by the authorized deliverable.

Editing-only work skips capture/modelling. Setup/documentation/publication-only
work must not invoke application operations. For unsupported native geometry,
remaining shimmer or missing source takes, retain UNRESOLVED; do not manufacture
acceptance. Perform bounded correction/retake under the responsible role and
verify again, rather than launching duplicate writers.

## Single-controller discipline

The coordinator must await each scene/editor action job before dispatching
another that touches the same live state. Treat the interactive desktop as
shared even across different applications: screenshots, playback, focus changes
and recorder hotkeys can disturb capture. Native readbacks also need a stable
scene. Workers cannot delegate further, and must not start independent app jobs.

A recorder may run as an observer while exactly one worker drives the scene.
Its start/stop/focus changes are sequential actions. Retain its exact
process/session handle and ownership until it is stopped/flushed and checked.
Only independent research or offline work on immutable inputs may run in
parallel, and not if rendering/capture resource contention would harm the take.

These are coordinator scheduling/tool-scope guardrails, **not an OS mutex or a
security sandbox**. Another user/session can still change the applications.
Check live state at handoffs; stop on conflicting concurrent changes rather than
overwriting them. No general shell or application tools are given to the
coordinator, and workers are not given the delegation tool.

## Specialist contract

Read this guide, [project rules](AGENTS.md) and the task-relevant skill/reference
before execution. Respect stricter project instructions and approved host
permissions. Stop if no bounded goal, scope or required application ownership
is supplied. Do not infer missing approval from a role's tool access.

The coordinator supplies a self-contained job envelope in the delegation message:

- Goal, exact current authorization, excluded work and named role.
- Requested model/effort and any explicitly justified escalation.
- Actual file/model/project, applicable authority and immutable before records.
- Allowed actions and desktop/app ownership; active recorder handle if relevant.
- Inputs/reference images, exact IDs/intervals and predecessor evidence.
- Required measurable checks, output artifacts and stop conditions.

Return a concise receipt, not a new planning-file bureaucracy:

- `status`: PASS, UNRESOLVED or BLOCKED for each requested requirement.
- Configured/requested model/effort and separately observed runtime evidence.
- Exact changed paths/IDs/intervals, or an explicit no-change result.
- Evidence paths and measured results, not just tool dispatch/counts.
- Saved/restored state, active helper handles and remaining ownership.
- Uncertainties/blockers and the next safe action.

Do not expose secrets or personal recent-file lists. Reconcile live state after
timeouts; never blindly replay edits, broadly Undo or silently rebaseline.
For QA, use a fresh bounded invocation independent of the builder's retained
context; share its evidence, not an instruction to rubber-stamp it.

## Editing and validation

Edit a role's `model` / `reasoning-effort` in its linked profile intentionally,
then update this routing table and the validator's approved-route expectations
in the same change. Do not change global Copilot preferences.
The [setup prompt](.github/prompts/setup-video-production.prompt.md) copies all
framework assets into another project while preserving existing instructions.

With Node.js available, no dependency installation is required:

```powershell
node .\scripts\validate-orchestration.cjs
node --test .\tests\orchestration.test.cjs
```

Static tests check authored routes, scopes and links; they do not prove model
entitlement, subagent dispatch, live MCP access or no-flicker. Use the plan-only
smoke request first, verify runtime metadata, and run a representative real take
only when production is separately requested.

### Recorded framework validation

On 2026-11-02, all 20 static regression tests passed. Copilot CLI 1.0.105
discovered all twelve profiles with no warnings/errors. A plan-only coordinator
run used `gpt-6.1-sol`. A separate synthetic dispatch test recorded actual
`vp-geometry-qa` execution on `gpt-6-astra` with configured `xhigh`, followed by
`vp-documentation` on `gpt-6.1-sol` with configured `medium`, using explicit
per-call overrides. Runtime configuration, selected-agent and model-call events
were checked, not the workers' verbal self-identification.

All MCP servers were disabled; the only tool calls were the two sequential
delegations and the workers made zero tool calls. Their production checks
correctly remained BLOCKED without live evidence. This verifies discovery and
representative routing, not all twelve roles against live applications or a new
film's acceptance. Repeat compatibility checks for another account/client.
