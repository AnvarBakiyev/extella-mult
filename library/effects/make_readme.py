"""Writes README.md from effects.json (run after render.py)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(os.path.join(HERE, 'effects.json')))

CATS = [('weather', 'Погода'), ('fire', 'Огонь и дым'), ('water', 'Вода'), ('celebration', 'Праздник'), ('comic', 'Комикс-знаки'),
        ('money', 'Деньги'), ('magic', 'Магия'), ('tech', 'Техника'), ('nature', 'Природа'), ('transition', 'Переходы как эффекты')]


def dir_size(p):
    t = 0
    for r, _, fs in os.walk(p):
        t += sum(os.path.getsize(os.path.join(r, f)) for f in fs)
    return t


seq_mb = dir_size(os.path.join(HERE, 'seq')) / 1e6
prev_mb = dir_size(os.path.join(HERE, 'preview')) / 1e6

L = []
L.append('# Войлочные эффекты из кода\n')
L.append('%d анимированных эффектов в войлочном стиле. Всё нарисовано кодом: numpy + Pillow + scipy, без ИИ-картинок, '
         'без платных сервисов и без готовых ассетов. Каждый кусочек проходит войлочный фильтр с тем же рецептом, что '
         '`handler/felt.py::felt_composite` из extella-mult: мягкий скос со светом сверху слева, тёмный край, ворс, '
         'пушистая кромка, мягкая тень.\n' % J['count'])
L.append('Смотреть сначала: `contact_sheet.jpg` (по кадру на эффект) и `showcase.mp4` (30 секунд, все эффекты сеткой 3×3).\n')
L.append('## Что где\n')
L.append('| файл | что |\n|---|---|')
L.append('| `effects_lib.py` | библиотека: %d функций `fx(t, params) -> RGBA`, реестр `EFFECTS` |' % J['count'])
L.append('| `feltcore.py` | войлочный движок: фигуры, строчка, войлочный спрайт с кэшем, холст, фон для превью |')
L.append('| `render.py` | рендер последовательностей, превью, `effects.json`, контактного листа и витрины |')
L.append('| `seq/<name>/0000.png…` | прозрачные PNG-кадры, 24 к/с (у тумана и облаков 12 к/с), тень уже внутри альфы |')
L.append('| `preview/<name>.mp4` | превью 960×540 на нейтральном войлочном фоне (петли проиграны 2–3 раза) |')
L.append('| `effects.json` | имя, категория, описание, параметры, петля или нет, длительность, кадры, размер |')
L.append('| `contact_sheet.jpg`, `showcase.mp4` | обзор |')
L.append('| `peek.py` | быстрый просмотр кадров при разработке |\n')
L.append('Размер: кадры %.0f МБ, превью %.0f МБ. PNG сжаты pngquant (палитра 256 цветов с альфой, на глаз без потерь, '
         'в 3–4 раза меньше). Полноэкранные эффекты (занавес, ирис, разрыв, туман, глитч, волны, линии скорости) '
         'хранятся в 960×540; функция при этом рисует любой размер.\n' % (seq_mb, prev_mb))
L.append('## Как пользоваться\n')
L.append('```python\nimport effects_lib as E\n\nimg = E.snow_light(1.25)                       # кадр в момент 1.25 с, RGBA 1920x1080\n'
         'img = E.hearts_float(0.5, {"at": (0.3, 0.5), "seed": 7})   # из точки, другой случайный рисунок\n'
         'img = E.render("fireworks", 2.0, {"W": 960, "H": 540})     # любой размер, всё масштабируется по высоте\n'
         'scene.alpha_composite(img)                      # наложить на кадр мультика\n```\n')
L.append('Общие параметры: `seed` (детерминированно), `W`, `H`, `dur` (длина петли или разового эффекта), `at=(x, y)` в долях кадра '
         'для эффектов из точки, `size` (масштаб значков у головы), `density`/`count`, `floor` (уровень пола). '
         'У петель кадр в `t` и в `t + dur` совпадает, стык незаметен: частицы идут потоком, где каждая частица рождается '
         'на сетке времени, кратной длине петли.\n')
L.append('Как устроено: эффект описывает кусочки векторно (многоугольники, полосы, строчка). Кусочек растеризуется с '
         'двойным сглаживанием, превращается в войлок один раз и кэшируется (по форме, размеру, квантованному углу), дальше '
         'только вклеивается. Поэтому 100–400 войлочных кусочков в кадре 1920×1080 рисуются за 0,05–0,5 с на одном ядре.\n')
L.append('Перерендер: `python3 render.py` (всё, 4 процесса, ~25 минут) или `python3 render.py snow_light hail` (отдельные).\n')
L.append('## Эффекты\n')
by = {}
for e in J['effects']:
    by.setdefault(e['category'], []).append(e)
for key, title in CATS:
    items = by.get(key, [])
    L.append('### %s (%d)\n' % (title, len(items)))
    L.append('| эффект | что | петля | с | параметры |\n|---|---|---|---|---|')
    for e in items:
        ps = ', '.join('%s=%s' % (k, v) for k, v in e['params'].items() if k != 'seed')
        L.append('| `%s` | %s | %s | %.1f | %s |' % (e['name'], e['about'], 'да' if e['loop'] else 'нет', e['duration'], ps))
    L.append('')
open(os.path.join(HERE, 'README.md'), 'w').write('\n'.join(L) + '\n')
print('README.md written')
