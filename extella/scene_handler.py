"""The cspl=scene handler: an Extella expert with cspl=scene passes its code (a SCENE program) here."""

def scene(code = "", filtered_source_code = "", func_name = "", **extra):
    import os, re, time, uuid, subprocess
    params = dict(extra)
    if isinstance(extra.get("kwargs"), dict):
        params.update(extra["kwargs"])
    home = os.path.expanduser("~/extella-mult")
    import json
    try:
        py = json.load(open(os.path.join(home, "config.json"))).get("python") or "python3"
    except Exception:
        py = "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12"
    if not os.path.isdir(os.path.join(home, "handler")):
        return {"status": "error", "error": "the scene language is not installed on this device (~/extella-mult)"}
    out = os.path.join(home, "out")
    os.makedirs(out, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONNOUSERSITE", "PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")}
    mode = str(params.get("mode") or "check")
    if mode == "status":
        job = str(params.get("job") or "")
        log = os.path.join(out, job + ".log")
        if not job or not os.path.exists(log):
            return {"status": "error", "error": "status needs job=<id> from mode=render"}
        text = open(log, encoding="utf-8", errors="replace").read()
        mp4 = os.path.join(out, job + ".mp4")
        if "wrote " in text and os.path.exists(mp4):
            return {"status": "done", "job": job, "video": mp4, "size_mb": round(os.path.getsize(mp4) / 1e6, 1)}
        if "Traceback" in text or "ERROR" in text:
            return {"status": "failed", "job": job, "error": text[-800:]}
        return {"status": "running", "job": job, "last": text.strip().splitlines()[-1:] }
    source = code or filtered_source_code or ""
    # {{placeholders}} from kwargs, as godot_script does; an unfilled one is an error, not an empty string
    def fill(m):
        k = m.group(1)
        return str(params[k]) if k in params else m.group(0)
    program = re.sub(r"\{\{(\w+)\}\}", fill, source)
    left = sorted(set(re.findall(r"\{\{(\w+)\}\}", program)))
    lines = len([l for l in program.splitlines() if l.strip() and not l.strip().startswith("#")])
    if left:
        return {"status": "rejected", "errors": "fill the template values: " + ", ".join(left), "lines": lines, "film": func_name}
    if not program.strip():
        return {"status": "rejected", "errors": "the film program is empty", "film": func_name}
    jid = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    path = os.path.join(out, jid + ".scene")
    open(path, "w", encoding="utf-8").write(program)
    chk = subprocess.run([py, "-m", "handler.main", path, "--check"], cwd=home, env=env, capture_output=True, text=True, timeout=120)
    msg = (chk.stderr or "").strip()
    if chk.returncode != 0:
        return {"status": "rejected", "errors": msg.replace("ERROR: ", ""), "lines": lines, "film": func_name}
    if mode == "check":
        return {"status": "ok", "summary": msg.replace("ok: ", ""), "lines": lines, "film": func_name, "handler_version": 1}
    if mode != "render":
        return {"status": "error", "error": "mode must be check, render or status"}
    log = open(os.path.join(out, jid + ".log"), "w")
    subprocess.Popen([py, "-m", "handler.main", path, "--out", os.path.join(out, jid + ".mp4"), "--procs", "6"],
                     cwd=home, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    return {"status": "started", "job": jid, "film": func_name, "summary": msg.replace("ok: ", ""), "lines": lines,
            "next": "the video will be at ~/extella-mult/out/" + jid + ".mp4; check with mode=status job=" + jid + " only if the user asks"}
