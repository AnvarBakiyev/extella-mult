# PUPPET: statements
tags: language, syntax, statements, film, shot, say, voice
One statement per line. # starts a comment. Times end with s. Only these statements exist:
film title="Название" style=puppet fps=24 size=1920x1080   (always the first line)
shot 0-4.6s: ch_dina push=0.05 focus=0.5,0.4   (which set is on screen, camera after the set)
say ch_dina "Реплика." at 0.3s   (on-screen line; the set's mouth moves; voice comes from the set)
voice "[deep] Закадровый текст." at 5s   (off-screen line; [deep] narrator, [ad] commercial voice)
text "НАДПИСЬ" at 0.5,0.18 size=0.07 color=#ffffff glow=#000000 2-6s
prop coffee_cup at 0.7,0.8 size=0.15 bob=0.01 12-18s   (only prop names from the catalog)
music mood=bright tempo=118 35-43s
fade in 0-0.6s   /   fade out 46.6-47s
Rules: the first shot starts at 0s. Shots touch: each starts exactly where the previous ends. All at= and ranges are film seconds, not shot seconds. Every say/text/fade lies inside the film. Words go in double quotes; inside them use «ёлочки», never ".
