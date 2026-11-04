# PUPPET: minimal complete program
tags: example, skeleton, template
film title="Цель накоплений" style=puppet fps=24 size=1920x1080
shot 0-3.5s: pl_tv_studio pull=0.2
fade in 0-0.6s
music mood=calm tempo=72 0-22s
voice "[deep] Сегодня в студии — финансовый эксперт." at 0.3s
shot 3.5-7s: ch_dina push=0.02
say ch_dina "Сколько у вас сейчас?" at 3.8s
shot 7-11s: ch_piggybank push=0.05 focus=0.5,0.4
say ch_piggybank "Ничего. Это осознанный минимализм." at 7.3s
shot 11-14s: ch_dina push=0.04
say ch_dina "А подушка безопасности?" at 11.3s
shot 14-18.5s: ch_piggybank push=0.1 focus=0.5,0.4
say ch_piggybank "Подушка — это я. Внутри просто воздух." at 14.3s
shot 18.5-22s: ch_dina pull=0.2
say ch_dina "А вы сами на что копите?" at 18.8s
shot 22-25s: ch_piggybank push=0.04 focus=0.5,0.4
shot 25-27.5s: ch_piggybank push=0.02 snap=25.3 focus=0.5,0.4
say ch_piggybank "[deadpan] На молоток." at 25.3s
fade out 27.1-27.5s
