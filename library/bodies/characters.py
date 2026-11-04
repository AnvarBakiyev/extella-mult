"""The cast: 120+ named felt puppets built from charlib parts. Each entry is a charlib spec plus name, about, voice."""

CAST = []


def P(name, about, voice, **kw):
    kw.update(name=name, about=about, voice=voice)
    CAST.append(kw)


# ---------------------------------------------------------------- newsroom and office
P('aigul', 'репортёр с микрофоном, всегда в кадре', 'journalist', skin='olive', head='oval', hair='long', hair_col='black',
  eyes='narrow', nose='button', outfit='suit', o1='navy', o3='rust', acc=[('mic', 'tomato'), ('earrings', 'gold')], lashes=True)
P('timur', 'ведущий вечерних новостей', 'narrator', skin='tan', head='square', hair='sidepart', hair_col='black', eyes='narrow',
  nose='long', outfit='suit', o1='charcoal', o3='teal', brow_w=1.2)
P('madina', 'редактор, читает всё дважды', 'calm', skin='light', head='heart', hair='bun', hair_col='espresso', eyes='round',
  nose='button', outfit='shirt', o1='sage', acc=[('glasses', 'cateye', 'burgundy'), 'pencil'], lashes=True)
P('oleg_petrovich', 'главный редактор, начальник', 'deep', skin='porcelain', head='jaw', hair='horseshoe', hair_col='gray',
  age='old', eyes='sleepy', nose='ball', outfit='suit', o1='slate', o3='burgundy', facial='mustache', build='broad')
P('stas_intern', 'стажёр, бегает за кофе', 'ad', skin='light', head='long', hair='spiky', hair_col='ginger', age='young',
  eyes='wide', nose='button', outfit='hoodie', o1='mustard', o2='cream', freckles=True, brow='worried', acc=[('lanyard', 'teal')])
P('zarina', 'ведущая утреннего эфира', 'lady', skin='olive', head='oval', hair='wavy', hair_col='espresso', eyes='round',
  nose='button', outfit='dress', o1='rose', o2='cream', pattern='plain', lashes=True, acc=[('earrings', 'gold')])
P('rustam_camera', 'оператор, молчаливый профи', 'deep', skin='tan', head='wide', hair='buzz', hair_col='black', eyes='narrow',
  nose='wide', outfit='tshirt', o1='charcoal', o2='rust', print='stripe', facial='stubble', acc=[('headphones', 'charcoal')])
P('vera_buhgalter', 'бухгалтер, знает цену всему', 'calm', skin='porcelain', head='egg', hair='bob', hair_col='auburn',
  eyes='sleepy', nose='hooked', outfit='vest', o1='plum', shirt='cream', acc=[('glasses', 'square', 'charcoal')], lashes=True)
P('boss_karimov', 'большой босс, говорит медленно', 'deep', skin='olive', head='potato', hair='horseshoe', hair_col='gray',
  age='old', eyes='narrow', nose='ball', outfit='suit', o1='navy', o3='gold', build='broad', facial='walrus', brow_w=1.4)
P('lena_smm', 'SMM-менеджер, всё снимает на телефон', 'ad', skin='light', head='heart', hair='ponytail', hair_col='blonde',
  age='young', eyes='round', nose='button', outfit='tshirt', o1='pink', o2='white', print='star', lashes=True)
P('daniyar_dev', 'программист, в наушниках с утра', 'calm', skin='tan', head='round', hair='curly', hair_col='black',
  age='young', eyes='sleepy', nose='button', outfit='hoodie', o1='slate', o2='mint', acc=[('headphones', 'mustard', 'charcoal')],
  facial='stubble')
P('hr_imp', 'бес из отдела кадров, улыбается по регламенту', 'odessa', kit='imp', outfit='suit', o1='black', o3='burgundy',
  acc=[('lanyard', 'burgundy')], fangs=True, facial='goatee', hair_col='black', smile=0.2)
P('imp_junior', 'младший бес, носит папки', 'fairy', kit='imp', fur='#7a4f78', age='young', outfit='shirt', o1='lilac',
  hair='tuft', hair_col='plumhair', fangs=True, brow='worried', eyes='round', iris='yellow')
P('nina_secretary', 'секретарь, помнит все дни рождения', 'lady', skin='light', head='oval', hair='bun', hair_col='brown',
  eyes='round', nose='button', outfit='dress', o1='teal', o2='cream', lashes=True, acc=[('necklace', 'cream')])
P('farhod_lawyer', 'юрист, говорит пунктами', 'narrator', skin='tan', head='long', hair='sidepart', hair_col='espresso',
  eyes='narrow', nose='hooked', outfit='suit', o1='charcoal', o3='navy', acc=[('glasses', 'square', 'black')])
P('max_marketing', 'маркетолог, у него всё «вау»', 'ad', skin='porcelain', head='jaw', hair='quiff', hair_col='blonde',
  eyes='wide', nose='long', outfit='vest', o1='teal', acc=[('bowtie', 'mustard')], smile=0.18)
P('auditor_crow', 'аудитор, всё замечает', 'calm', kit='owl', fur='charcoal', fur2='gray', outfit='suit', o1='black',
  o3='slate', acc=[('glasses', 'square', 'silver')], brow='angry')
P('kirill_it', 'админ, перезагружает всё подряд', 'calm', skin='light', head='pear', hair='short', hair_col='brown',
  facial='beard', eyes='sleepy', nose='ball', outfit='tshirt', o1='forest', o2='butter', print='bolt', build='broad')
P('saule_pr', 'пиар-директор, улыбка на миллион', 'lady', skin='olive', head='diamond', hair='long', hair_col='black',
  eyes='narrow', nose='button', outfit='suit', o1='burgundy', tie=False, shirt='cream', lashes=True,
  acc=[('earrings', 'silver')])
P('courier_ali', 'курьер, всегда торопится', 'gogi', skin='tan', head='round', hair='short', hair_col='black', eyes='round',
  nose='hooked', outfit='hoodie', o1='tomato', o2='white', acc=[('hat', 'cap', 'mustard')], facial='mustache')

# ---------------------------------------------------------------- medicine and science
P('doctor_aibek', 'терапевт, спокойный как утро', 'calm', skin='tan', head='oval', hair='short', hair_col='black',
  eyes='narrow', nose='button', outfit='labcoat', acc=['stethoscope'], shirt='sky')
P('doctor_maria', 'хирург, шутит без улыбки', 'narrator', skin='light', head='heart', hair='bob', hair_col='brown',
  eyes='round', nose='long', outfit='labcoat', shirt='mint', acc=['stethoscope', ('glasses', 'round', 'teal')], lashes=True)
P('nurse_gulya', 'медсестра, добрее всех', 'lady', skin='olive', head='round', hair='bun', hair_col='espresso', eyes='round',
  nose='button', outfit='uniform', o1='sky', o3='white', lashes=True)
P('dentist_mouse', 'мышь-стоматолог, любит сыр и пломбы', 'fairy', kit='mouse', outfit='labcoat', shirt='pink',
  acc=[('glasses', 'round', 'charcoal'), 'stethoscope'], buck=True)
P('vet_bear', 'медведь-ветеринар', 'deep', kit='bear', outfit='labcoat', shirt='sage', acc=['stethoscope'])
P('prof_einbaum', 'профессор физики, волосы дыбом', 'narrator', skin='porcelain', head='long', hair='spiky', hair_col='white',
  age='old', eyes='wide', nose='long', outfit='labcoat', shirt='lilac', tie=True, o3='burgundy', facial='walrus', bushy=True)
P('dr_kamila', 'биолог, говорит с микроскопом', 'calm', skin='olive', head='egg', hair='braids', hair_col='black',
  eyes='narrow', nose='button', outfit='labcoat', shirt='cream', acc=[('glasses', 'round', 'gold')], o3='coral')
P('chemist_frog', 'лягушка-химик, всё смешивает', 'ad', kit='frog', outfit='labcoat', shirt='butter',
  acc=[('glasses', 'round', 'charcoal')])
P('lab_robot', 'лабораторный робот, считает вслух', 'calm', kit='robot', outfit='labcoat', shirt='slate', o3='tomato')
P('astronaut_asel', 'космонавт, первая на Луне из аула', 'narrator', skin='olive', head='oval', hair='bun', hair_col='black',
  eyes='narrow', nose='button', outfit='spacesuit', o3='tomato', acc=['helmet'], lashes=True)
P('astronaut_ivan', 'космонавт, скучает по борщу', 'deep', skin='porcelain', head='square', hair='buzz', hair_col='blonde',
  eyes='round', nose='ball', outfit='spacesuit', o3='navy', acc=['helmet'])
P('space_dog', 'собака-космонавт', 'fairy', kit='dog', fur='white', fur2='cream', patch=True, outfit='spacesuit', o3='teal',
  acc=['helmet'])
P('pharmacist_owl', 'сова-фармацевт', 'calm', kit='owl', fur='sand', fur2='cream', outfit='labcoat', shirt='sky',
  acc=[('glasses', 'round', 'gold')])
P('engineer_bolat', 'инженер, всё чинит изолентой', 'deep', skin='tan', head='jaw', hair='short', hair_col='black',
  eyes='narrow', nose='wide', outfit='overalls', o1='slate', o2='mustard', acc=[('hat', 'hardhat', 'mustard')], facial='stubble')
P('archaeologist_hare', 'заяц-археолог', 'narrator', kit='hare', fur='sand', outfit='shirt', o1='khaki',
  acc=[('hat', 'fedora', 'coffee', 'cream')])

# ---------------------------------------------------------------- food and city
P('chef_pig', 'свинья-шеф, всё пробует', 'gogi', kit='pig', outfit='chef', o1='tomato', acc=[('hat', 'toque')])
P('chef_gogi', 'шашлычник Гоги, мастер огня', 'gogi', skin='tan', head='egg', hair='short', hair_col='black', eyes='round',
  nose='hooked', outfit='chef', o1='forest', facial='walrus', bushy=True, build='broad', acc=[('hat', 'toque')])
P('baker_olga', 'пекарь, пахнет корицей', 'lady', skin='porcelain', head='round', hair='kerchief', kerchief='butter',
  kerchief2='rust', eyes='round', nose='ball', outfit='chef', o1='rust', freckles=True)
P('plov_master', 'устабаши, плов на триста человек', 'deep', skin='tan', head='wide', hair='bald', hair_col='black',
  eyes='narrow', nose='wide', outfit='robe', o1='navy', o2='mustard', o3='white', facial='mustache',
  acc=[('hat', 'tubeteika')], age='old', build='broad')
P('waiter_fox', 'лис-официант, вежливый до хитрости', 'odessa', kit='fox', outfit='vest', o1='black',
  acc=[('bowtie', 'burgundy')], smile=0.16)
P('barista_cat', 'кошка-бариста', 'fairy', kit='cat', fur='#e7ddcc', fur2='white', outfit='shirt', o1='coffee',
  acc=[('hat', 'beret', 'black')], lashes=True)
P('taxi_gena', 'таксист Гена, знает всё про всех', 'odessa', skin='light', head='potato', hair='horseshoe', hair_col='brown',
  eyes='sleepy', nose='ball', outfit='shirt', o1='sky', pattern='check', o2='navy', acc=[('hat', 'cap', 'charcoal')],
  facial='mustache', build='broad')
P('taxi_nurlan', 'таксист из Алматы, слушает радио', 'calm', skin='tan', head='square', hair='short', hair_col='black',
  eyes='narrow', nose='long', outfit='vest', o1='charcoal', shirt='white', acc=[('hat', 'cap', 'mustard')], facial='stubble')
P('bus_driver_dog', 'пёс-водитель автобуса', 'deep', kit='dog', fur='coffee', fur2='sand', outfit='uniform', o1='denim',
  o3='silver', acc=[('hat', 'cap', 'navy')])
P('postman_hare', 'заяц-почтальон', 'ad', kit='hare', fur='gray', outfit='uniform', o1='sky', o3='gold',
  acc=[('hat', 'cap', 'navy')], buck=True)
P('policeman_bear', 'медведь-постовой, без погон', 'deep', kit='bear', fur='coffee', outfit='uniform', o1='navy',
  o3='silver', acc=[('hat', 'cap', 'navy')])
P('firefighter_dina', 'пожарная, смеётся громко', 'ad', skin='brown', head='round', hair='ponytail', hair_col='black',
  eyes='round', nose='wide', outfit='uniform', o1='tomato', o3='mustard', acc=[('hat', 'hardhat', 'red')])
P('janitor_sergei', 'дворник, философ двора', 'narrator', skin='light', head='long', hair='bald', age='old', eyes='sleepy',
  nose='long', outfit='overalls', o1='olive', o2='gray', facial='beard', hair_col='gray', acc=[('hat', 'beanie', 'rust')])
P('market_apa', 'апа с рынка, продаёт курут', 'odessa', skin='tan', head='wide', hair='kerchief', kerchief='teal',
  kerchief2='butter', age='old', eyes='narrow', nose='ball', outfit='robe', o1='plum', o2='rose', o3='gold', trim='mustard',
  acc=[('earrings', 'gold')])
P('shopkeeper_salmon', 'лосось из рыбной лавки', 'salmon', kit='salmon', outfit='overalls', o1='denim', o2='white')
P('fishmonger_salmon', 'лосось-рыботорговец, иронизирует', 'salmon', kit='salmon', fur='#c97a6a', outfit='chef',
  o1='teal', acc=[('hat', 'cap', 'teal')])
P('banker_salmon', 'лосось-банкир, плывёт против течения', 'salmon', kit='salmon', fur='#d79a80', outfit='suit',
  o1='charcoal', o3='mustard', acc=[('glasses', 'square', 'gold')])
P('barber_rafik', 'парикмахер Рафик', 'gogi', skin='olive', head='egg', hair='quiff', hair_col='black', eyes='round',
  nose='hooked', outfit='vest', o1='burgundy', shirt='white', facial='mustache')

# ---------------------------------------------------------------- family and village
P('granny_zina', 'бабушка Зина, всё видела', 'odessa', skin='light', age='old', head='egg', hair='kerchief', kerchief='rose',
  eyes='sleepy', nose='ball', outfit='dress', o1='plum', o2='cream', acc=[('necklace', 'coral')])
P('granny_batima', 'әже Батима, рассказчица', 'narrator', skin='tan', age='old', head='wide', hair='kerchief',
  kerchief='white', kerchief2='rose', eyes='narrow', nose='button', outfit='robe', o1='burgundy', o2='gold', o3='forest',
  acc=[('necklace', 'coral'), ('earrings', 'gold')])
P('grandpa_sabit', 'ата Сабит, в калпаке', 'deep', skin='tan', age='old', head='long', hair='bald', hair_col='white',
  eyes='narrow', nose='long', outfit='robe', o1='navy', o2='gray', o3='white', facial='beard', acc=[('hat', 'kalpak')])
P('grandpa_misha', 'дед Миша, рыбак', 'calm', skin='porcelain', age='old', head='round', hair='horseshoe', hair_col='white',
  eyes='sleepy', nose='ball', outfit='sweater', o1='forest', o2='cream', facial='walrus', acc=[('hat', 'beanie', 'navy')])
P('granny_rosa', 'бабушка Роза из Одессы', 'odessa', skin='olive', age='old', head='pear', hair='curly', hair_col='gray',
  eyes='round', nose='hooked', outfit='dress', o1='teal', o2='white', pattern='dots', acc=[('glasses', 'cateye', 'gold'),
  ('earrings', 'gold')], lashes=True)
P('mama_aida', 'мама, всё успевает', 'lady', skin='olive', head='oval', hair='ponytail', hair_col='espresso', eyes='round',
  nose='button', outfit='sweater', o1='rose', o2='cream', pattern='stripes', lashes=True)
P('papa_erlan', 'папа, строит скворечник', 'deep', skin='tan', head='square', hair='short', hair_col='black', eyes='narrow',
  nose='ball', outfit='shirt', o1='denim', pattern='check', o2='cream', facial='stubble', build='broad')
P('kid_arman', 'первоклассник, задаёт вопросы', 'fairy', skin='tan', age='kid', head='round', hair='buzz', hair_col='black',
  eyes='round', nose='button', outfit='tshirt', o1='sky', o2='mustard', print='star')
P('kid_sonya', 'девочка Соня, рисует везде', 'fairy', skin='porcelain', age='kid', head='round', hair='braids',
  hair_col='ginger', eyes='wide', nose='button', outfit='overalls', o1='rose', o2='cream', freckles=True)
P('kid_ali', 'мальчик Али, футболист', 'fairy', skin='brown', age='kid', head='egg', hair='curly', hair_col='black',
  eyes='round', nose='button', outfit='tshirt', o1='tomato', o2='white', print='circle', o3='tomato')
P('teen_dana', 'школьница, ведёт подкаст', 'ad', skin='olive', age='young', head='heart', hair='bob', hair_col='plumhair',
  eyes='narrow', nose='button', outfit='hoodie', o1='lilac', o2='white', acc=[('headphones', 'teal', 'cream')])
P('farmer_kanat', 'фермер, разводит овец', 'calm', skin='tan', head='jaw', hair='short', hair_col='black', eyes='narrow',
  nose='wide', outfit='overalls', o1='olive', o2='cream', pattern='check', o3='rust', acc=[('hat', 'kalpak')], facial='stubble')
P('farmer_bear', 'медведь-пасечник', 'deep', kit='bear', fur='chestnut', outfit='overalls', o1='denim', o2='rust',
  pattern='check', o3='cream', acc=[('hat', 'straw')])
P('farmer_pig', 'свинья-огородник', 'gogi', kit='pig', outfit='overalls', o1='denim', o2='mustard', acc=[('hat', 'straw')])
P('shepherd_sheep', 'овца-чабан, сама себя пасёт', 'calm', kit='sheep', outfit='robe', o1='burgundy', o2='gold', o3='forest',
  acc=[('scarf', 'teal', 'cream')])
P('lamb_kozy', 'ягнёнок Козы, любопытный', 'fairy', kit='sheep', age='kid', fur='#4a3d3a', fur2='cream', outfit='sweater',
  o1='sky', o2='white', pattern='diamonds', o3='mustard')
P('milkmaid_cow_girl', 'доярка Галя', 'lady', skin='light', head='round', hair='braids', hair_col='blonde', eyes='round',
  nose='ball', outfit='dress', o1='denim', o2='white', pattern='flowers', o3='mustard', freckles=True)
P('beekeeper_oma', 'пасечница, в шляпе', 'lady', skin='tan', age='old', head='egg', hair='bun', hair_col='white',
  eyes='sleepy', nose='button', outfit='overalls', o1='butter', o2='white', acc=[('hat', 'straw', 'cream', 'mustard')])

# ---------------------------------------------------------------- teachers, culture, sport
P('teacher_galina', 'учительница русского, строгая', 'narrator', skin='porcelain', head='long', hair='bun', hair_col='brown',
  age='old', eyes='narrow', nose='long', outfit='vest', o1='navy', shirt='white', acc=[('glasses', 'cateye', 'charcoal')],
  brow='angry')
P('teacher_marat', 'учитель истории, всё помнит', 'narrator', skin='tan', head='square', hair='sidepart', hair_col='gray',
  age='old', eyes='narrow', nose='ball', outfit='suit', o1='coffee', o3='mustard', acc=[('glasses', 'square', 'coffee')],
  facial='mustache')
P('teacher_owl', 'сова-учительница математики', 'calm', kit='owl', outfit='dress', o1='plum', o2='cream', pattern='plain',
  acc=[('glasses', 'round', 'gold'), ('necklace', 'cream')])
P('pe_coach_dog', 'пёс-физрук', 'ad', kit='dog', fur='chestnut', fur2='sand', outfit='hoodie', o1='tomato', o2='white')
P('music_teacher_cat', 'кот-учитель музыки', 'fairy', kit='cat', fur='charcoal', fur2='white', outfit='vest', o1='burgundy',
  acc=[('bowtie', 'black')])
P('librarian_mouse', 'мышь-библиотекарь, шепчет', 'calm', kit='mouse', fur='sand', fur2='cream', outfit='sweater',
  o1='sage', o2='cream', acc=[('glasses', 'cateye', 'coffee')])
P('poet_anvar', 'поэт, рифмует на ходу', 'narrator', skin='tan', head='long', hair='wavy', hair_col='espresso', eyes='sleepy',
  nose='long', outfit='shirt', o1='cream', acc=[('scarf', 'burgundy', 'gold')], facial='goatee')
P('akyn_kairat', 'акын с домброй в душе', 'deep', skin='tan', head='wide', hair='short', hair_col='black', eyes='narrow',
  nose='wide', outfit='robe', o1='forest', o2='gold', o3='burgundy', acc=[('hat', 'kalpak')], facial='mustache')
P('dancer_aru', 'танцовщица, кружится', 'lady', skin='olive', head='heart', hair='braids', hair_col='black', eyes='narrow',
  nose='button', outfit='dress', o1='burgundy', o2='gold', pattern='ikat', o3='teal', acc=[('hat', 'tubeteika', 'burgundy'),
  ('earrings', 'gold')], lashes=True)
P('rock_star_zhan', 'рок-музыкант', 'ad', skin='light', head='long', hair='mohawk', hair_col='teal', eyes='narrow',
  nose='hooked', outfit='tshirt', o1='black', o2='tomato', print='bolt', acc=[('earrings', 'silver')], facial='stubble')
P('dj_fox', 'лис-диджей', 'ad', kit='fox', fur='#9a9a9a', fur2='white', ear_tip='charcoal', outfit='hoodie', o1='plum',
  o2='white', acc=[('headphones', 'black', 'tomato')])
P('opera_diva', 'оперная прима', 'lady', skin='porcelain', head='pear', hair='bun', hair_col='auburn', eyes='round',
  nose='ball', outfit='dress', o1='wine', o2='gold', pattern='plain', lashes=True, acc=[('necklace', 'white'),
  ('earrings', 'gold')], build='broad')
P('painter_gaukhar', 'художница, в краске', 'fairy', skin='olive', head='egg', hair='bob', hair_col='black', eyes='round',
  nose='button', outfit='overalls', o1='cream', o2='rust', acc=[('hat', 'beret', 'tomato')])
P('chess_grandpa', 'шахматист, думает долго', 'calm', skin='light', age='old', head='egg', hair='horseshoe',
  hair_col='gray', eyes='sleepy', nose='long', outfit='vest', o1='coffee', shirt='cream', acc=[('glasses', 'round', 'black')])
P('boxer_bek', 'боксёр, добряк', 'deep', skin='tan', head='jaw', hair='buzz', hair_col='black', eyes='narrow', nose='wide',
  outfit='tshirt', o1='tomato', o2='white', build='broad', scar=True, brow='angry')
P('wrestler_bear', 'медведь-борец', 'deep', kit='bear', fur='#4a3a30', fur2='sand', outfit='tshirt', o1='navy', o2='gold',
  print='stripe', build='broad')
P('runner_hare', 'заяц-бегун', 'ad', kit='hare', fur='white', fur2='cream', outfit='tshirt', o1='teal', o2='white',
  print='stripe', acc=[('hat', 'cap', 'tomato')])
P('footballer_dog', 'пёс-футболист', 'ad', kit='dog', fur='white', fur2='cream', patch=True, outfit='tshirt', o1='mustard',
  o2='navy', print='circle', o3='mustard')
P('skater_frog', 'лягушка-скейтер', 'fairy', kit='frog', fur='#6f8f5a', outfit='hoodie', o1='tomato', o2='white',
  acc=[('scarf', 'mustard', 'cream')])
P('yoga_cat', 'кошка-инструктор йоги', 'calm', kit='cat', fur='#d9b48a', fur2='white', outfit='tshirt', o1='mint',
  o2='white', lashes=True)

# ---------------------------------------------------------------- animals at work and fairy-tale folk
P('fox_detective', 'лис-сыщик', 'narrator', kit='fox', outfit='suit', o1='coffee', o3='mustard', acc=[('hat', 'fedora', 'coffee',
  'black')])
P('fox_lisa', 'лиса-кумушка, сплетница', 'odessa', kit='fox', outfit='dress', o1='teal', o2='cream', pattern='dots',
  lashes=True, acc=[('scarf', 'mustard', 'rust')])
P('arctic_fox', 'песец-синоптик', 'calm', kit='fox', fur='#e9e4da', fur2='white', ear_tip='gray', iris='blue',
  outfit='sweater', o1='navy', o2='white', pattern='diamonds', o3='sky', acc=[('scarf', 'tomato', 'white')])
P('bear_mayor', 'медведь-мэр', 'deep', kit='bear', fur='chestnut', outfit='suit', o1='charcoal', o3='tomato',
  acc=[('hat', 'bowler', 'black')], build='broad')
P('panda_bear', 'медведь в чёрно-белом', 'calm', kit='bear', fur='#ece6d9', fur2='white', ears='bear', outfit='hoodie',
  o1='sage', o2='white', eyes='bead', panda=True, iris='dark')
P('cat_boss', 'кот-начальник, дремлет на совещаниях', 'deep', kit='cat', fur='gray', fur2='white', eyes='sleepy',
  iris='yellow', outfit='suit', o1='navy', o3='rust', build='broad')
P('cat_journalist', 'кошка-журналистка', 'journalist', kit='cat', fur='#3a3436', fur2='white', iris='yellow',
  outfit='suit', o1='burgundy', tie=False, shirt='cream', acc=[('mic', 'teal')], lashes=True)
P('dog_sheriff', 'пёс-шериф без звезды', 'gogi', kit='dog', fur='sand', fur2='cream', outfit='vest', o1='coffee',
  shirt='cream', acc=[('hat', 'fedora', 'sand', 'coffee')])
P('dog_reporter', 'пёс-репортёр', 'journalist', kit='dog', fur='#c9a06a', fur2='white', outfit='shirt', o1='sky',
  acc=[('mic', 'mustard')])
P('owl_judge', 'сова-судья', 'narrator', kit='owl', fur='gray', fur2='silver', outfit='robe', o1='black', o2='charcoal',
  o3='black', trim='white')
P('owl_night_dj', 'сова, ведёт ночной эфир', 'calm', kit='owl', fur='coffee', fur2='oat', outfit='hoodie', o1='navy',
  o2='white', acc=[('headphones', 'charcoal', 'mustard')])
P('frog_prince', 'лягушка, мечтает о короне', 'fairy', kit='frog', outfit='vest', o1='burgundy', shirt='cream',
  acc=[('bowtie', 'gold')])
P('frog_weather', 'лягушка-синоптик', 'ad', kit='frog', fur='#88a56a', outfit='suit', o1='teal', o3='mustard',
  acc=[('mic', 'tomato')])
P('mouse_clerk', 'мышь-клерк', 'calm', kit='mouse', outfit='shirt', o1='white', acc=[('glasses', 'square', 'charcoal')])
P('mouse_kid', 'мышонок', 'fairy', kit='mouse', age='kid', fur='#b8a898', outfit='overalls', o1='rose', o2='cream')
P('hare_coward', 'заяц-трусишка', 'fairy', kit='hare', fur='white', outfit='sweater', o1='sky', o2='white', brow='worried')
P('pig_banker', 'свинья-копилка, финансист', 'odessa', kit='pig', outfit='suit', o1='navy', o3='gold',
  acc=[('glasses', 'round', 'gold')], build='broad')
P('pig_singer', 'свинка-певица', 'lady', kit='pig', fur='#d6a0a6', outfit='dress', o1='plum', o2='white', lashes=True,
  acc=[('earrings', 'silver'), ('flower', 'cream')])
P('salmon_anchor', 'лосось, ведущий прогноза нереста', 'salmon', kit='salmon', outfit='suit', o1='navy', o3='rust',
  acc=[('mic', 'teal')])
P('salmon_grandpa', 'старый лосось, видел все пороги', 'salmon', kit='salmon', fur='#b9806e', age='old',
  outfit='sweater', o1='slate', o2='cream', eyes='sleepy')
P('salmon_kid', 'малёк', 'fairy', kit='salmon', fur='#e6a088', age='kid', outfit='tshirt', o1='sky', o2='white', print='star')
P('robot_r2', 'робот-помощник, вежливый', 'calm', kit='robot', outfit='uniform', o1='slate', o3='gold')
P('robot_bolt', 'робот-курьер', 'ad', kit='robot', fur='#b0866a', fur2='sand', iris='amber', outfit='hoodie', o1='teal',
  o2='white', o3='mustard')
P('robot_nanny', 'робот-няня', 'fairy', kit='robot', fur='#a9c1c0', iris='blue', head='round', outfit='dress', o1='rose',
  o2='white', o3='rose', lashes=True)
P('robot_boss', 'робот-директор, оптимизирует всех', 'deep', kit='robot', fur='#6b7378', iris='redeye', outfit='suit',
  o1='black', o3='tomato', brow='angry')
P('monster_gurgle', 'добрый монстр Гургл', 'deep', kit='monster', outfit='hoodie', o1='mustard', o2='white', fangs=True)
P('monster_fifi', 'монстрик Фифи', 'fairy', kit='monster', fur='#7fa6a2', fur2='mint', iris='amber', outfit='sweater',
  o1='rose', o2='cream', eyes='round', lashes=True, hair='tuft', hair_col='rose')
P('monster_grumbo', 'ворчливый монстр', 'deep', kit='monster', fur='#8a6f4e', iris='yellow', outfit='overalls',
  o1='denim', o2='rust', brow='angry', eyes='narrow', bushy=True)
P('imp_accountant', 'бес-бухгалтер, считает грехи в Excel', 'odessa', kit='imp', fur='#9a4a44', outfit='vest', o1='black',
  shirt='cream', acc=[('glasses', 'round', 'gold')], fangs=True)
P('sheep_poet', 'овечка-поэтесса', 'lady', kit='sheep', outfit='dress', o1='lilac', o2='white', lashes=True,
  acc=[('flower', 'rose')])
P('fairy_godmother', 'фея-крёстная, без палочки', 'fairy', skin='porcelain', head='round', hair='curly', hair_col='white',
  age='old', eyes='round', nose='button', outfit='dress', o1='lavender', o2='white', pattern='dots', lashes=True,
  acc=[('necklace', 'lavender')])
P('wizard_merlan', 'звездочёт, без символов', 'narrator', skin='light', head='long', hair='long', hair_col='white', age='old',
  eyes='sleepy', nose='long', outfit='robe', o1='navy', o2='navy', o3='lilac', trim='gold', facial='beard', bushy=True)
P('pirate_jack', 'пират в отставке', 'odessa', skin='tan', head='jaw', hair='long', hair_col='espresso', eyes='narrow',
  nose='hooked', outfit='vest', o1='burgundy', shirt='cream', facial='beard', acc=[('earrings', 'gold'), ('scarf', 'tomato', 'cream')])
P('batyr_er', 'батыр, добрый великан', 'deep', skin='tan', head='square', hair='topknot', hair_col='black', eyes='narrow',
  nose='wide', outfit='robe', o1='rust', o2='mustard', o3='coffee', facial='mustache', build='broad')
P('aldar_kose', 'хитрец-шутник из степи', 'gogi', skin='tan', head='diamond', hair='bald', hair_col='black', eyes='narrow',
  nose='button', outfit='robe', o1='teal', o2='white', o3='mustard', acc=[('hat', 'tubeteika')], smile=0.22)

# ---------------------------------------------------------------- more people: varied looks and ages
P('kenji_photographer', 'фотограф, ловит свет', 'calm', skin='light', head='oval', hair='short', hair_col='black',
  eyes='narrow', nose='button', outfit='tshirt', o1='olive', o2='cream', print='circle', o3='olive',
  acc=[('glasses', 'round', 'black')])
P('amara_anchor', 'ведущая новостей', 'journalist', skin='deep', head='oval', hair='curly', hair_col='black', eyes='round',
  nose='wide', outfit='suit', o1='mustard', tie=False, shirt='white', acc=[('earrings', 'gold'), ('mic', 'navy')], lashes=True)
P('omar_tailor', 'портной, шьёт войлок', 'gogi', skin='brown', head='long', hair='horseshoe', hair_col='gray', age='old',
  eyes='sleepy', nose='hooked', outfit='vest', o1='olive', shirt='cream', facial='beard', acc=[('glasses', 'round', 'gold')])
P('priya_scientist', 'астрофизик', 'narrator', skin='brown', head='heart', hair='long', hair_col='black', eyes='round',
  nose='long', outfit='labcoat', shirt='plum', acc=[('earrings', 'gold')], lashes=True)
P('lucas_surfer', 'серфер, всё «нормально»', 'ad', skin='tan', head='jaw', hair='wavy', hair_col='blonde', eyes='sleepy',
  nose='button', outfit='tshirt', o1='teal', o2='butter', print='circle', o3='coral', facial='stubble')
P('ngozi_doctor', 'педиатр', 'lady', skin='deep', head='round', hair='bun', hair_col='black', eyes='round', nose='wide',
  outfit='labcoat', shirt='coral', acc=['stethoscope'], lashes=True)
P('chen_grandma', 'бабушка, гимнастика в парке', 'calm', skin='light', age='old', head='round', hair='bob', hair_col='white',
  eyes='narrow', nose='button', outfit='sweater', o1='teal', o2='cream', pattern='stripes')
P('fatima_teacher', 'учительница английского', 'lady', skin='olive', head='oval', hair='kerchief', kerchief='sage',
  kerchief2='cream', eyes='round', nose='button', outfit='shirt', o1='cream', lashes=True,
  acc=[('glasses', 'square', 'burgundy')])
P('igor_trucker', 'дальнобойщик', 'deep', skin='porcelain', head='potato', hair='buzz', hair_col='brown', eyes='narrow',
  nose='ball', outfit='shirt', o1='rust', pattern='check', o2='black', facial='beard', build='broad', acc=[('hat', 'cap', 'charcoal')])
P('asylbek_student', 'студент, вечно голодный', 'ad', skin='tan', age='young', head='long', hair='quiff', hair_col='black',
  eyes='narrow', nose='button', outfit='hoodie', o1='navy', o2='mustard', freckles=False, brow='worried')
P('dilnoza_designer', 'дизайнер, видит шрифты во сне', 'calm', skin='olive', age='young', head='heart', hair='topknot',
  hair_col='espresso', eyes='narrow', nose='button', outfit='tshirt', o1='mustard', o2='black', print='circle', o3='tomato',
  acc=[('glasses', 'round', 'tomato'), ('earrings', 'silver')])
P('petya_blogger', 'блогер, «ставьте лайки»', 'ad', skin='light', age='young', head='pear', hair='spiky', hair_col='rose',
  eyes='wide', nose='button', outfit='tshirt', o1='lilac', o2='butter', print='star', acc=[('mic', 'lilac')])
P('auntie_raya', 'тётя Рая, соседка сверху', 'odessa', skin='porcelain', head='round', hair='curly', hair_col='auburn',
  eyes='round', nose='ball', outfit='dress', o1='tomato', o2='white', pattern='dots', build='broad', lashes=True,
  acc=[('earrings', 'gold')])
P('uncle_vano', 'дядя Вано, тамада', 'gogi', skin='olive', head='egg', hair='horseshoe', hair_col='black', eyes='round',
  nose='hooked', outfit='suit', o1='black', o3='burgundy', facial='walrus', bushy=True, build='broad')
P('sasha_courier', 'велокурьер', 'ad', skin='light', age='young', head='oval', hair='short', hair_col='ash', eyes='round',
  nose='long', outfit='hoodie', o1='tomato', o2='charcoal', acc=[('hat', 'beanie', 'charcoal')])
P('yerlan_pilot', 'пилот, говорит «пристегнитесь»', 'narrator', skin='tan', head='square', hair='sidepart',
  hair_col='black', eyes='narrow', nose='ball', outfit='uniform', o1='navy', o3='gold', acc=[('hat', 'cap', 'navy')])
P('svetlana_mayor', 'мэр города, режет ленточки', 'narrator', skin='porcelain', head='diamond', hair='bob', hair_col='blonde',
  eyes='round', nose='long', outfit='suit', o1='plum', tie=False, shirt='white', acc=[('necklace', 'white')], lashes=True)
P('gulnara_judge', 'судья, справедливая', 'calm', skin='tan', head='oval', hair='bun', hair_col='black', eyes='narrow',
  nose='button', outfit='robe', o1='black', o2='charcoal', o3='black', trim='white', acc=[('glasses', 'square', 'gold')])
P('ruslan_guard', 'охранник, «вы к кому?»', 'deep', skin='tan', head='jaw', hair='buzz', hair_col='black', eyes='narrow',
  nose='wide', outfit='uniform', o1='charcoal', o3='silver', build='broad', brow='angry')
P('lyuda_cashier', 'кассир, «пакет нужен?»', 'odessa', skin='light', head='egg', hair='curly', hair_col='ginger',
  eyes='sleepy', nose='ball', outfit='vest', o1='teal', shirt='white', acc=[('lanyard', 'tomato')], lashes=True)
P('nursultan_runner', 'марафонец', 'ad', skin='tan', head='long', hair='short', hair_col='black', eyes='narrow', nose='long',
  outfit='tshirt', o1='sky', o2='white', print='stripe', acc=[('hat', 'cap', 'white')])
P('aisha_vlogger', 'девочка-влогер', 'fairy', skin='brown', age='kid', head='round', hair='bun', hair_col='black', eyes='wide',
  nose='button', outfit='hoodie', o1='pink', o2='white', acc=[('headphones', 'rose', 'white')])
P('boris_neighbor', 'сосед с дрелью', 'deep', skin='porcelain', head='square', hair='horseshoe', hair_col='brown',
  eyes='sleepy', nose='ball', outfit='tshirt', o1='gray', o2='cream', facial='stubble', build='broad')
P('kamal_chef', 'шеф-повар фьюжн', 'gogi', skin='brown', head='oval', hair='buzz', hair_col='black', eyes='round', nose='wide',
  outfit='chef', o1='mustard', facial='goatee', acc=[('hat', 'toque')])
P('eva_scientist', 'генетик', 'calm', skin='porcelain', head='oval', hair='ponytail', hair_col='brown', eyes='round',
  nose='button', outfit='labcoat', shirt='lilac', acc=[('glasses', 'round', 'teal')], freckles=True)
P('akmal_farmer', 'дехканин, растит дыни', 'gogi', skin='tan', age='old', head='wide', hair='bald', eyes='narrow',
  nose='wide', outfit='robe', o1='forest', o2='mustard', o3='white', facial='beard', hair_col='gray',
  acc=[('hat', 'tubeteika')])
P('baby_ayan', 'малыш Аян, первое слово', 'fairy', skin='olive', age='kid', head='round', hair='tuft', hair_col='black',
  eyes='wide', nose='button', outfit='overalls', o1='sky', o2='white', R=0.2)
