import json, re, os, subprocess, sys
S=sys.argv[1]; OUT=sys.argv[2]; os.makedirs(OUT,exist_ok=True)
cat=json.load(open(S+"/music_cat.json")); root=S+"/dl/oga_music"
R=[ # name, slug, regex, max seconds, what
("stinger_epic_hit_01","85-short-music-jingles",r"HIT00",20,"epic orchestral hit jingle (Kenney)"),
("stinger_epic_hit_02","85-short-music-jingles",r"HIT05",20,"epic hit jingle (Kenney)"),
("stinger_epic_hit_03","85-short-music-jingles",r"HIT12",20,"epic hit jingle (Kenney)"),
("jingle_lounge_sax_01","85-short-music-jingles",r"SAX00",20,"sax jingle — lounge/comedy (Kenney)"),
("jingle_lounge_sax_02","85-short-music-jingles",r"SAX04",20,"sax jingle (Kenney)"),
("jingle_lounge_sax_03","85-short-music-jingles",r"SAX10",20,"sax jingle (Kenney)"),
("jingle_comedy_pizzicato_01","85-short-music-jingles",r"PIZZA01",20,"pizzicato comedy jingle (Kenney)"),
("jingle_comedy_pizzicato_02","85-short-music-jingles",r"PIZZA06",20,"pizzicato comedy jingle (Kenney)"),
("jingle_comedy_pizzicato_03","85-short-music-jingles",r"PIZZA12",20,"pizzicato comedy jingle (Kenney)"),
("jingle_happy_steeldrum_01","85-short-music-jingles",r"STEEL00",20,"steel-drum happy jingle (Kenney)"),
("jingle_happy_steeldrum_02","85-short-music-jingles",r"STEEL07",20,"steel-drum jingle (Kenney)"),
("jingle_gameshow_chip_01","85-short-music-jingles",r"NES00",20,"8-bit game-show jingle (Kenney)"),
("jingle_gameshow_chip_02","85-short-music-jingles",r"NES08",20,"8-bit jingle (Kenney)"),
("news_intro_dramatic_01","opening-theme-actionsuspense",r"opening_theme\.wav",30,"dramatic opening theme, excerpt — usable as news/doc intro"),
("news_intro_dramatic_02","prologue-theme",r"\.ogg$",30,"prologue theme, excerpt — usable as news intro"),
("commercial_jingle_icecream","ice-cream-truck-theme",r"Lead Intro",16,"ice-cream-truck style lead intro — commercial jingle"),
("commercial_jingle_shop","shop-theme",r"Radio Edit\)\.ogg",30,"cheerful shop theme 'Buy Something!', excerpt — commercial bed"),
("commercial_jingle_clear","sci-fi-puzzle-jingle-result",r"Clear \(Jingle\)",8,"short 'success' jingle"),
("gameshow_win","the-war-over-a-melon-field-themes-and-jingles",r"win_1",14,"game-show win jingle"),
("gameshow_lose","the-war-over-a-melon-field-themes-and-jingles",r"lose_3",24,"game-show lose jingle"),
("gameshow_select","the-war-over-a-melon-field-themes-and-jingles",r"charselect_2",15,"game-show contestant select loop"),
("gameshow_upbeat","free-nes-music-pack",r"nes_19-upbeat",45,"upbeat chiptune game-show bed"),
("gameshow_cheery","free-nes-music-pack",r"nes_03-cheery",45,"cheery chiptune"),
("gameshow_fail","sci-fi-puzzle-jingle-result",r"Failure \(Jingle\)",8,"'wrong answer' jingle"),
("suspense_streets","night-of-the-streets-horrorsuspense",r".",40,"horror/suspense, excerpt"),
("suspense_dark_stinger","dark-stinger-1",r"\.ogg$",20,"dark suspense stinger"),
("suspense_pressure","bumblebee-loop",r"Bumblebee%20loop",40,"tension loop, excerpt"),
("suspense_sirens","sirens-in-darkness",r".",40,"dark tension, excerpt"),
("doc_drone_downfall","downfall",r"\.flac$",45,"dark documentary drone, excerpt"),
("doc_drone_space","background-space-track",r".",45,"ambient space drone, excerpt"),
("doc_drone_searching","searching",r".",45,"searching ambient drone, excerpt"),
("doc_drone_postapoc","horror-atmosphere",r".",45,"post-apocalyptic atmosphere drone, excerpt"),
("comedy_tuba","midi-pack-2-27-new-tunes",r"tubamuck",30,"tuba-led comedic MIDI tune, excerpt"),
("comedy_clumsy","8-bit-i-am-not-clumsy",r".",39,"clumsy comedic chiptune"),
("comedy_mustard","which-brand-of-mustard-shall-i-buy",r".",40,"quirky comedic tune, excerpt"),
("comedy_two_left_socks","two-left-socks",r".",40,"quirky comedic tune, excerpt"),
("ukulele_begin","ukulele-forest-beginning-loop-and-end",r"forest_beginning",8,"ukulele intro"),
("ukulele_loop","ukulele-forest-beginning-loop-and-end",r"forest_loop",10,"ukulele loop (seamless)"),
("ukulele_end","ukulele-forest-beginning-loop-and-end",r"forest_end",5,"ukulele ending"),
("ukulele_bleu","bleu",r".",40,"Komiku 'Bleu' — light acoustic, excerpt"),
("whistling_bright_eyes","bright-eyes",r".",45,"whistle-like lead melody, excerpt"),
("whistling_blues","blues-0",r".",40,"bluesy whistle-ish melody, excerpt"),
("lounge_bossa","bossa-nova",r".",45,"8-bit bossa nova lounge, excerpt"),
("lounge_elevator_01","elevator-music",r".",45,"elevator music, excerpt"),
("lounge_elevator_02","somewhere-in-the-elevator",r".",45,"elevator lounge, excerpt"),
("lounge_mirror_lake","mirror-lake",r".",45,"calm jazz, excerpt"),
("lofi_hiphop","lofi-hip-hop",r".",45,"lo-fi hip hop loop, excerpt"),
("lofi_chill","chill-lofi-inspired",r"\.ogg$",45,"chill lo-fi, excerpt"),
("lofi_cup_of_tea","lofi-compilation",r"A%20cup",45,"lo-fi 'A cup of tea', excerpt"),
("lofi_cat_caffe","lofi-compilation",r"Cat%20caffe",45,"lo-fi 'Cat caffe', excerpt"),
("epic_fanfare","victory-fanfare-short",r".",12,"short heavy victory fanfare"),
("epic_great_mission","free-music-pack",r"Great mission",40,"epic orchestral 'Great mission', excerpt"),
("epic_battle","battle-theme-a",r".",40,"epic battle theme, excerpt"),
("sad_piano_loop","emotional-piano-loop",r".",28,"emotional piano loop"),
("sad_piano_sadness","sadness",r".",26,"sad piano"),
("sad_piano_snowfall","snowfall",r"Looped",45,"melancholic piano loop, excerpt"),
("sad_piano_vampires","vampires-piano",r"\.wav$",45,"sombre piano, excerpt"),
("happy_ending_town","town-theme-rpg",r".",40,"happy town theme, excerpt"),
("happy_ending_success","success-stinger",r".",17,"success stinger"),
("happy_ending_finish","finish-line-stinger",r".",9,"finish-line stinger"),
("happy_ending_daylight","daylight-stinger",r".",19,"daylight stinger"),
("happy_ending_newtown","new-town-stinger",r".",19,"new-town stinger"),
("happy_ending_victory","victory",r"\.wav$",5,"tiny victory jingle"),
("happy_ending_level","level-complete",r"level_complete_1",34,"level complete jingle"),
("happy_ending_outro","anime-esque-intro-outro-theme",r"Outro ~\.ogg",13,"upbeat outro"),
("intro_upbeat","anime-esque-intro-outro-theme",r"Intro ~\.ogg",12,"upbeat intro"),
("stinger_wild_west","wild-west-stinger-1",r"\.ogg$",19,"wild-west stinger"),
("stinger_forest","bit-forest-stinger",r".",28,"8-bit forest stinger"),
]
meta=[]
for name,slug,rx,mx,what in R:
    c=[x for x in cat if x['slug']==slug and re.search(rx,x['path'])]
    c.sort(key=lambda x:(x['path'].endswith('.mp3'),x['path']))
    if not c: print("MISSING",name); continue
    x=c[0]; src=os.path.join(root,x['path']); dst=os.path.join(OUT,name+".ogg"); tmp=dst+".wav"
    exc = x['dur']>mx+0.5
    fo = f",afade=t=out:st={mx-2.5}:d=2.5" if exc else ""
    flt=f"silenceremove=start_periods=1:start_threshold=-60dB:start_silence=0.02,atrim=0:{mx}{fo},aresample=44100"
    subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-af",flt,"-ar","44100","-ac","2",tmp],check=True)
    r=subprocess.run(["ffmpeg","-hide_banner","-i",tmp,"-af","volumedetect","-f","null","-"],capture_output=True,text=True).stderr
    g=-1.0-float(re.search(r"max_volume: (-?[\d.]+) dB",r).group(1))
    subprocess.run(["ffmpeg","-v","error","-y","-i",tmp,"-af",f"volume={g}dB,alimiter=limit=0.891:level=false","-c:a","libvorbis","-q:a","4",dst],check=True); os.remove(tmp)
    d=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",dst],capture_output=True,text=True).stdout)
    m=json.load(open(os.path.join(root,slug,"meta.json")))
    meta.append(dict(file=name+".ogg",what=f"{what} — {d:.1f}s{' (excerpt of '+str(int(x['dur']))+'s track, fade-out)' if exc else ''}; \"{m['title']}\"",source=m['url'],licence="CC0 1.0",author=m['author']))
    print("ok",name,round(d,1),flush=True)
json.dump(meta,open(S+"/meta/music.json","w"),indent=1); print("done",len(meta))
