# Production techniques and verified limits

Observed with MicroStation MSPy/MCP, Camtasia 2024.1.9 and FFmpeg 9.0.1.
Prepare APIs and inspect installed tools/schema for each new environment.
Examples below are not universal settings or runnable production initializers.

## Native camera movement

- Follow MCP preparation, corrections, identical-source validation and fresh
  request execution. In fresh native Python sessions, load `MSPyECObjects`
  before `MSPyMstnPlatform` where the verified import context requires it;
  a warmed session can conceal missing base-type registration.
- Keep native Python inside its supported sandbox. Host-side capture, filesystem
  operations and FFmpeg subprocesses belong outside MicroStation; do not import
  removed filesystem/process/network modules or install native dependencies.
- Construct a stable eye/target forward-right-up basis and eight perspective
  frustum corners. Use `SetupFromFrustum`, `SynchWithViewInfo` and explicit
  selected-viewport control through prepared/verified native Python.
- Derive UOR scale and viewport aspect ratio; do not assume 10,000 UOR/m,
  16:9, a particular model ID, or another project's camera coordinates.
- Quintic easing, `u*u*u*(10 + u*(-15 + 6*u))`, provides smooth starts/stops.
  Inspect travel as well as endpoints: easing cannot fix a route through a face.
- World-space target interpolation can turn abruptly when departing a very close
  detail. The keyboard departure improved with shortest-path yaw and pitch
  interpolation and a separately interpolated target distance. Use that only
  where justified, with a stable up vector and direct moving-footage inspection.
- Apply the display style before the explicit camera. Capture current framing
  without a capture-tool style override; fitting/overrides can change the view
  or produce blank captures. Confirm full-image dimensions and actual pixels.
- Prefer Illustration Sky Sphere/Illustration for geometry review where defined;
  use Smooth as a complementary finish test. Production should use one tested
  appearance. Do not infer live style from capture metadata alone.

## Complete redraws and separate artifact classes

The earlier tour lost large paving patches during movement. Representative
ordinary full redraws with stop events cleared retained them. The revision used:

```python
stops = StopEvents(False, False, False, False, False, False)
stops.Clear()
update = IndexedViewSet.FullUpdateInfo()
update.SetIncremental(False)
update.SetStopEvents(stops)
update.SetDeferShadows(False)
```

Use prepared imports and verified `UpdateView` arguments for the installed
version, followed by `PyCadInputQueue.PythonMainLoop()`. Check the actual update
return semantics: the observed ordinary update returned `False`/zero, not a
truthy success value. The zero-argument `StopEvents()` constructor failed.

Dynamic redraws were tested but changed lighting/shading on the screen and
keyboard. They were rejected, not accepted as an interchangeable faster path.
Benchmark a consistent alternative before a new run; do not mix it into a take.

Classify remaining artifacts:

| Observation | Investigation | Acceptance |
|---|---|---|
| Large patches vanish during motion | Interruptions, incremental/deferred drawing, complete presentation | Inspect moving/adjacent delivered frames |
| Thin edges/text shimmer or show dashes | Style edges, aliasing, near/back clipping, thin overlapping layers | Report separately; redraw completion is insufficient |
| A face fills the image while travelling | Actual occlusion, near-plane intersection, route through geometry | Inspect/change the camera route, not preserved geometry |

Enabling bounded camera depth clipping was tested with near/far 0.20/250m instead
of 0.04/1000m. The following mutation persisted, whereas changing a detached
`GetViewFlags()` copy did not:

```python
info = viewport.GetViewInfo()
info.ViewFlags.noFrontClip = 0
info.ViewFlags.noBackClip = 0
viewport.SynchWithViewInfo(False, False)
```

Choose distances for the new subject, read them back and restore original flags
afterwards. Do not change a protected clip volume or another viewport.
Tighter clipping did not conclusively eliminate screen-artwork artifacts.
The final revision still showed fine Illustration edge aliasing/dashed outlines;
do not claim these tests established a completely flicker-free render.

## Timestamp-aware genuine capture

- Record the selected physical monitor, not the whole virtual desktop.
  Multi-monitor offsets can be negative. Verify composition, dimensions and
  visible private/unrelated content before capture.
- Camtasia Recorder MCP and host-side FFmpeg capture are distinct methods.
  Start/status/hotkey success is not a saved take: inspect the actual file,
  decoded changing frames and chronology. Never misattribute an FFmpeg take.
- The native UTC call returned `(status, milliseconds)`:
  `BeDateTime.GetCurrentTimeUtc().ToUnixMilliseconds()`. Check zero status.
  Log each pose index, intended tour time, camera, rendering result, completion
  timestamp and held-through timestamp.
- 180ms minimum holds, 15fps capture and four encoder threads reduced recording
  contention in this run. They are measured starting points, not guarantees:
  one hold had no eligible sample in the newest source.
- Map native completion to actual decoded recording timestamps, not nominal
  `frame / fps`. The tested interior window was completion+20ms through
  hold-end-10ms. Calibrate clocks/capture delay for another recorder; prove that
  the chosen pixels really show the completed view.
- Check every overlapping source. Frame434 was recovered from part3 while part4
  had no eligible sample. Preserve ascending capture time and tour-pose order;
  source parts may legitimately alternate. Concatenate contiguous groups.
- If no source covers a hold, fail explicitly and record a controlled camera-only
  retake. Do not silently select an incomplete frame, skip a pose or fill a gap
  with optical flow. Do not reconstruct missing construction footage.
- Approximately 40-second native batches avoided a 60-second bridge limit in
  this environment. Keep batches bounded, return/persist progress and resume
  from read-back state with fresh request IDs. Renew recordings before expiry.
- PowerShell `Tee-Object` logs here were UTF-16 with BOM; UTF-8 decoding failed.
  Inspect and decode actual encodings. A PowerShell native-stderr wrapper can
  report an error although the media completed: inspect FFmpeg diagnostics and
  probe/decode the file, never assume success or blindly re-record.
- Explicitly stopped MKVs can lack final trailers. Remux verified completed
  portions into edit inputs; report truncation and prove selected-frame coverage.
  Keep the original sources. Flush/present enough footage after the last hold
  before stopping a task-owned recording process.
  Stop only the task's known recording session/process IDs, never all processes
  sharing an application name.

## Exact retiming and decode checks

For timestamp-mapped recordings, index the original decoded timestamps before
frame-rate normalization. Saved indices from an older normalized-source recipe
apply only to that exact normalized source, not a newly normalized VFR file.

The successful FFmpeg 9 selection used a balanced selection expression and
`-filter_threads 1`. Its filter-file option is `-/filter:v PATH`; the older
`-filter_script:v` option was unavailable in this installation.

After selecting actual frames, the exact-output recipe used:

```text
select='<verified selection expression>',settb=1/30,setpts=N
-fps_mode cfr -r 30 -frames:v <selected frame count>
```

This limits each segment to its selected count. Without the limit, CFR conversion
of 15fps inputs appended duplicate EOF frames: 755 rather than the required 750.
FFmpeg 9 rejected `-fps_mode passthrough` together with `-r 30`; do not repeat it.
Validate segment and concatenated counts, durations and boundary frame order.
25 seconds at 30fps requires 750 output frames; this does not by itself prove
750 different native poses or absence of artifacts.

Use a full decode, not container metadata alone. Check width/height, frame rate,
duration, actual decoded frame count, unexpected audio and full-screen framing.
Motion/stillness scores and grayscale grouping are not flicker certification.
Inspect real motion plus full-size feature frames, including all required text.

## Camtasia MCP workflow

Discover tool definitions before use. The available MCP surface included:

| Tools | Purpose |
|---|---|
| `camtasia_status`, `camtasia_get_ui_state` | Identify editor/project, dialogs, playback state and timing |
| `camtasia_get_project` | Inspect canvas/rate, media resolution, tracks, clip IDs and timings |
| `camtasia_launch_recorder`, `camtasia_recorder_hotkey` | Operate Camtasia Recorder when chosen; still verify the file |
| `camtasia_add_media`, `camtasia_update_clip`, `camtasia_delete_clip` | Scoped project-file changes; close the target project first and keep `force` false |
| `camtasia_list_shortcuts`, `camtasia_run_shortcut` | Actual configured Save, NewProject, PlayPause and timeline navigation |
| `camtasia_launch`, `camtasia_screenshot` | Reopen the project and inspect genuine editor playback/composition |

1. Save through MCP, verify a separate project backup and preserve source media.
2. Prefer supported MCP project editing. The add-media tool refuses an open
   target unless forced; do not bypass that protection. Save/backup, use the
   configured `NewProject` shortcut and confirm untitled UI state before any
   project-file write, including MCP add/update/delete and custom schema edits.
   Keep `force` false. Custom JSON edits are only for unsupported operations.
   `.trec` files must be imported through the supported Camtasia UI route, not
   `camtasia_add_media`.
3. Inspect the actual schema and edit rate. Observed format8.0 stores clips under
   `timeline.sceneTrack.scenes[].csml.tracks[].medias` and sources in `sourceBin`,
   not `timeline.tracks`. Do not assume that schema for other versions.
4. Specify append start at the actual whole-project end, target track, duration,
   source in-point and scale/copy choices. `camtasia_add_media` defaults to the
   chosen track's end, not necessarily the complete edit's end; default
   `shrink_to_fit` does not upscale smaller footage. Preserve the whole frame
   and resolve aspect-ratio conflicts instead of cropping silently.
   `copy_into_project` defaults true and helps keep bundle/media portable.
   Replace only the authorized interval. Preserve original timing, in-points,
   transforms, crop, effects, metadata and animations; normalize only proven
   internal ID/source-reference renumbering during comparison.
5. Reopen through MCP, inspect and play the inserted interval, then save natively.
   A black canvas exactly beyond the last frame is not proof of a black film;
   inspect inside the interval and the last actual decoded frame.
6. Revalidate after save. Camtasia copied the revised media to its bundle root
   and reduced its stored path to a basename. Verify resolved content/hash,
   not equality with the pre-save relative path. Refresh clip/source IDs.
7. Verify actual project end and source availability. Do not silently change
   existing project settings to accommodate a new clip. Keep bundle/media
   together and deliver both video and editable-project links.

## Preservation and reporting

Restore session view snapshots, selected viewport/selection and protected clip
settings. Do not overwrite newer concurrent presentation with an old snapshot.
Compare native inventory with applicable saved authority and before records;
check DGN bytes/hash and pending state where appropriate. Pending=false alone
does not prove that nothing changed. Never use `DisplayHandler.Drop` for inspection.

Report exactly what was inspected, recorded, edited, saved and verified.
Keep no-flicker, readable-detail, model preservation, photographic equivalence,
fabrication/clearance and construction-history claims separate.
Historical controllers, clip IDs and native builders are evidence, not templates
to execute. Keep workflow state lightweight; no producer leases or watcher ritual.
