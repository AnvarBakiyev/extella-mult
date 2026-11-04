# PUPPET: fixing check errors
tags: check, error, fix, mode=check
Check answers with "line N: ...". Fix only that line, then run check again.
"no set 'x' on this device" -> search the catalog; take a listed name. Never invent a set.
"set x has no talking mouth" -> the set is a place; use voice "..." instead of say, or put the speaker's ch_ set on screen.
"shots must touch" -> make this shot start where the previous ends; shift all later times by the same amount.
"the first shot must start at 0s" -> first shot 0-...s.
"say needs a start time" / "needs its time" -> add at Xs or A-Bs.
"is outside the film" -> move it inside the shots or extend the last shot.
"unknown voice who=" -> use one of: narrator, journalist, lady, calm, fairy, deep, ad, salmon.
"unclosed quote" -> close the quote; replace inner " with «».
"is not a statement" -> only film, shot, say, voice, text, prop, music, fade.
"recordings do not fit" -> keep words; re-time: line at = shot start + 0.3, shot end = line end + 0.4; shift everything after.
Two failed fixes in a row: rewrite that beat shorter.
