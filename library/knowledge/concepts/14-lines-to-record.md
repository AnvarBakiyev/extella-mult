# PUPPET: LINES_TO_RECORD
tags: LINES_TO_RECORD, recording, voice, elevenlabs, stop
If check returns LINES_TO_RECORD, the program is valid but some lines have no recording yet and the device has no voice key.
Do this:
1. Stop. Do not render. Do not change the program.
2. Show the person the list as a short table: line number, voice (who), text, file path.
3. Say: record these lines with your own voice service, put each file at the given path, then ask me to render.
4. When the person says the files are in place, run check again. Then render once.
Do not rewrite lines to avoid recording. Do not drop lines. Do not retry check in a loop.
After recording, check may report real lengths ("the recordings do not fit"). Then re-time the shots (see "PUPPET: fixing check errors") without changing a single word, so the same recordings are reused.
