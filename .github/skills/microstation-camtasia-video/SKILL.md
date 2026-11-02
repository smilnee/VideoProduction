---
name: microstation-camtasia-video
description: "Use when producing MicroStation demonstration videos, full-screen recordings, smooth camera walk/fly tours, detail reveals, genuine modelling footage, or appending/revising an existing Camtasia timeline through MCP. Covers incomplete redraws, geometry popping/flicker checks, readable details, real agent-panel footage, preservation and verified delivery."
---

# MicroStation + Camtasia video production

Follow the active project's model authority and
[technical techniques](./references/production-techniques.md).
This skill supplies a workflow, not permission to build geometry or replay an
earlier project's controller. Documentation changes need no live application calls.
Use the [orchestrator](../../../ORCHESTRATION.md) for approved model/reasoning
routing, minimal specialist selection, single-controller live application work
and independent verification. Never turn its setup into a replay of past builds.
For missing Camtasia MCP tools, use the
[connection guide](../../../CAMTASIA-MCP.md) and bundled server/configuration
examples. Obtain approval before installing dependencies or changing/starting
connections; tool discovery alone does not prove a running editor.

## 1. Establish the film contract

- Identify audience/purpose, attached key frames, selected features, duration,
  output resolution/rate and append/replace/new-project destination.
- Default to a camera-only tour, whole intended monitor, silence and no added
  captions. Include the real agent panel when requested; never fabricate it.
- Resolve conflicts with monitor aspect ratio or existing Camtasia settings
  before changing either. Do not require approval of routine internal stages.
- For construction demonstrations, obtain a bounded edit scope and record the
  real baseline before edits. Completed-model footage is not construction evidence.

## 2. Protect and inspect

- Discover MicroStation/Camtasia MCP tools. Inspect selection, actual file/model,
  units, pending/writable state and the correct project's saved authority.
- Inspect reference images and complementary model views sufficient to choose a
  route. Snapshot affected presentation with a unique session name; preserve
  other views, clipping, selection and any concurrent work.
- Use Camtasia MCP to identify the open project, settings, media and exact target
  interval. Save and verify a separate pre-edit backup. Do not trust stale clip IDs.

## 3. Prove a representative take

- Prepare/verify a small native camera path. Derive viewport aspect and units
  from the live scene. Avoid degenerate camera bases and routes through geometry.
- Include close detail, a tight-to-wide departure and a geometry-heavy exterior
  or equivalent difficult scene. Confirm genuine whole-monitor capture and
  readable details in decoded target-resolution frames.
- Benchmark completed redraw/hold/capture throughput and recording overhead.
  Estimate full-run wall time before selecting a recording duration/batch size.
  Do not begin a long take with an unproven slow method.
- Separate interrupted redraw dropouts from thin-edge aliasing/depth artifacts.
  Correct, recapture and inspect failures; if blocked, report the specific limit.
  A clean still or successful update return does not prove stable movement.

## 4. Record the real journey

- Use native cameras with eased movement and purposeful brief stops. Honour the
  requested number of featured objects; do not dwell at redundant similar items.
  Interpolate orientation safely when leaving a very close target.
- Use one validated rendering mode throughout. For ordinary full redraws,
  disable interruption/deferred rendering as supported by the verified APIs,
  process native events and record completion/hold times.
- Start a responsive recorder before advancing the camera. Use bounded,
  timeout-safe batches with a lightweight progress cursor and durable results.
  Renew numbered source recordings before they expire.
- Reconcile retained progress after timeouts; never blindly replay poses or
  initializers. Persist complete native pose/clock records before restarting.

## 5. Select and edit

- When using completion timestamps, map them to actual decoded source PTS,
  including dropped/VFR frames. Select only genuine frames inside completed
  holds; inspect all overlapping sources before declaring a missing frame.
- Preserve chronological camera order when an overlapping source is needed.
  Use contiguous source groups, not one concatenation block per source file.
  Explicitly repair uncovered poses with camera-only retakes; never silently
  skip them or synthesize geometry/intermediate camera frames.
- Retime selected frames only after source indexing. Fully decode each segment
  and final film to check frame count/duration; prevent EOF duplication.
- Prefer Camtasia MCP project editing. Its add/update/delete project-file tools
  require the target project to be closed: save/backup, switch to an untitled
  project and verify UI state first. Keep `force` false; do not bypass the
  open-project guard. Use custom schema edits only for an unsupported operation
  after inspecting the actual format. Reopen through MCP afterwards.
- Specify the target track, source in-point, duration and whole-project append
  time explicitly; a tool's default append-to-track end may be the wrong place.
  Check copy/scale settings so the bundle is portable and the full frame is kept.

## 6. Verify, restore and deliver

- Inspect actual playback and full-size detail/adjacent frames, especially
  translucent/thin geometry, paving, dense details and transitions. Contact
  sheets and motion scores support inspection but cannot certify no-flicker.
- Measure required readable detail in delivered frames. For featured keyboard
  A-Z legends, check every letter at least 8 pixels high; use relevant measurable
  criteria for other project types. Preserve the full-screen delivery composition.
- Reopen, play and save in Camtasia. Validate original clips' timing, source
  in-points, transforms, crop, effects, metadata and animations after native save.
  Resolve media by content identity when Camtasia copies/normalizes their paths.
- Restore affected views and selected view/selection; verify protected clipping,
  the applicable native inventory and saved-state/file checks. Stop task-owned
  recording helpers; keep original footage, media and backups.
- Deliver video and editable-project links with requirement-by-requirement
  PASS/unresolved results. Distinguish camera tours, genuine construction,
  rendering acceptance and model/photo/clearance certification.
