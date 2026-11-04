# PUPPET, felt puppet films

A film is a text program, one statement per line, `#` starts a comment. The first line picks the look: `film title="..." style=puppet fps=24 size=1920x1080 [voices=off] [look=warm|none]`.

Two kinds of picture:

- **picture sets** (the PREMIUM pack): a generated still of one character or place, a whole shot each. A talking set has a few stills of the same frame (mouth closed, half open, open, eyes closed); only the region that differs is pasted in with a soft mask, so the picture never flickers. The mouth follows the loudness of the voice. A set is used directly as the shot and never gets a `cast` line.
- **code-built shots** (the CORE pack): a layered felt plate with one or more code-built characters cast on it. Layers move at their own parallax speed with the camera; the speaker's mouth follows Russian visemes laid over the recording, or over a synthetic envelope when there is none.

```
film title="Лосось" style=puppet fps=24 size=1920x1080 [voices=off]
shot 0-6s: <set | plate | stage> push=0.05 pan=right focus=0.5,0.4 handheld=1 snap=2.3
cast <char> on <plate> at x,y [size=0.62] [facing=left|right] [mood=neutral] [as=<stage>]
cast <char> on <plate> at x,y body=full [size=0.7] ...      the whole puppet; x,y is where its feet stand
act <char> <move> A-Bs [to=x]                                walk, run, wave, point, shrug, jump, dance, sit, nod, ...
act <char> holding <prop> A-Bs  |  prop <name> in=<char>.hand  a prop in the hand
say <set | char> "реплика" at 0.4s [who=voice] [mood=neutral|happy|angry|shocked] [file=recording.mp3]
voice "реплика" at 12s [who=deep] [file=...]                 off screen
text "РЕКЛАМА" at 0.5,0.15 size=0.1 color=#ffffff [font=ptsans|oswald|caveat] [halo=0.8] 30-33s
prop <name> at x,y size=0.15 [bob=0.01] 12-18s
fx <effect> 2-6s [at x,y] [opacity=1]
sfx <name> at 3.2s [gain=1]
music mood=tense key=D tempo=80 [A-Bs]  |  music file=<name> [A-Bs] [gain=0.5]
cut wipe|iris|dissolve|whip|dip|dip_white|page|slide at Xs [dur=0.6] [dir=left|right]
fade in 0-0.6s  |  fade out 50-51s
```

Rules the checker enforces, in words: shots touch each other; one time range per line (fade, act and text go on lines of their own); a character that speaks must be cast on the plate of the shot; full bodies keep at least 0.12 of the frame apart; a picture set that is both a set and a code character (oil_barrel) is the set unless it was cast.

Voices: with an ElevenLabs key in `~/extella-mult/config.json` the handler records `say` and `voice` lines itself; without it the check lists the lines to record (LINES_TO_RECORD) and `file=` attaches a recording; `voices=off` makes a film with subtitles instead.

Check and render:

```
python3 -m handler.main film.scene --check
python3 -m handler.main film.scene --out film.mp4
```
