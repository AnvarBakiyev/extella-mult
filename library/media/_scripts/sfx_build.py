import json, re, os, subprocess, sys
S=sys.argv[1]; OUT=sys.argv[2]; os.makedirs(OUT,exist_ok=True)
cat=json.load(open(S+"/sfx_cat.json")); root=S+"/dl/oga_sfx"
R=[ # category, slug, filename regex, n, max seconds, what
("whoosh","swishes-sound-pack",r"swish-(1|3|5|8|10|12)\.",6,3,"swish / whoosh"),
("whoosh","18-random-video-game-sound-effects",r"whoosh",2,3,"whoosh"),
("whoosh","wind-whoosh-loop",r".",1,6,"wind whoosh"),
("pop","pop-sounds",r"pop(2|3|8|10)\.",4,2,"pop"),
("pop","balloon-sounds",r"balloon_pop\.",1,2,"balloon pop"),
("pop","100-cc0-sfx",r"plop_0[12]",2,2,"plop"),
("pop","bubbles-pop",r".",1,3,"bubbles pop"),
("boing","boing",r".",1,4,"boing"),("boing","18-random-video-game-sound-effects",r"boing",1,4,"boing"),
("boing","100-cc0-sfx",r"spring_0[1236]",4,2,"spring boing"),("boing","boings",r".",3,2,"cartoon bing/bung"),
("boing","various-sound-effects-0",r"snd_sproing",1,2,"sproing"),
("slip","various-sound-effects-0",r"snd_slip_on_ice|fall_0|uff",3,3,"slip / fall / oof"),
("slip","nhfea-sound",r"as_h_trip|as_h_fall",2,3,"trip / fall"),
("cartoon","silly-sound-effects",r"bloop|blung|plup|booleh",4,2,"silly mouth sound"),
("cartoon","27-metal-audio-samples-sfx",r"wobble_0[1-3]",3,2,"metal wobble"),
("cartoon","propeller-cartoon-loop",r"\.ogg$",1,3,"cartoon propeller loop"),
("cartoon","58-random-sound-effects",r"Squeek_01|Finger_Click_02|Tongue_Click",3,2,"squeak / finger snap / tongue click"),
("laugh","group-giggling",r".",1,8,"group giggling"),
("laugh","do-you-remember-laughter",r".",1,26,"crowd laughter"),
("laugh","evil-laugh",r".",1,4,"evil laugh"),("laugh","witch-cackle",r".",1,5,"witch cackle"),
("applause","applause-in-a-large-hall-or-church",r".",1,20,"applause in hall (trimmed to 20 s)"),
("applause","fireworks-with-applause-happy-people",r".",1,20,"applause with fireworks (first 20 s)"),
("applause","58-random-sound-effects",r"Hand_Clap_03",1,2,"single hand clap"),
("crickets","crickets-ambient-noise-loopable",r".",1,12,"crickets loop"),
("crickets","random-sounds-samples",r"cricket",1,13,"crickets ambience"),
("cash","202-more-sound-effects",r"Money_0[1-3]",3,3,"money / cash handling"),
("cash","58-random-sound-effects",r"Coins_0[124]",3,2,"coins"),
("cash","54-casino-sound-effects-cards-dice-chips",r"chips-stack-[1-2]\.|chip-lay-1\.",3,2,"casino chips"),
("typewriter","typewriter-sounds",r"typewriter[1-8]\.",8,2,"typewriter key/carriage"),
("keyboard","keyboard-soundpack-1-typing-and-single-keystrokes",r"typing|keypress-00[1-3]",6,10,"computer keyboard typing / keystroke"),
("click","mouse-click",r".",1,2,"mouse click"),("click","middle-mouse-click",r".",1,2,"middle mouse click"),
("click","interface-sounds",r"click_00[1-4]|switch_00[1-2]",5,2,"UI click / switch (Kenney)"),
("click","51-ui-sound-effects-buttons-switches-and-clicks",r"click[1-3]\.|switch[1-3]\.",4,2,"button click / switch (Kenney)"),
("phone","crank-movie-telephone-ringtone",r".",1,8,"old telephone ring"),
("phone","modern-ringtone-chirptone",r".",1,3,"modern ringtone"),
("phone","202-more-sound-effects",r"Phone[123]",3,11,"phone sound"),
("phone","doorbell-ring",r".",1,5,"doorbell ring"),
("notification","ui-sound-effects-button-clicks-user-feedback-notifications",r"Ding|chimes|ding_deep|negative_sound\.|alarm\.",5,3,"notification ding / chime / error"),
("notification","interface-sounds",r"confirmation_00[1-3]|error_00[1-2]|maximize_001|minimize_001",6,2,"notification / confirm / error (Kenney)"),
("notification","space-sound-effects",r"message1",1,2,"message blip"),
("door","various-sound-effects",r"door_creak_open|door_creak_close|door_open|door_close|drawer_open",5,3,"door / drawer"),
("door","100-cc0-sfx",r"door_0[12]|slam_0[12]",4,3,"door open-close / slam"),
("door","202-more-sound-effects",r"Key_Lock_Door_0[1-2]",2,3,"key in lock"),
("footsteps","100-cc0-sfx-2",r"footstep_wood_0[1-2]|footstep_wet_01|footstep_0[12]",5,2,"footstep (wood / wet / plain)"),
("footsteps","random-sounds-samples",r"full",1,6,"footsteps walking sequence"),
("footsteps","footsteps-leather-cloth-armor",r"step_cloth[12]\.",2,2,"cloth footstep"),
("footsteps","various-sound-effects",r"floor_creak1",1,3,"floor creak"),
("splash","40-cc0-water-splash-slime-sfx",r"splash_(06|09|10|14)\.",4,2,"water splash"),
("splash","100-cc0-sfx",r"splash_0[12]",2,2,"splash"),
("water","40-cc0-water-splash-slime-sfx",r"loop_water_0[13]",2,5,"water loop"),
("water","various-sound-effects",r"tap_water|toilet_flush",2,5,"tap water / toilet flush"),
("water","water-waves",r"wave_0[24]",2,4,"water wave"),("water","beach-ocean-waves",r"wave_01",1,4,"beach wave"),
("water","dripping-water-loop",r".",1,10,"dripping water loop"),("water","202-more-sound-effects",r"Drink_0[15]",2,3,"drink / gulp"),
("wind","wind",r"Wind\.|Wind2",2,7,"wind gust"),("wind","wind1",r"wind1\.|wind3\.",2,20,"wind ambience (first 20 s)"),
("wind","random-sfx",r"Hollow Wind",1,11,"hollow wind"),
("rain","rain-loopable",r"/1\.ogg$|/3\.ogg$",2,30,"rain loop (30 s)"),
("rain","rain-gutter-loop",r".",1,30,"rain gutter (30 s)"),
("rain","40-cc0-water-splash-slime-sfx",r"loop_rain",1,7,"short rain loop"),
("thunder","rain-long-thunder",r".",1,30,"rain with long thunder (30 s)"),
("thunder","100-cc0-sfx-2",r"thunder_01",1,6,"thunder clap"),
("birds","ambient-bird-sounds",r".",1,30,"bird ambience"),
("birds","bird-chirping-sounds",r"\.wav$",1,3,"bird chirps"),
("birds","sound-effects-for-oh-gully",r"synth%20seagull",1,4,"seagull"),
("forest","random-sounds-samples",r"moving%20leaves",1,2,"rustling leaves"),
("forest","various-sound-effects-0",r"rustling_of_the_weeds",1,2,"rustling grass"),
("forest","random-sounds-samples",r"dog%20barking",1,9,"distant dog barking"),
("city","high-traffic-road-sounds",r".",1,30,"busy road traffic (30 s)"),
("city","100-cc0-sfx-2",r"loop_highway|loop_construction_site",2,17,"highway / construction site loop"),
("city","car-sound-effects-pack-low-quality",r"Car_Horn|Car_Door_Open",2,2,"car horn / car door"),
("city","car-engine-start-01",r".",1,4,"car engine start"),
("office","the-shop",r"^((?!LEGIT).)*drone\.",1,12,"shop / fridge hum room tone"),
("office","30-cc0-sfx-loops",r"ambient_0[13]|machine_08",3,9,"indoor ambient / machine hum loop"),
("office","100-cc0-sfx-2",r"loop_ambient_0[14]|loop_machine_02",3,11,"ambient room / machine loop"),
("office","various-sound-effects",r"microwave|switch_on",2,5,"microwave / light switch"),
("office","58-random-sound-effects",r"Paper_Crunch_01|Scissors_Snip_02|Spoon_On_Cup_01",3,2,"paper crunch / scissors / spoon on cup"),
("static","frequency-static-sound-effects",r"static1",1,10,"radio/TV static (10 s)"),
("static","static",r".",1,10,"static"),("static","miscmenu-sci-fi-sounds",r"walkie",1,2,"walkie-talkie static"),
("glitch","interface-sounds",r"glitch_00[1-4]",4,2,"digital glitch (Kenney)"),
("glitch","50-cc0-sci-fi-sfx",r"weird_0[24]|terminal_0[12]",4,3,"sci-fi glitch / terminal"),
("bell","100-cc0-sfx",r"bell_0[1-3]",3,3,"bell"),("bell","pleasing-bell-sound-effect",r".",1,2,"pleasing bell"),
("bell","bicycle-sounds",r"rotating_bicycle_bell-1\.ogg",1,2,"bicycle bell"),("bell","point-bell",r".",1,3,"point bell"),
("bell","bell-arpeggio-24",r".",1,4,"bell arpeggio"),
("gong","100-cc0-sfx",r"gong_0[12]",2,3,"gong"),
("horn","bicycle-horn",r".",1,2,"bicycle horn"),("horn","their-coming-generic-horn-sound",r"\.ogg$|\.wav$",1,6,"war horn"),
("siren","sirens-and-alarm-noise",r".",1,15,"siren (15 s)"),("siren","alarm-2",r".",1,3,"alarm"),
("siren","30-cc0-sfx-loops",r"alarm_0[13]",2,3,"alarm loop"),
("explosion","synthesized-explosion",r".",1,4,"synth explosion"),("explosion","100-cc0-sfx",r"explosion",1,2,"explosion"),
("explosion","various-sound-effects-0",r"dull_explosion",1,4,"dull explosion"),("explosion","50-cc0-retro-synth-sfx",r"retro_explosion_0[15]",2,2,"retro explosion"),
("explosion","battle-at-sea",r"cannon_fire_1",1,4,"cannon fire"),
("fire","fire-crackling",r"fire-1\.",1,4,"fire crackle"),("fire","fireplace-sound-loop",r".",1,30,"fireplace loop"),
("fire","58-random-sound-effects",r"Cigarette_Lighter_01",1,1,"lighter"),("fire","various-sound-effects",r"match",1,2,"match strike"),
("rocket","50-cc0-sci-fi-sfx",r"rocket_01|teleport_02",2,3,"rocket launch / takeoff"),
("rocket","space-sound-effects",r"warpout",1,5,"warp out"),
("magic","magic-spell-sfx",r"magical_[1-5]",5,3,"magic sparkle / spell"),
("magic","freeze-spell-0",r".",1,3,"freeze spell sparkle"),("magic","80-cc0-rpg-sfx",r"item_gem_0[14]",2,2,"gem sparkle"),
("camera","202-more-sound-effects",r"Camera_0[1-3]",3,3,"camera shutter"),("camera","camerashudder",r".",1,2,"camera shutter"),
("camera","camera",r".",1,3,"camera"),
]
picked=[]; used=set()
for catg,slug,rx,n,mx,what in R:
    cands=[x for x in cat if x['slug']==slug and re.search(rx,x['path']) and x['dur']>0 and x['path'] not in used]
    # dedupe same basename stem differing only by ext; prefer ogg/wav/flac over mp3
    seen={}
    for x in sorted(cands,key=lambda x:(x['path'].endswith('.mp3'),x['path'])):
        stem=re.sub(r'(_0)?\.(ogg|wav|mp3|flac)$','',x['path'].split('/')[-1])
        if stem not in seen: seen[stem]=x
    for x in list(seen.values())[:n]:
        used.add(x['path']); picked.append((catg,x,mx,what))
print(len(picked))
meta=[]; cnt={}
for catg,x,mx,what in picked:
    cnt[catg]=cnt.get(catg,0)+1
    name=f"{catg}_{cnt[catg]:02d}.ogg"; src=os.path.join(root,x['path']); dst=os.path.join(OUT,name)
    # pass 1: trim silence (start + end), cap length, resample, stereo kept
    flt=f"silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.02,areverse,silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.05,areverse,atrim=0:{mx},afade=t=out:st={max(0,mx-0.3)}:d=0.3,aresample=44100"
    tmp=dst+".tmp.wav"
    subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-af",flt,"-ar","44100",tmp],check=True)
    r=subprocess.run(["ffmpeg","-hide_banner","-i",tmp,"-af","volumedetect","-f","null","-"],capture_output=True,text=True).stderr
    mxv=float(re.search(r"max_volume: (-?[\d.]+) dB",r).group(1)); g=-1.0-mxv
    subprocess.run(["ffmpeg","-v","error","-y","-i",tmp,"-af",f"volume={g}dB,alimiter=limit=0.891:level=false:attack=1:release=20","-c:a","libvorbis","-q:a","5","-ar","44100",dst],check=True)
    os.remove(tmp)
    d=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",dst],capture_output=True,text=True).stdout)
    m=json.load(open(os.path.join(root,x['slug'],"meta.json")))
    meta.append(dict(file=name,what=f"{what} — {d:.1f}s; orig file {x['path'].split('/')[-1]}",source=m['url'],licence="CC0 1.0",author=m['author'],title=m['title']))
json.dump(meta,open(S+"/meta/sfx.json","w"),indent=1); print("done",len(meta),cnt)
