"""Camtasia MCP server (Windows, Camtasia 2024).

Two layers:
  * Project tools  - read/edit .tscproj project files (JSON) directly.
  * App tools      - drive the running Camtasia editor through Windows UI Automation
                     (menus, buttons, user keyboard shortcuts, screenshots, recorder hotkeys).

Camtasia has no public automation API on Windows, so exporting/rendering is done by
driving the UI (e.g. camtasia_run_shortcut("ExportLocal") or camtasia_menu(["Export", ...])).
"""

from __future__ import annotations

import io
import json
import os
import shutil
import struct
import subprocess
import time
import winreg
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP, Image

mcp = FastMCP("camtasia")

V8_EDIT_RATE = 705_600_000
SOURCE_EDIT_RATE = 10_000_000  # 100ns units, matches Windows media duration units
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".wma", ".aac", ".flac", ".ogg"}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".avi", ".wmv", ".mkv", ".webm", ".mpg", ".mpeg"}
STUDIO_PROCESS = "CamtasiaStudio.exe"
RECORDER_PROCESS = "CamtasiaRecorder.exe"


# --------------------------------------------------------------------------- install / registry


def _install_dir() -> Optional[Path]:
    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for hive, key in roots:
        try:
            with winreg.OpenKey(hive, key) as k:
                for i in range(winreg.QueryInfoKey(k)[0]):
                    try:
                        with winreg.OpenKey(k, winreg.EnumKey(k, i)) as sub:
                            name = winreg.QueryValueEx(sub, "DisplayName")[0]
                            if name.startswith("Camtasia"):
                                loc = winreg.QueryValueEx(sub, "InstallLocation")[0]
                                if loc and (Path(loc) / STUDIO_PROCESS).exists():
                                    return Path(loc)
                    except OSError:
                        continue
        except OSError:
            continue
    for p in sorted(Path(r"C:\Program Files\TechSmith").glob("Camtasia*"), reverse=True):
        if (p / STUDIO_PROCESS).exists():
            return p
    return None


def _install_info() -> dict:
    d = _install_dir()
    info: dict[str, Any] = {"installed": d is not None, "install_dir": str(d) if d else None}
    if d:
        try:
            import win32api

            fi = win32api.GetFileVersionInfo(str(d / STUDIO_PROCESS), "\\")
            ms, ls = fi["FileVersionMS"], fi["FileVersionLS"]
            info["version"] = f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
        except Exception:
            pass
    return info


def _settings_key_values() -> dict:
    """Values from HKCU\\Software\\TechSmith\\Camtasia Studio\\<ver>\\Camtasia Studio\\<ver>."""
    out: dict = {}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\TechSmith\Camtasia Studio") as base:
            versions = [winreg.EnumKey(base, i) for i in range(winreg.QueryInfoKey(base)[0])]
        for ver in sorted(versions, key=lambda v: [int(x) if x.isdigit() else 0 for x in v.split(".")], reverse=True):
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"Software\TechSmith\Camtasia Studio\{ver}\Camtasia Studio\{ver}") as k:
                    for i in range(winreg.QueryInfoKey(k)[1]):
                        n, v, _ = winreg.EnumValue(k, i)
                        out[n] = v
                out["_version_key"] = ver
                return out
            except OSError:
                continue
    except OSError:
        pass
    return out


def _mru(name: str) -> list[str]:
    raw = _settings_key_values().get(name) or ""
    return [p for p in str(raw).split("*") if p]


def _shortcuts_file() -> Optional[Path]:
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "TechSmith" / "Camtasia Studio"
    cands = sorted(base.glob("*/KeyboardShortcuts.json"), reverse=True)
    return cands[0] if cands else None


# --------------------------------------------------------------------------- processes


def _processes() -> list[dict]:
    import psutil

    out = []
    for p in psutil.process_iter(["pid", "name", "exe"]):
        n = p.info.get("name") or ""
        if n.lower() in (STUDIO_PROCESS.lower(), RECORDER_PROCESS.lower()):
            out.append({"pid": p.info["pid"], "name": n, "path": p.info.get("exe")})
    return out


def _studio_pid() -> Optional[int]:
    for p in _processes():
        if p["name"].lower() == STUDIO_PROCESS.lower():
            return p["pid"]
    return None


# --------------------------------------------------------------------------- UI Automation helpers


def _uia():
    from pywinauto.uia_defines import IUIA

    return IUIA()


def _pid_hwnds(pid: int) -> list[tuple[int, str]]:
    import win32gui
    import win32process

    found: list[tuple[int, str]] = []

    def cb(h, _):
        if (win32gui.IsWindowVisible(h) or win32gui.IsIconic(h)) and win32process.GetWindowThreadProcessId(h)[1] == pid:
            found.append((h, win32gui.GetWindowText(h)))
        return True

    win32gui.EnumWindows(cb, None)
    return found


def _wrap_hwnd(hwnd: int):
    from pywinauto.controls.uiawrapper import UIAWrapper
    from pywinauto.uia_element_info import UIAElementInfo

    return UIAWrapper(UIAElementInfo(hwnd))


def _main_window(required: bool = True):
    pid = _studio_pid()
    if pid is None:
        if required:
            raise RuntimeError("Camtasia editor is not running. Use camtasia_launch first.")
        return None
    hwnds = _pid_hwnds(pid)
    main = next((h for h, t in hwnds if t.startswith("TechSmith Camtasia")), None) or (hwnds[0][0] if hwnds else None)
    if main is None:
        if required:
            raise RuntimeError("Camtasia is running but its main window was not found (still starting?).")
        return None
    return _wrap_hwnd(main)


def _top_windows():
    pid = _studio_pid()
    return [_wrap_hwnd(h) for h, _ in _pid_hwnds(pid)] if pid else []


def _wrap(element):
    from pywinauto.controls.uiawrapper import UIAWrapper
    from pywinauto.uia_element_info import UIAElementInfo

    return UIAWrapper(UIAElementInfo(element))


def _condition(automation_id: Optional[str] = None, name: Optional[str] = None, control_type: Optional[str] = None):
    u = _uia()
    conds = []
    if automation_id:
        conds.append(u.iuia.CreatePropertyCondition(u.UIA_dll.UIA_AutomationIdPropertyId, automation_id))
    if name:
        conds.append(u.iuia.CreatePropertyCondition(u.UIA_dll.UIA_NamePropertyId, name))
    if control_type:
        ct = u.known_control_types.get(control_type)
        if ct is None:
            raise ValueError(f"Unknown control_type '{control_type}'. Examples: Button, MenuItem, Edit, Text, TabItem, ListItem, CheckBox, ComboBox.")
        conds.append(u.iuia.CreatePropertyCondition(u.UIA_dll.UIA_ControlTypePropertyId, ct))
    if not conds:
        return u.true_condition
    c = conds[0]
    for nxt in conds[1:]:
        c = u.iuia.CreateAndCondition(c, nxt)
    return c


def _find_all(root, automation_id=None, name=None, control_type=None, scope="descendants") -> list:
    u = _uia()
    arr = root.element_info.element.FindAll(u.tree_scope[scope], _condition(automation_id, name, control_type))
    return [_wrap(arr.GetElement(i)) for i in range(arr.Length)]


def _find_first(root, automation_id=None, name=None, control_type=None, children_first: bool = True):
    """Search direct children first (cheap), then the whole subtree (can take seconds on Camtasia's big WPF tree)."""
    u = _uia()
    cond = _condition(automation_id, name, control_type)
    el = None
    if children_first:
        el = root.element_info.element.FindFirst(u.tree_scope["children"], cond)
    if not el:
        el = root.element_info.element.FindFirst(u.tree_scope["descendants"], cond)
    return _wrap(el) if el else None


def _describe(w) -> dict:
    ei = w.element_info
    r = ei.rectangle
    d = {
        "name": ei.name,
        "control_type": ei.control_type,
        "automation_id": ei.automation_id,
        "class_name": ei.class_name,
        "rect": [r.left, r.top, r.right, r.bottom],
        "enabled": ei.enabled,
    }
    try:
        if ei.control_type == "Edit":
            d["value"] = w.get_value()
    except Exception:
        pass
    return {k: v for k, v in d.items() if v not in ("", None)}


def _focus(w) -> None:
    import win32con
    import win32gui

    hwnd = w.handle
    if hwnd and win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.4)
    try:
        w.set_focus()
    except Exception:
        pass
    time.sleep(0.15)


def _open_project_name() -> Optional[str]:
    """Name of the project currently open in the editor (e.g. 'Demo.tscproj'), or None."""
    try:
        w = _main_window(required=False)
        if w is None:
            return None
        lbl = _find_first(w, automation_id="t-ProjectTitleLabel")
        return (lbl.window_text() or "").strip() if lbl else None
    except Exception:
        return None


def _normalize_label(s: str) -> str:
    return s.replace("_", "").replace("&", "").replace("\u2026", "").replace("...", "").strip().lower()


# --------------------------------------------------------------------------- project file helpers


def _resolve_project(path: str) -> Path:
    p = Path(path).expanduser()
    if p.is_dir():
        inner = p / p.name
        if inner.is_file():
            return inner
        found = list(p.glob("*.tscproj"))
        if len(found) == 1 and found[0].is_file():
            return found[0]
        raise FileNotFoundError(f"No .tscproj file found inside bundle folder {p}")
    if p.is_file():
        return p
    raise FileNotFoundError(f"Project not found: {p}")


def _load(path: Path) -> dict:
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def _guard_open(path: Path, force: bool) -> None:
    if force:
        return
    open_name = _open_project_name()
    if open_name and open_name.lower().rstrip(" *") == path.name.lower():
        raise RuntimeError(
            f"'{path.name}' is open in Camtasia. Editing the file now would be overwritten when Camtasia saves. "
            "Close the project in Camtasia first (or pass force=True), then reopen it with camtasia_launch."
        )


def _save(path: Path, data: dict, backup: bool = True) -> Optional[str]:
    bak = None
    if backup and path.exists():
        bak = str(path) + ".bak"
        shutil.copy2(path, bak)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)
    return bak


def _rate(d: dict) -> int:
    return int(d.get("editRate") or 30)


def _sec(ticks: float, rate: int) -> float:
    return round(float(ticks) / rate, 4)


def _ticks(seconds: float, rate: int) -> int:
    return int(round(float(seconds) * rate))


def _tracks(d: dict) -> list:
    scenes = d["timeline"]["sceneTrack"].setdefault("scenes", [])
    if not scenes:
        scenes.append({"csml": {"tracks": []}})
    return scenes[0]["csml"].setdefault("tracks", [])


def _max_id(o: Any) -> int:
    m = 0
    if isinstance(o, dict):
        if isinstance(o.get("id"), int):
            m = o["id"]
        for v in o.values():
            m = max(m, _max_id(v))
    elif isinstance(o, list):
        for v in o:
            m = max(m, _max_id(v))
    return m


def _new_track_attributes(d: dict) -> dict:
    if d.get("version", "8.0") >= "5.0":
        return {"ident": "", "audioMuted": False, "videoHidden": False, "magnetic": False, "matte": 0, "solo": False,
                "metadata": {"IsLocked": "False", "WinTrackHeight": "56"}}
    return {"ident": "", "audioMuted": False, "videoHidden": False, "metadata": {"IsLocked": "False", "trackHeight": "48"}}


def _ensure_track(d: dict, index: int) -> dict:
    tracks = _tracks(d)
    attrs = d["timeline"].setdefault("trackAttributes", [])
    while len(tracks) <= index:
        tracks.append({"trackIndex": len(tracks), "medias": []})
    while len(attrs) < len(tracks):
        attrs.append(_new_track_attributes(d))
    return tracks[index]


def _clip_end(m: dict) -> int:
    return int(m.get("start", 0)) + int(m.get("duration", 0))


def _overlaps(track: dict, start: int, dur: int, ignore_id: Optional[int] = None) -> list:
    out = []
    for m in track.get("medias", []):
        if ignore_id is not None and m.get("id") == ignore_id:
            continue
        if start < _clip_end(m) and m.get("start", 0) < start + dur:
            out.append(m.get("id"))
    return out


def _pick_track(d: dict, start: int, dur: int, track: Optional[int]) -> int:
    tracks = _tracks(d)
    if track is not None:
        if track < 0:
            raise ValueError("track must be >= 0")
        if track < len(tracks):
            clash = _overlaps(tracks[track], start, dur)
            if clash:
                raise ValueError(f"Track {track} already has clip(s) {clash} in that time range. Choose another track or start time.")
        return track
    for i, t in enumerate(tracks):
        if not _overlaps(t, start, dur):
            return i
    return len(tracks)


def _sort_track(track: dict) -> None:
    track["medias"].sort(key=lambda m: m.get("start", 0))


def _source_by_id(d: dict, sid) -> Optional[dict]:
    for s in d.get("sourceBin", []):
        if s.get("id") == sid:
            return s
    return None


def _clip_name(m: dict) -> str:
    t = m.get("_type")
    if t == "Callout":
        return (m.get("def", {}).get("text") or m.get("def", {}).get("shape") or "callout")[:80]
    if t == "UnifiedMedia":
        return (m.get("video") or {}).get("attributes", {}).get("ident", "")
    return m.get("attributes", {}).get("ident", "")


def _clip_src(m: dict):
    if m.get("_type") == "UnifiedMedia":
        return (m.get("video") or m.get("audio") or {}).get("src")
    return m.get("src")


def _clip_summary(d: dict, m: dict, track_index: int) -> dict:
    r = _rate(d)
    out = {
        "id": m.get("id"),
        "type": m.get("_type"),
        "name": _clip_name(m),
        "track": track_index,
        "start_s": _sec(m.get("start", 0), r),
        "duration_s": _sec(m.get("duration", 0), r),
        "end_s": _sec(_clip_end(m), r),
    }
    if m.get("_type") not in ("IMFile", "Callout", "Group"):
        out["media_start_s"] = _sec(m.get("mediaStart", 0), r)
    if m.get("scalar", 1) not in (1, "1"):
        out["speed_scalar"] = m.get("scalar")
    src = _clip_src(m)
    if src is not None:
        s = _source_by_id(d, src)
        out["source_id"] = src
        if s:
            out["source"] = s.get("src")
    if m.get("_type") == "Group":
        out["group_tracks"] = len(m.get("tracks", []))
        out["group_clips"] = sum(len(t.get("medias", [])) for t in m.get("tracks", []))
    fx = [e.get("effectName") for e in m.get("effects", []) if isinstance(e, dict) and e.get("effectName")]
    if fx:
        out["effects"] = fx
    return out


def _find_clip(d: dict, clip_id: int):
    for ti, t in enumerate(_tracks(d)):
        for m in t.get("medias", []):
            if m.get("id") == clip_id:
                return ti, t, m
    raise ValueError(f"Clip id {clip_id} not found on the top-level timeline (use camtasia_get_project to list clip ids).")


def _markers(d: dict) -> list:
    toc = (d["timeline"].get("parameters") or {}).get("toc") or {}
    r = _rate(d)
    return [{"time_s": _sec(k.get("time", 0), r), "name": k.get("value", "")} for k in toc.get("keyframes", [])]


def _source_path(project: Path, src: str) -> Path:
    p = Path(src)
    return p if p.is_absolute() else (project.parent / src).resolve()


def _rel_or_abs(project: Path, media: Path) -> str:
    try:
        rel = media.resolve().relative_to(project.parent.resolve())
        return str(rel).replace("\\", "/") if len(rel.parts) > 1 else rel.name
    except ValueError:
        return str(media.resolve())


# --------------------------------------------------------------------------- media probing


def _mp4_tracks(path: Path) -> list[dict]:
    """Minimal ISO-BMFF parser: returns [{'handler': 'vide'|'soun', 'timescale', 'channels', 'sample_rate', 'bits'}]."""

    def boxes(f, start, end):
        pos = start
        while pos + 8 <= end:
            f.seek(pos)
            hdr = f.read(8)
            if len(hdr) < 8:
                return
            size, typ = struct.unpack(">I4s", hdr)
            hlen = 8
            if size == 1:
                size = struct.unpack(">Q", f.read(8))[0]
                hlen = 16
            elif size == 0:
                size = end - pos
            if size < hlen:
                return
            yield typ.decode("latin-1"), pos + hlen, pos + size
            pos += size

    out = []
    with open(path, "rb") as f:
        f.seek(0, 2)
        fsize = f.tell()
        for typ, s, e in boxes(f, 0, fsize):
            if typ != "moov":
                continue
            for t2, s2, e2 in boxes(f, s, e):
                if t2 != "trak":
                    continue
                info: dict = {}
                for t3, s3, e3 in boxes(f, s2, e2):
                    if t3 != "mdia":
                        continue
                    for t4, s4, e4 in boxes(f, s3, e3):
                        if t4 == "hdlr":
                            f.seek(s4 + 8)
                            info["handler"] = f.read(4).decode("latin-1")
                        elif t4 == "mdhd":
                            f.seek(s4)
                            ver = f.read(1)[0]
                            f.seek(s4 + (20 if ver == 1 else 12))
                            info["timescale"] = struct.unpack(">I", f.read(4))[0]
                            info["duration"] = struct.unpack(">Q" if ver == 1 else ">I", f.read(8 if ver == 1 else 4))[0]
                        elif t4 == "minf":
                            for t5, s5, e5 in boxes(f, s4, e4):
                                if t5 != "stbl":
                                    continue
                                for t6, s6, e6 in boxes(f, s5, e5):
                                    if t6 == "stsd" and e6 - s6 > 8 + 36:
                                        f.seek(s6 + 8)  # version/flags + entry_count
                                        entry = f.read(36)
                                        info["_entry"] = entry
                out.append(info)
    for info in out:
        entry = info.pop("_entry", None)
        if info.get("handler") == "soun" and entry and len(entry) >= 36:
            info["channels"] = struct.unpack(">H", entry[24:26])[0]
            info["bits"] = struct.unpack(">H", entry[26:28])[0]
            info["sample_rate"] = struct.unpack(">I", entry[32:36])[0] >> 16
    return out


def _probe(path: Path) -> dict:
    ext = path.suffix.lower()
    kind = "image" if ext in IMAGE_EXT else "audio" if ext in AUDIO_EXT else "video" if ext in VIDEO_EXT else None
    if ext == ".trec":
        raise ValueError(
            ".trec recordings contain multiple streams (screen, camera, cursor, audio) and must be imported through "
            "Camtasia itself. Open the project and use camtasia_run_shortcut('ImportMedia') or drag the file in."
        )
    if kind is None:
        raise ValueError(f"Unsupported media type '{ext}'.")
    info: dict = {"kind": kind}
    props: dict = {}
    try:
        from win32com.propsys import propsys, pscon

        st = propsys.SHGetPropertyStoreFromParsingName(str(path))
        for key in ("Media_Duration", "Video_FrameWidth", "Video_FrameHeight", "Video_FrameRate", "Audio_SampleRate",
                    "Audio_ChannelCount", "Audio_SampleSize", "Image_HorizontalSize", "Image_VerticalSize"):
            try:
                props[key] = st.GetValue(getattr(pscon, "PKEY_" + key)).GetValue()
            except Exception:
                props[key] = None
    except Exception:
        pass
    if kind == "image":
        w, h = props.get("Image_HorizontalSize"), props.get("Image_VerticalSize")
        if not (w and h):
            from PIL import Image as PILImage

            with PILImage.open(path) as im:
                w, h = im.size
        info.update(width=int(w), height=int(h))
        return info
    dur = props.get("Media_Duration")
    if not dur:
        raise ValueError(f"Could not read the duration of {path.name} (Windows has no property handler for it).")
    info["duration_100ns"] = int(dur)
    if kind == "video":
        w, h = props.get("Video_FrameWidth"), props.get("Video_FrameHeight")
        if not (w and h):
            raise ValueError(f"Could not read the frame size of {path.name}.")
        info.update(width=int(w), height=int(h), fps=round((props.get("Video_FrameRate") or 30000) / 1000, 3))
        audio = None
        if ext in (".mp4", ".mov", ".m4v"):
            try:
                mp4 = _mp4_tracks(path)
                audio = next((t for t in mp4 if t.get("handler") == "soun"), None)
                vtrack = next((t for t in mp4 if t.get("handler") == "vide"), None)
                # Camtasia stores mp4 source tracks in each track's own mdhd timescale
                if vtrack and vtrack.get("timescale") and vtrack.get("duration"):
                    info["video_timebase"] = (int(vtrack["timescale"]), int(vtrack["duration"]))
                    info["duration_100ns"] = int(round(vtrack["duration"] / vtrack["timescale"] * SOURCE_EDIT_RATE))
                # Camtasia keeps source tracks in file order; clips reference them by index (trackNumber)
                info["audio_first"] = bool(audio and vtrack and mp4.index(audio) < mp4.index(vtrack))
            except Exception:
                audio = None
        elif props.get("Audio_ChannelCount"):
            audio = {"channels": props["Audio_ChannelCount"], "sample_rate": props.get("Audio_SampleRate"),
                     "bits": props.get("Audio_SampleSize")}
        if audio:
            info["audio"] = {"channels": int(audio.get("channels") or 2), "sample_rate": int(audio.get("sample_rate") or 48000),
                             "bits": int(audio.get("bits") or 16)}
            if audio.get("timescale") and audio.get("duration"):
                info["audio"]["timebase"] = (int(audio["timescale"]), int(audio["duration"]))
    else:
        info["audio"] = {"channels": int(props.get("Audio_ChannelCount") or 2), "sample_rate": int(props.get("Audio_SampleRate") or 44100),
                         "bits": int(props.get("Audio_SampleSize") or 16)}
    return info


def _last_mod(media: Path) -> str:
    return datetime.fromtimestamp(media.stat().st_mtime, timezone.utc).strftime("%Y%m%dT%H%M%S")


def _audio_source_track(a: dict, dur: int, meta: str = "") -> dict:
    rate, rng = a.get("timebase") or (SOURCE_EDIT_RATE, dur)
    return {"range": [0, rng], "type": 2, "editRate": rate, "trackRect": [0, 0, 0, 0],
            "sampleRate": a["sample_rate"], "bitDepth": a["bits"], "numChannels": a["channels"], "metaData": meta}


def _build_source(sid: int, src: str, media: Path, info: dict) -> dict:
    now = datetime.now()
    meta = media.name + ";"
    entry: dict = {
        "id": sid,
        "src": src,
        "rect": [0, 0, info.get("width", 0), info.get("height", 0)],
        "lastMod": _last_mod(media),
        "loudnessNormalization": True,
        "sourceTracks": [],
        "metadata": {"timeAdded": now.strftime("%Y%m%dT%H%M%S.%f")},
    }
    if info["kind"] == "image":
        entry["sourceTracks"].append({"range": [0, 1], "type": 1, "editRate": 600, "trackRect": [0, 0, info["width"], info["height"]],
                                      "sampleRate": 0, "bitDepth": 0, "numChannels": 0, "metaData": ""})
    elif info["kind"] == "video":
        dur = info["duration_100ns"]
        rate, rng = info.get("video_timebase") or (SOURCE_EDIT_RATE, dur)
        entry["sourceTracks"].append({"range": [0, rng], "type": 0, "editRate": rate,
                                      "trackRect": [0, 0, info["width"], info["height"]],
                                      "sampleRate": int(info["fps"]) if float(info["fps"]).is_integer() else info["fps"],
                                      "bitDepth": 24, "numChannels": 0, "integratedLUFS": 100.0, "peakLevel": -1.0,
                                      "metaData": meta})
        if info.get("audio"):
            entry["sourceTracks"].append(_audio_source_track(info["audio"], dur, meta))
            if info.get("audio_first"):
                entry["sourceTracks"].reverse()
    else:
        entry["sourceTracks"].append(_audio_source_track(info["audio"], info["duration_100ns"], meta))
    return entry


def _source_duration_ticks(d: dict, source: dict) -> Optional[int]:
    best = None
    for st in source.get("sourceTracks", []):
        if st.get("type") == 1:
            continue
        rng, er = st.get("range") or [0, 0], st.get("editRate") or 1
        t = int(round((rng[1] - rng[0]) / float(er) * _rate(d)))
        best = t if best is None else max(best, t)
    return best


def _clip_metadata() -> dict:
    return {"audiateLinkedSession": "", "clipSpeedAttribute": {"type": "bool", "value": False}}


def _scale_for(d: dict, w: int, h: int, scale_mode: str) -> float:
    if not (w and h) or scale_mode == "none":
        return 1.0
    fit = min(float(d["width"]) / w, float(d["height"]) / h)
    if scale_mode == "fit":
        return round(fit, 6)
    return round(min(1.0, fit), 6)  # shrink_to_fit


def _visual_clip(cid: int, typ: str, sid: int, name: str, scale: float, start: int, dur: int, mstart: int, mdur, track_no: int = 0) -> dict:
    c = {"id": cid, "_type": typ, "src": sid, "trackNumber": track_no, "attributes": {"ident": name},
         "parameters": {"scale0": scale, "scale1": scale} if scale != 1.0 else {}, "effects": [],
         "start": start, "duration": dur, "mediaStart": mstart, "mediaDuration": mdur, "scalar": 1,
         "metadata": _clip_metadata(), "animationTracks": {}}
    if typ == "IMFile":
        c["trimStartSum"] = 0
    return c


def _audio_clip(cid: int, sid: int, name: str, channels: int, start: int, dur: int, mstart: int, track_no: int) -> dict:
    return {"id": cid, "_type": "AMFile", "src": sid, "trackNumber": track_no,
            "attributes": {"ident": name, "gain": 1.0, "mixToMono": False, "loudnessNormalization": True, "sourceFileOffset": 0},
            "channelNumber": ",".join(str(i) for i in range(max(1, channels))), "effects": [],
            "start": start, "duration": dur, "mediaStart": mstart, "mediaDuration": dur, "scalar": 1,
            "metadata": _clip_metadata(), "animationTracks": {}}


def _set_timing(m: dict, start=None, dur=None, mstart=None) -> None:
    targets = [m] + [m[k] for k in ("video", "audio") if isinstance(m.get(k), dict)]
    for t in targets:
        if start is not None:
            t["start"] = start
        if dur is not None:
            t["duration"] = dur
            if t.get("_type") != "IMFile" and m.get("_type") != "Group":
                t["mediaDuration"] = dur
        if mstart is not None:
            t["mediaStart"] = mstart


def _is_speed_changed(m: dict) -> bool:
    return any(str(t.get("scalar", 1)) not in ("1", "1.0") for t in [m] + [m[k] for k in ("video", "audio") if isinstance(m.get(k), dict)])


def _hex_rgba(color: str) -> tuple[int, int, int, int]:
    c = color.lstrip("#")
    if len(c) not in (6, 8):
        raise ValueError("color must be '#RRGGBB' or '#RRGGBBAA'")
    vals = [int(c[i:i + 2], 16) for i in range(0, len(c), 2)]
    if len(vals) == 3:
        vals.append(255)
    return tuple(vals)  # type: ignore[return-value]


# =========================================================================== TOOLS: discovery


@mcp.tool()
def camtasia_status() -> dict:
    """Camtasia install/version, whether the editor and recorder are running, the project currently open
    in the editor, recent projects and recent recordings."""
    procs = _processes()
    info = _install_info()
    info["running"] = procs
    info["open_project"] = _open_project_name() if any(p["name"] == STUDIO_PROCESS for p in procs) else None
    info["recent_projects"] = _mru("FileSaveAsMru")[:15]
    info["recent_recordings"] = _mru("RecentRecordingsMru")[:10]
    sf = _shortcuts_file()
    info["keyboard_shortcuts_file"] = str(sf) if sf else None
    return info


@mcp.tool()
def camtasia_find_projects(folder: Optional[str] = None, max_results: int = 50) -> dict:
    """Find Camtasia projects (.tscproj). With no folder, returns the recent-projects list plus projects
    found under Documents\\Camtasia. With a folder, searches it recursively."""
    results: list[dict] = []
    seen: set[str] = set()

    def add(p: Path, origin: str):
        try:
            f = _resolve_project(str(p))
        except Exception:
            return
        k = str(f).lower()
        if k in seen:
            return
        seen.add(k)
        st = f.stat()
        results.append({"project_file": str(f), "modified": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                        "size_kb": round(st.st_size / 1024, 1), "origin": origin})

    if folder:
        root = Path(folder)
        for p in root.rglob("*.tscproj"):
            if len(results) >= max_results:
                break
            if p.is_file() and not p.name.endswith(".autosave.tscproj"):
                add(p, "search")
    else:
        for p in _mru("FileSaveAsMru"):
            add(Path(p), "recent")
        docs = [Path.home() / "Documents" / "Camtasia"] + list(Path.home().glob("OneDrive*/Documents/Camtasia"))
        for dd in docs:
            if dd.exists():
                for p in dd.rglob("*.tscproj"):
                    if len(results) >= max_results:
                        break
                    if p.is_file():
                        add(p, "documents")
    return {"count": len(results), "projects": results[:max_results]}


@mcp.tool()
def camtasia_get_project(project_path: str, include_clips: bool = True) -> dict:
    """Summarise a Camtasia project: canvas size, frame rate, duration, media bin (with missing-file check),
    tracks and their clips (ids, types, names, times in seconds), and timeline markers.
    project_path may be the .tscproj file or the .tscproj bundle folder."""
    path = _resolve_project(project_path)
    d = _load(path)
    r = _rate(d)
    tracks = _tracks(d)
    attrs = d["timeline"].get("trackAttributes", [])
    duration = max((_clip_end(m) for t in tracks for m in t.get("medias", [])), default=0)
    bin_ = []
    for s in d.get("sourceBin", []):
        sp = _source_path(path, s.get("src", ""))
        item = {"source_id": s.get("id"), "src": s.get("src"), "exists": sp.exists(),
                "kinds": sorted({{0: "video", 1: "image", 2: "audio"}.get(t.get("type"), str(t.get("type"))) for t in s.get("sourceTracks", [])}),
                "rect": s.get("rect")}
        dt = _source_duration_ticks(d, s)
        if dt:
            item["duration_s"] = _sec(dt, r)
        bin_.append(item)
    out = {
        "project_file": str(path),
        "title": d.get("title") or (d.get("metadata") or {}).get("Title", ""),
        "format_version": d.get("version"),
        "authoring_client": d.get("authoringClientName"),
        "canvas": {"width": d.get("width"), "height": d.get("height")},
        "frame_rate": d.get("videoFormatFrameRate"),
        "edit_rate": r,
        "duration_s": _sec(duration, r),
        "media_bin": bin_,
        "markers": _markers(d),
        "open_in_camtasia": (_open_project_name() or "").lower().rstrip(" *") == path.name.lower(),
    }
    track_list = []
    for i, t in enumerate(tracks):
        a = attrs[i] if i < len(attrs) else {}
        tr = {"track": i, "name": a.get("ident", ""), "muted": a.get("audioMuted", False), "hidden": a.get("videoHidden", False),
              "locked": (a.get("metadata") or {}).get("IsLocked") == "True", "clip_count": len(t.get("medias", []))}
        if include_clips:
            tr["clips"] = [_clip_summary(d, m, i) for m in t.get("medias", [])]
        track_list.append(tr)
    out["tracks"] = track_list
    return out


# =========================================================================== TOOLS: project editing


@mcp.tool()
def camtasia_create_project(project_path: str, width: int = 1920, height: int = 1080, fps: int = 30,
                            title: str = "", overwrite: bool = False) -> dict:
    """Create a new, empty Camtasia 2024 project. Like Camtasia, it is saved as a bundle folder:
    'D:\\Videos\\Demo' or 'D:\\Videos\\Demo.tscproj' -> 'D:\\Videos\\Demo.tscproj\\Demo.tscproj'."""
    p = Path(project_path)
    stem = p.stem if p.suffix.lower() == ".tscproj" else p.name
    bundle = (p if p.suffix.lower() == ".tscproj" else p.with_name(stem + ".tscproj"))
    if bundle.parent.name.lower() == bundle.name.lower():
        bundle = bundle.parent  # caller passed the inner file path
    f = bundle / (stem + ".tscproj")
    if f.exists() and not overwrite:
        raise FileExistsError(f"{f} already exists (pass overwrite=True to replace it).")
    bundle.mkdir(parents=True, exist_ok=True)
    data = {
        "title": title, "description": "", "author": "", "targetLoudness": -18.0,
        "shouldApplyLoudnessNormalization": True, "videoFormatFrameRate": fps, "audioFormatSampleRate": 44100,
        "allowSubFrameEditing": False, "width": float(width), "height": float(height), "version": "8.0",
        "editRate": V8_EDIT_RATE, "authoringClientName": {"name": "Camtasia", "platform": "Windows", "version": "2024.0.0"},
        "sourceBin": [],
        "timeline": {
            "id": 1, "sceneTrack": {"scenes": [{"csml": {"tracks": [{"trackIndex": 0, "medias": []}, {"trackIndex": 1, "medias": []}]}}]},
            "trackAttributes": [],
            "captionAttributes": {"enabled": True, "fontName": "Arial", "fontSize": 64, "backgroundColor": [0, 0, 0, 191],
                                  "foregroundColor": [255, 255, 255, 255], "lang": "en", "alignment": 0, "defaultFontSize": True,
                                  "opacity": 0.5, "backgroundEnabled": True, "backgroundOnlyAroundText": True},
            "gain": 1.0, "legacyAttenuateAudioMix": False, "backgroundColor": [0, 0, 0, 255],
        },
        "metadata": {"Date": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"), "IsAutoSave": {"type": "bool", "value": False},
                     "IsStandalone": {"type": "bool", "value": True}, "Language": "ENU", "ProfileName": "",
                     "Title": title or stem, "calloutStyle": "Basic"},
    }
    data["timeline"]["trackAttributes"] = [_new_track_attributes(data), _new_track_attributes(data)]
    _save(f, data, backup=False)
    return {"project_file": str(f), "bundle_folder": str(bundle), "canvas": [width, height], "fps": fps}


@mcp.tool()
def camtasia_set_project_settings(project_path: str, width: Optional[int] = None, height: Optional[int] = None,
                                  fps: Optional[int] = None, title: Optional[str] = None, description: Optional[str] = None,
                                  author: Optional[str] = None, background_color: Optional[str] = None,
                                  force: bool = False) -> dict:
    """Change canvas size, frame rate, title/description/author or background colour ('#RRGGBB') of a project.
    Refuses if the project is open in Camtasia (unless force=True). A .bak backup is written first."""
    path = _resolve_project(project_path)
    _guard_open(path, force)
    d = _load(path)
    if width is not None:
        d["width"] = float(width)
    if height is not None:
        d["height"] = float(height)
    if fps is not None:
        d["videoFormatFrameRate"] = fps
    for k, v in (("title", title), ("description", description), ("author", author)):
        if v is not None:
            d[k] = v
    if title is not None:
        d.setdefault("metadata", {})["Title"] = title
    if background_color:
        d["timeline"]["backgroundColor"] = list(_hex_rgba(background_color))
    bak = _save(path, d)
    return {"saved": str(path), "backup": bak, "canvas": [d["width"], d["height"]], "fps": d.get("videoFormatFrameRate")}


@mcp.tool()
def camtasia_add_media(project_path: str, media_path: str, add_to_timeline: bool = True, track: Optional[int] = None,
                       start_seconds: Optional[float] = None, duration_seconds: Optional[float] = None,
                       media_start_seconds: float = 0.0, scale_mode: str = "shrink_to_fit",
                       copy_into_project: bool = True, force: bool = False) -> dict:
    """Import a video (mp4/mov/avi/wmv...), audio (mp3/wav/m4a...) or image (png/jpg...) into a project's media bin
    and optionally place it on the timeline.
    - track: track index (0 = bottom). Omitted -> lowest track that is free at that time.
    - start_seconds: omitted -> appended after the last clip on the chosen track (track 0 if track omitted).
    - duration_seconds: omitted -> full media length (images default to 5 s).
    - media_start_seconds: trim from the start of the source.
    - scale_mode: 'shrink_to_fit' (default, like Camtasia), 'fit' (scale up or down to canvas) or 'none'.
    - copy_into_project: copy the file into the .tscproj bundle folder (default, same as Camtasia's own import);
      False references the file at its current absolute path.
    .trec recordings must be imported via the Camtasia UI. Refuses if the project is open in Camtasia unless force=True."""
    path = _resolve_project(project_path)
    _guard_open(path, force)
    media = Path(media_path)
    if not media.is_file():
        raise FileNotFoundError(media)
    info = _probe(media)
    if copy_into_project:
        dest = path.parent / media.name
        n = 2
        while dest.exists() and dest.resolve() != media.resolve() and \
                (dest.stat().st_size != media.stat().st_size or int(dest.stat().st_mtime) != int(media.stat().st_mtime)):
            dest = path.parent / f"{media.stem} ({n}){media.suffix}"
            n += 1
        if not dest.exists():
            shutil.copy2(media, dest)
        media = dest
    d = _load(path)
    r = _rate(d)
    next_id = _max_id(d) + 1
    sid = next_id
    next_id += 1
    source = _build_source(sid, _rel_or_abs(path, media), media, info)
    d.setdefault("sourceBin", []).append(source)
    result: dict = {"source_id": sid, "media": info}
    if add_to_timeline:
        name = media.stem
        if info["kind"] == "image":
            dur = _ticks(duration_seconds if duration_seconds is not None else 5.0, r)
            mstart = 0
        else:
            full = int(round(info["duration_100ns"] / SOURCE_EDIT_RATE * r))
            mstart = _ticks(media_start_seconds, r)
            if mstart >= full:
                raise ValueError("media_start_seconds is beyond the end of the media.")
            dur = _ticks(duration_seconds, r) if duration_seconds is not None else full - mstart
            if mstart + dur > full + 1:
                raise ValueError(f"Requested range exceeds media length ({_sec(full, r)} s).")
        if start_seconds is None:
            ti = track if track is not None else 0
            existing = _tracks(d)[ti]["medias"] if ti < len(_tracks(d)) else []
            start = max((_clip_end(m) for m in existing), default=0)
            ti = _pick_track(d, start, dur, ti)
        else:
            start = _ticks(start_seconds, r)
            ti = _pick_track(d, start, dur, track)
        t = _ensure_track(d, ti)
        cid = next_id
        if info["kind"] == "image":
            clip = _visual_clip(cid, "IMFile", sid, name, _scale_for(d, info["width"], info["height"], scale_mode), start, dur, 0, 1)
        elif info["kind"] == "audio":
            clip = _audio_clip(cid, sid, name, info["audio"]["channels"], start, dur, mstart, 0)
        elif info.get("audio"):
            scale = _scale_for(d, info["width"], info["height"], scale_mode)
            vi, ai = (1, 0) if info.get("audio_first") else (0, 1)
            v = _visual_clip(cid + 1, "VMFile", sid, name, scale, start, dur, mstart, dur, vi)
            a = _audio_clip(cid + 2, sid, "", info["audio"]["channels"], start, dur, mstart, ai)
            clip = {"id": cid, "_type": "UnifiedMedia", "video": v, "audio": a, "start": start, "duration": dur,
                    "mediaStart": mstart, "mediaDuration": dur, "scalar": 1, "metadata": _clip_metadata()}
        else:
            clip = _visual_clip(cid, "VMFile", sid, name, _scale_for(d, info["width"], info["height"], scale_mode), start, dur, mstart, dur)
        t["medias"].append(clip)
        _sort_track(t)
        result["clip"] = _clip_summary(d, clip, ti)
    result["backup"] = _save(path, d)
    return result


@mcp.tool()
def camtasia_add_text(project_path: str, text: str, start_seconds: float = 0.0, duration_seconds: float = 5.0,
                      track: Optional[int] = None, font_name: str = "Arial", font_size: float = 72.0,
                      color: str = "#FFFFFF", bold: bool = False, x: float = 0.0, y: float = 0.0,
                      alignment: str = "center", force: bool = False) -> dict:
    """Add a text annotation (basic text callout) to the timeline.
    x/y are pixel offsets from the canvas centre (y positive = up). alignment: left|center|right.
    track omitted -> lowest free track at that time. Refuses if the project is open in Camtasia unless force=True."""
    path = _resolve_project(project_path)
    _guard_open(path, force)
    if alignment not in ("left", "center", "right"):
        raise ValueError("alignment must be left, center or right")
    d = _load(path)
    r = _rate(d)
    start, dur = _ticks(start_seconds, r), _ticks(duration_seconds, r)
    ti = _pick_track(d, start, dur, track)
    t = _ensure_track(d, ti)
    rr, gg, bb, aa = _hex_rgba(color)
    n = len(text)
    weight = 700 if bold else 400
    lines = max(1, text.count("\n") + 1)
    attrs = [
        {"name": "fontName", "rangeEnd": n, "rangeStart": 0, "value": font_name, "valueType": "string"},
        {"name": "fontSize", "rangeEnd": n, "rangeStart": 0, "value": float(font_size), "valueType": "double"},
        {"name": "fontWeight", "rangeEnd": n, "rangeStart": 0, "value": weight, "valueType": "int"},
        {"name": "fgColor", "rangeEnd": n, "rangeStart": 0, "value": f"({rr},{gg},{bb},{aa})", "valueType": "color"},
        {"name": "underline", "rangeEnd": n, "rangeStart": 0, "value": 0, "valueType": "int"},
        {"name": "strikethrough", "rangeEnd": n, "rangeStart": 0, "value": 0, "valueType": "int"},
        {"name": "fontItalic", "rangeEnd": n, "rangeStart": 0, "value": 0, "valueType": "int"},
        {"name": "kerning", "rangeEnd": n, "rangeStart": 0, "value": 0.0, "valueType": "double"},
    ]
    cid = _max_id(d) + 1
    clip = {
        "id": cid, "_type": "Callout",
        "def": {
            "kind": "remix", "shape": "text", "style": "basic", "corner-radius": 0.0, "enable-ligatures": 1.0,
            "height": float(round(font_size * 1.5 * lines + 20, 2)), "line-spacing": 0.0, "tracking": 0.0,
            "width": float(round(d["width"] * 0.8, 2)), "word-wrap": 1.0, "horizontal-alignment": alignment,
            "resize-behavior": "resizeText", "text": text, "vertical-alignment": "center",
            "font": {"color-blue": bb / 255, "color-green": gg / 255, "color-opacity": aa / 255, "color-red": rr / 255,
                     "size": float(font_size), "name": font_name, "weight": "Bold" if bold else "Regular"},
            "textAttributes": {"type": "textAttributeList", "keyframes": [{"endTime": 0, "time": 0, "value": attrs, "duration": 0}]},
        },
        "attributes": {"ident": "", "autoRotateText": True},
        "parameters": {"translation0": float(x), "translation1": float(y)},
        "effects": [], "start": start, "duration": dur, "mediaStart": 0, "mediaDuration": dur, "scalar": 1,
        "metadata": _clip_metadata(), "animationTracks": {},
    }
    t["medias"].append(clip)
    _sort_track(t)
    bak = _save(path, d)
    return {"clip": _clip_summary(d, clip, ti), "backup": bak}


@mcp.tool()
def camtasia_update_clip(project_path: str, clip_id: int, start_seconds: Optional[float] = None,
                         duration_seconds: Optional[float] = None, media_start_seconds: Optional[float] = None,
                         track: Optional[int] = None, name: Optional[str] = None, text: Optional[str] = None,
                         x: Optional[float] = None, y: Optional[float] = None, scale: Optional[float] = None,
                         force: bool = False) -> dict:
    """Move, trim, retime, rename or reposition a top-level timeline clip (ids from camtasia_get_project).
    media_start_seconds trims the source in-point (video/audio only). text edits a text callout.
    x/y (pixels from canvas centre, y up) and scale set the clip's default transform."""
    path = _resolve_project(project_path)
    _guard_open(path, force)
    d = _load(path)
    r = _rate(d)
    ti, t, m = _find_clip(d, clip_id)
    typ = m.get("_type")
    new_start = _ticks(start_seconds, r) if start_seconds is not None else m.get("start", 0)
    new_dur = _ticks(duration_seconds, r) if duration_seconds is not None else m.get("duration", 0)
    new_mstart = _ticks(media_start_seconds, r) if media_start_seconds is not None else None
    if new_dur <= 0:
        raise ValueError("duration must be > 0")
    if typ in ("Group",) and (duration_seconds is not None or media_start_seconds is not None):
        raise ValueError("Groups can only be moved (start/track) with this tool.")
    if (duration_seconds is not None or media_start_seconds is not None) and _is_speed_changed(m):
        raise ValueError("This clip has a speed change; trim/retime it in Camtasia instead (moving is fine).")
    if typ in ("VMFile", "AMFile", "ScreenVMFile", "UnifiedMedia"):
        src = _source_by_id(d, _clip_src(m))
        full = _source_duration_ticks(d, src) if src else None
        ms = new_mstart if new_mstart is not None else int(m.get("mediaStart", 0))
        if full and ms + new_dur > full + r // 100:
            raise ValueError(f"Clip would extend past the end of its source media ({_sec(full, r)} s).")
    dest = ti if track is None else track
    if dest < len(_tracks(d)):
        clash = _overlaps(_tracks(d)[dest], new_start, new_dur, ignore_id=clip_id)
        if clash:
            raise ValueError(f"Track {dest} has overlapping clip(s) {clash} at that time.")
    _set_timing(m, new_start, new_dur if duration_seconds is not None else None, new_mstart)
    if name is not None:
        target = m.get("video") if typ == "UnifiedMedia" else m
        target.setdefault("attributes", {})["ident"] = name
    if text is not None:
        if typ != "Callout":
            raise ValueError("text can only be set on Callout (text) clips.")
        m["def"]["text"] = text
        for kf in (m["def"].get("textAttributes") or {}).get("keyframes", []):
            for a in kf.get("value", []):
                a["rangeStart"], a["rangeEnd"] = 0, len(text)
    if x is not None or y is not None or scale is not None:
        target = m.get("video") if typ == "UnifiedMedia" else m
        params = target.setdefault("parameters", {})
        for key, val in (("translation0", x), ("translation1", y), ("scale0", scale), ("scale1", scale)):
            if val is None:
                continue
            if isinstance(params.get(key), dict):
                params[key]["defaultValue"] = float(val)
            else:
                params[key] = float(val)
    if dest != ti:
        t["medias"].remove(m)
        nt = _ensure_track(d, dest)
        nt["medias"].append(m)
        _sort_track(nt)
    else:
        _sort_track(t)
    bak = _save(path, d)
    return {"clip": _clip_summary(d, m, dest), "backup": bak}


@mcp.tool()
def camtasia_delete_clip(project_path: str, clip_id: int, force: bool = False) -> dict:
    """Delete a top-level clip from the timeline (media stays in the media bin)."""
    path = _resolve_project(project_path)
    _guard_open(path, force)
    d = _load(path)
    ti, t, m = _find_clip(d, clip_id)
    summary = _clip_summary(d, m, ti)
    t["medias"].remove(m)
    bak = _save(path, d)
    return {"deleted": summary, "backup": bak}


@mcp.tool()
def camtasia_set_track(project_path: str, track: int, name: Optional[str] = None, muted: Optional[bool] = None,
                       hidden: Optional[bool] = None, locked: Optional[bool] = None, force: bool = False) -> dict:
    """Rename, mute, hide or lock a timeline track (creates the track if it does not exist yet)."""
    path = _resolve_project(project_path)
    _guard_open(path, force)
    d = _load(path)
    _ensure_track(d, track)
    a = d["timeline"]["trackAttributes"][track]
    if name is not None:
        a["ident"] = name
    if muted is not None:
        a["audioMuted"] = muted
    if hidden is not None:
        a["videoHidden"] = hidden
    if locked is not None:
        a.setdefault("metadata", {})["IsLocked"] = "True" if locked else "False"
    bak = _save(path, d)
    return {"track": track, "attributes": a, "backup": bak}


@mcp.tool()
def camtasia_add_marker(project_path: str, time_seconds: float, name: str, force: bool = False) -> dict:
    """Add a timeline marker (shows in Camtasia's marker view / becomes a chapter/TOC entry)."""
    path = _resolve_project(project_path)
    _guard_open(path, force)
    d = _load(path)
    tk = _ticks(time_seconds, _rate(d))
    params = d["timeline"].setdefault("parameters", {})
    toc = params.setdefault("toc", {"type": "string", "keyframes": []})
    toc["keyframes"].append({"endTime": tk, "time": tk, "value": name, "duration": 0})
    toc["keyframes"].sort(key=lambda k: k.get("time", 0))
    bak = _save(path, d)
    return {"markers": _markers(d), "backup": bak}


@mcp.tool()
def camtasia_remove_marker(project_path: str, name: Optional[str] = None, time_seconds: Optional[float] = None,
                           force: bool = False) -> dict:
    """Remove timeline marker(s) matching a name and/or time (seconds, ±0.05 s)."""
    if name is None and time_seconds is None:
        raise ValueError("Give name and/or time_seconds.")
    path = _resolve_project(project_path)
    _guard_open(path, force)
    d = _load(path)
    r = _rate(d)
    toc = (d["timeline"].get("parameters") or {}).get("toc") or {"keyframes": []}
    before = len(toc["keyframes"])
    toc["keyframes"] = [k for k in toc["keyframes"]
                        if not ((name is None or k.get("value") == name)
                                and (time_seconds is None or abs(k.get("time", 0) / r - time_seconds) <= 0.05))]
    removed = before - len(toc["keyframes"])
    bak = _save(path, d) if removed else None
    return {"removed": removed, "markers": _markers(d), "backup": bak}


@mcp.tool()
def camtasia_relink_media(project_path: str, source_id: int, new_media_path: str, force: bool = False) -> dict:
    """Point a media-bin entry at a different file (e.g. to fix a missing/moved file). The new file should
    have the same content type and at least the same duration."""
    path = _resolve_project(project_path)
    _guard_open(path, force)
    new = Path(new_media_path)
    if not new.is_file():
        raise FileNotFoundError(new)
    d = _load(path)
    s = _source_by_id(d, source_id)
    if not s:
        raise ValueError(f"source_id {source_id} not in media bin")
    old = s.get("src")
    s["src"] = _rel_or_abs(path, new)
    s["lastMod"] = _last_mod(new)
    bak = _save(path, d)
    return {"source_id": source_id, "old_src": old, "new_src": s["src"], "backup": bak}


@mcp.tool()
def camtasia_restore_backup(project_path: str) -> dict:
    """Undo the last file edit made by this server by restoring '<project>.tscproj.bak'."""
    path = _resolve_project(project_path)
    bak = Path(str(path) + ".bak")
    if not bak.exists():
        raise FileNotFoundError(f"No backup at {bak}")
    _guard_open(path, False)
    shutil.copy2(bak, path)
    return {"restored": str(path), "from": str(bak)}


# =========================================================================== TOOLS: app control


@mcp.tool()
def camtasia_launch(project_path: Optional[str] = None, wait_seconds: float = 20.0) -> dict:
    """Start the Camtasia editor, optionally opening a project (file or bundle folder). If Camtasia is already
    running the project is handed to the running instance (Camtasia may prompt to save the current project)."""
    d = _install_dir()
    if not d:
        raise RuntimeError("Camtasia is not installed.")
    args = [str(d / STUDIO_PROCESS)]
    if project_path:
        args.append(str(_resolve_project(project_path)))
    subprocess.Popen(args, close_fds=True)
    deadline = time.time() + wait_seconds
    win = None
    while time.time() < deadline:
        try:
            win = _main_window(required=False)
            if win is not None:
                break
        except Exception:
            pass
        time.sleep(1)
    time.sleep(1.5 if project_path else 0)
    return {"launched": args, "main_window_found": win is not None, "open_project": _open_project_name()}


@mcp.tool()
def camtasia_launch_recorder() -> dict:
    """Start Camtasia Recorder (screen recording). Use camtasia_recorder_hotkey to start/stop recording."""
    d = _install_dir()
    if not d:
        raise RuntimeError("Camtasia is not installed.")
    subprocess.Popen([str(d / RECORDER_PROCESS)], close_fds=True)
    return {"launched": str(d / RECORDER_PROCESS)}


@mcp.tool()
def camtasia_recorder_hotkey(action: str) -> dict:
    """Send Camtasia Recorder's global hotkeys: action='start_pause' (F9) or 'stop' (F10).
    The recorder must be running; stopping opens the recording in the editor (default behaviour)."""
    from pywinauto import keyboard

    keys = {"start_pause": "{F9}", "stop": "{F10}"}.get(action)
    if not keys:
        raise ValueError("action must be 'start_pause' or 'stop'")
    keyboard.send_keys(keys)
    return {"sent": keys}


@mcp.tool()
def camtasia_get_ui_state() -> dict:
    """Quick read of the editor: open project name, playhead time, frame rate, top-level windows/dialogs."""
    w = _main_window()
    out: dict = {"window_title": w.window_text(), "open_project": _open_project_name()}
    for auto_id, key in (("t-CurrentEditRate", "edit_rate"), ("t-CurrentPlaybackSpeed", "playback_speed"), ("RecoveryTitle", "recovery")):
        el = _find_first(w, automation_id=auto_id)
        if el and el.window_text().strip():
            out[key] = el.window_text().strip()
    durs = _find_first(w, automation_id="DurationLabels")
    if durs:
        out["time_display"] = [x.window_text() for x in _find_all(durs, control_type="Text") if x.window_text()]
    out["windows"] = []
    for x in _top_windows():
        rc = x.rectangle()
        out["windows"].append({"title": x.window_text(), "class_name": x.element_info.class_name,
                               "minimized": rc.left <= -32000, "rect": [rc.left, rc.top, rc.right, rc.bottom]})
    return out


@mcp.tool()
def camtasia_list_controls(automation_id: Optional[str] = None, name: Optional[str] = None,
                           control_type: Optional[str] = None, parent_automation_id: Optional[str] = None,
                           window_title: Optional[str] = None, max_depth: int = 2, max_results: int = 150) -> dict:
    """Inspect Camtasia's UI. Two modes:
    - Search: give automation_id / name / control_type -> matching controls anywhere under the parent (fast, native search).
    - Browse: no filters -> walk children of the parent down to max_depth.
    parent_automation_id scopes to a sub-panel; window_title picks another Camtasia window (dialogs, detached canvas).
    Useful ids: t-FileMenu, t-EditMenu, t-ModifyMenu, t-ViewMenu, t-ExportMenu, t-HelpMenu, shareButton, recordButton,
    undoButton, redoButton, cutButton, copyButton, pasteButton, splitButton, ToolPanelContainer, trackScrollViewer."""
    root = _main_window()
    if window_title:
        root = next((x for x in _top_windows() if window_title.lower() in (x.window_text() or "").lower()), None)
        if root is None:
            raise ValueError(f"No Camtasia window with title containing '{window_title}'. See camtasia_get_ui_state().windows")
    if parent_automation_id:
        p = _find_first(root, automation_id=parent_automation_id)
        if p is None:
            raise ValueError(f"No control with automation_id '{parent_automation_id}'")
        root = p
    if automation_id or name or control_type:
        items = _find_all(root, automation_id=automation_id, name=name, control_type=control_type)
        return {"count": len(items), "controls": [_describe(x) for x in items[:max_results]]}
    out: list = []
    frontier = [(root, 0)]
    while frontier and len(out) < max_results:
        node, depth = frontier.pop(0)
        if depth >= max_depth:
            continue
        for c in _find_all(node, scope="children"):
            desc = _describe(c)
            desc["depth"] = depth + 1
            out.append(desc)
            frontier.append((c, depth + 1))
            if len(out) >= max_results:
                break
    return {"count": len(out), "truncated": len(out) >= max_results, "controls": out}


@mcp.tool()
def camtasia_click(automation_id: Optional[str] = None, name: Optional[str] = None, control_type: Optional[str] = None,
                   index: int = 0, window_title: Optional[str] = None, double_click: bool = False,
                   set_text: Optional[str] = None) -> dict:
    """Click / invoke a Camtasia control found by automation_id and/or name (+ optional control_type).
    Uses the UIA Invoke/Toggle/Select pattern when available, otherwise a real mouse click.
    set_text: instead of clicking, type this value into an Edit control (e.g. export file name)."""
    if not (automation_id or name):
        raise ValueError("Give automation_id and/or name.")
    root = _main_window()
    if window_title:
        root = next((x for x in _top_windows() if window_title.lower() in (x.window_text() or "").lower()), None)
        if root is None:
            raise ValueError(f"No Camtasia window titled like '{window_title}'")
    _focus(root)
    items = _find_all(root, automation_id=automation_id, name=name, control_type=control_type)
    if len(items) <= index:
        raise ValueError(f"Found {len(items)} matching control(s); index {index} out of range.")
    c = items[index]
    how = None
    if set_text is not None:
        try:
            c.iface_value.SetValue(set_text)
            how = "value_pattern"
        except Exception:
            c.click_input()
            from pywinauto import keyboard

            keyboard.send_keys("^a{BACKSPACE}")
            keyboard.send_keys(set_text, with_spaces=True)
            how = "typed"
    elif double_click:
        c.double_click_input()
        how = "double_click"
    else:
        for pattern, fn in (("invoke", lambda: c.invoke()), ("toggle", lambda: c.toggle()), ("select", lambda: c.select())):
            try:
                fn()
                how = pattern
                break
            except Exception:
                continue
        if how is None:
            c.click_input()
            how = "mouse_click"
    time.sleep(0.3)
    return {"control": _describe(c), "action": how}


@mcp.tool()
def camtasia_menu(path: list[str]) -> dict:
    """Open a Camtasia menu path, e.g. ["File", "Save"], ["Export", "Local File..."], ["File", "Batch Export..."],
    ["File", "Recent Projects", "<name>"]. Matching ignores case, '...' and access-key underscores.
    If the path ends on a menu/submenu (e.g. ["File"]), its items are listed and the menu is closed again -
    use this to discover menu items without triggering anything."""
    if not path:
        raise ValueError("path must contain at least the top-level menu name")
    w = _main_window()
    _focus(w)
    menubar = _find_first(w, automation_id="t-MainWindowMenu") or w
    tops = _find_all(menubar, control_type="MenuItem", scope="children")
    current = next((m for m in tops if _normalize_label(m.window_text()) == _normalize_label(path[0])), None)
    if current is None:
        raise ValueError(f"Top-level menu '{path[0]}' not found. Available: {[m.window_text() for m in tops]}")
    opened: list = []
    try:
        for depth, label in enumerate(path):
            if depth > 0:
                kids = _menu_items(current)
                nxt = next((k for k in kids if _normalize_label(k.window_text()) == _normalize_label(label)), None)
                if nxt is None:
                    raise ValueError(f"Menu item '{label}' not found under '{path[depth - 1]}'. "
                                     f"Available: {[k.window_text() for k in kids]}")
                current = nxt
            is_last = depth == len(path) - 1
            if depth == 0 or not _is_leaf(current):
                current.expand()
                opened.append(current)
                time.sleep(0.4)
                continue
            if not is_last:
                raise ValueError(f"'{label}' is a command, not a submenu.")
            if not current.is_enabled():
                raise RuntimeError(f"Menu item '{label}' is disabled right now.")
            try:
                current.invoke()
            except Exception:
                current.click_input()
            opened = []  # invoking closes the menu chain
            time.sleep(0.4)
            return {"invoked": path}
        items = [{"name": k.window_text(), "automation_id": k.element_info.automation_id or None,
                  "enabled": k.is_enabled(), "has_submenu": not _is_leaf(k)} for k in _menu_items(current)]
        return {"menu": path, "items": items}
    finally:
        _close_menus(w, opened)


def _close_menus(w, opened: list) -> None:
    from pywinauto import keyboard

    for m in reversed(opened):
        try:
            m.collapse()
        except Exception:
            pass
    time.sleep(0.2)
    pid = _studio_pid()
    if opened and pid and any(not t for _, t in _pid_hwnds(pid)):
        # popup still showing - fall back to Esc presses
        _focus(w)
        for _ in opened:
            keyboard.send_keys("{ESC}")


def _menu_items(menu_item) -> list:
    items = [k for k in _find_all(menu_item, control_type="MenuItem", scope="children") if k.window_text()]
    if not items:
        items = [k for k in _find_all(menu_item, control_type="MenuItem") if k.window_text()]
    return items


def _is_leaf(menu_item) -> bool:
    try:
        return menu_item.get_expand_state() == 3  # ExpandCollapseState_LeafNode
    except Exception:
        return True  # items without the ExpandCollapse pattern are commands


_KEY_MAP = {
    "OemComma": ",", "OemPeriod": ".", "OemPlus": "{+}", "OemMinus": "{-}", "Oem1": ";", "OemOpenBrackets": "[",
    "Oem6": "]", "Oem5": "\\", "OemQuestion": "/", "OemQuotes": "'", "Oem7": "'", "OemTilde": "`", "Back": "{BACKSPACE}",
    "Delete": "{DELETE}", "Return": "{ENTER}", "Enter": "{ENTER}", "Escape": "{ESC}", "Space": "{SPACE}", "Tab": "{TAB}",
    "Home": "{HOME}", "End": "{END}", "Left": "{LEFT}", "Right": "{RIGHT}", "Up": "{UP}", "Down": "{DOWN}",
    "PageUp": "{PGUP}", "PageDown": "{PGDN}", "Insert": "{INSERT}",
}
_BUILTIN_SHORTCUTS = {
    "Save": "^s", "SaveAs": "^+s", "Open": "^o", "NewProject": "^n", "Undo": "^z", "Redo": "^y", "Cut": "^x",
    "Copy": "^c", "Paste": "^v", "SelectAll": "^a", "Delete": "{DELETE}", "PlayPause": "{SPACE}",
}


def _to_send_keys(key: str, modifiers: str) -> Optional[str]:
    if not key or key == "None":
        return None
    if key in _KEY_MAP:
        k = _KEY_MAP[key]
    elif len(key) == 2 and key[0] == "D" and key[1].isdigit():
        k = key[1]
    elif len(key) == 1:
        k = key.lower()
    elif key.startswith("F") and key[1:].isdigit():
        k = "{" + key + "}"
    elif key.startswith("NumPad") and key[6:].isdigit():
        k = "{VK_NUMPAD" + key[6:] + "}"
    else:
        k = "{" + key.upper() + "}"
    pre = ""
    for m in [x.strip() for x in (modifiers or "").split(",")]:
        pre += {"Control": "^", "Shift": "+", "Alt": "%"}.get(m, "")
    return pre + k


def _load_shortcuts() -> dict:
    out = dict(_BUILTIN_SHORTCUTS)
    f = _shortcuts_file()
    if f:
        try:
            for s in json.loads(f.read_text(encoding="utf-8-sig")).get("Shortcuts", []):
                ks = _to_send_keys(s.get("Key"), s.get("Modifiers"))
                if ks:
                    out[s["ID"]] = ks
        except Exception:
            pass
    return out


@mcp.tool()
def camtasia_list_shortcuts() -> dict:
    """List Camtasia command IDs usable with camtasia_run_shortcut, read from your own KeyboardShortcuts.json
    (so customised shortcuts are respected) plus standard ones (Save, Undo, Redo, PlayPause...)."""
    return {"shortcuts": _load_shortcuts()}


@mcp.tool()
def camtasia_run_shortcut(command_id: str) -> dict:
    """Run a Camtasia command by its shortcut ID, e.g. Save, Undo, PlayPause, Split, AddMarker, ImportMedia,
    ExportLocal, ExportFrameAs, LaunchRecorder, TimelineZoomToFit, JumpToTimelineBeginning, Duplicate, Group.
    The editor window is focused first. See camtasia_list_shortcuts for all IDs."""
    from pywinauto import keyboard

    sc = _load_shortcuts()
    keys = sc.get(command_id) or next((v for k, v in sc.items() if k.lower() == command_id.lower()), None)
    if not keys:
        raise ValueError(f"Unknown command '{command_id}'. Call camtasia_list_shortcuts for valid IDs.")
    _focus(_main_window())
    keyboard.send_keys(keys)
    time.sleep(0.3)
    return {"command": command_id, "sent": keys}


@mcp.tool()
def camtasia_send_keys(keys: str, focus_editor: bool = True) -> dict:
    """Send raw keystrokes (pywinauto syntax: ^=Ctrl, +=Shift, %=Alt, {ENTER}, {TAB}, {ESC}, {F9}, {SPACE}...).
    Literal text: wrap special chars in braces, e.g. '{+}'. Focuses the Camtasia editor first by default."""
    from pywinauto import keyboard

    if focus_editor:
        _focus(_main_window())
    keyboard.send_keys(keys, with_spaces=True, pause=0.02)
    return {"sent": keys}


@mcp.tool()
def camtasia_screenshot(max_width: int = 1600, window_title: Optional[str] = None, full_screen: bool = False) -> Image:
    """Screenshot of the Camtasia editor (restored and brought to front), another Camtasia window (window_title,
    e.g. a dialog or the detached canvas) or the full virtual screen."""
    from PIL import ImageGrab

    if full_screen:
        img = ImageGrab.grab(all_screens=True)
    else:
        w = _main_window()
        if window_title:
            w = next((x for x in _top_windows() if window_title.lower() in (x.window_text() or "").lower()), None)
            if w is None:
                raise ValueError(f"No Camtasia window titled like '{window_title}'")
        _focus(w)
        time.sleep(0.3)
        r = w.rectangle()
        img = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom), all_screens=True)
    if img.width > max_width:
        img = img.resize((max_width, int(img.height * max_width / img.width)))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    return Image(data=buf.getvalue(), format="png")


if __name__ == "__main__":
    mcp.run()
