# PUPPET: camera parameters of shot
tags: camera, push, pull, snap, pan, dutch, whip, handheld, shake, focus
push=0.05   slow push in over the whole shot. 0.02 near-still, 0.04-0.06 slow, 0.1 clear, 0.14-0.16 strong. Default 0.04 if you write nothing.
pull=0.25   starts close, pulls back to the whole frame. Reveals. Do not combine with push.
focus=0.5,0.4   point the push moves to (x,y 0..1). Put it on the face.
pan=right   slow drift; left|right|up|down. Adds a small zoom. For landscapes, maps, rows of things.
snap=44.3   crash zoom at that FILM second (must lie inside the shot). Put it on the reaction or at the start of the last line.
handheld=1   uneven wander, like a news or reality camera.
dutch=10   tilted horizon in degrees (8-12, sign gives side). Unease, problems, lies.
whip=left   the shot flies in from the side, 0.35 s. Fast cut between people or a new arrival.
shake=0.003   trembling. Impact, wind, panic. Keep 0.002-0.004.
Combine at most two moves per shot. Never use push above 0.3.
