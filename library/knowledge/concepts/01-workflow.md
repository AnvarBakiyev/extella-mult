# PUPPET: how to work
tags: workflow, order, start
1. Read the request. Pick ONE format (F01-F25) that fits; search "PUPPET format Fxx" for its beats.
2. Pick 2-3 characters (ch_ codes) and 1-2 places (pl_ codes). Use only names from the catalog.
3. Write the joke first, in Russian, as 8-12 short lines. Decide the last line before anything else.
4. Lay the lines on the format beats. One line per shot. 35-55 s total.
5. Compute times: line length = words/2 s + 0.5 s per [pause]; shot = 0.3 s lead + line + 0.4 s tail.
6. Add camera per beat (search "PUPPET camera grammar"), music only where the format needs it, fade in and out.
7. Run check (mode=check). Fix every error by its line number. Never change words to fix timing; move times.
8. If check returns LINES_TO_RECORD, stop and show the list. Do not render.
9. Render once. Do not poll status.
Output only the program, 25-45 lines. Start with 3 comments: # format: F01 Интервью / # logline: ... / # why it works: ...
