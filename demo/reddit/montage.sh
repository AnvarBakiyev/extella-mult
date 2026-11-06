#!/bin/zsh
# "Grandma is waiting", before and after. Run from the repository root.
#   montage.sh parts    cards and labels only
#   montage.sh render   before on a clean v3 copy, after here, then parts and montage
#   montage.sh after    after and montage only, when before is ready
#   montage.sh montage  montage from what is already rendered
# Before = grandma.scene without its say lines, which v3 cannot read; nothing else changes. Both render with MULT_SUPER_FELT=2.
set -e
D=demo/reddit; O=out/reddit; mkdir -p $O/seg
export MULT_SUPER_FELT=2
FF=$(python3 -c "from handler.config import ffmpeg; print(ffmpeg())")
BG=0xf6ecd8

parts() {
  for fmt in 169 11; do
    if [ $fmt = 169 ]; then sz=1920x1080; s1=0.1; s2=0.095; else sz=1080x1080; s1=0.07; s2=0.068; fi
    sed -e "s/SIZE/$sz/" -e "s/S1/$s1/" -e "s/S2/$s2/g" $D/cards.scene > $O/cards-$fmt.scene
    python3 -m handler.main $O/cards-$fmt.scene --out $O/cards-$fmt.mp4 --procs 6 2>/dev/null
  done
  sed -e 's/SIZE/900x70/' -e 's/WORDS/Before: v3 (no emotions, no speech bubbles)/' -e 's/LS/0.48/' $D/label.scene > $O/lb.scene
  sed -e 's/SIZE/220x70/' -e 's/WORDS/After/' -e 's/LS/0.62/' $D/label.scene > $O/la.scene
  cp $D/label2.scene $O/lb2.scene
  for n in lb lb2 la; do
    python3 -m handler.main $O/$n.scene --frames 0.9 --dir $O/$n 2>/dev/null
    mv $O/$n/000.90.png $O/$n.png; rmdir $O/$n
  done
}

render_before() {
  grep -vE '^[a-z]+ say ' $D/grandma.scene > $O/before.scene
  V=$(mktemp -d)/v3
  git worktree add -q --detach $V v3
  cp -R assets $V/
  ABS=$PWD/$O
  SECONDS=0
  (cd $V && python3 -m handler.main $ABS/before.scene --out $ABS/before.mp4 --procs 6)
  echo "before ${SECONDS}s" > $O/times.txt
  git worktree remove --force $V
}

render_after() {
  rm -rf $O/after.mp4_frames
  SECONDS=0
  python3 -m handler.main $D/grandma.scene --out $O/after.mp4 --procs 6
  echo "after ${SECONDS}s" >> $O/times.txt
}

enc=(-r 24 -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -b:a 192k -ar 48000 -ac 2)
soft="fade=t=in:st=0:d=0.25:color=${BG}"

card() {  # card FORMAT START LENGTH OUT
  $FF -v error -y -ss $2 -t $3 -i $O/cards-$1.mp4 -f lavfi -t $3 -i anullsrc=r=48000:cl=stereo \
    -filter_complex "[0:v]$soft,fade=t=out:st=$(( $3 - 0.25 )):d=0.25:color=${BG}[v]" -map "[v]" -map 1:a -shortest $enc $4
}

both() {  # both FORMAT START LENGTH OUT: before and after at once, in step
  if [ $1 = 169 ]; then
    c=1920x1080; lb=lb2; bs=960:540; lay="[bg][b]overlay=0:270[x];[x][a]overlay=960:270[y];[y][lb]overlay=930-w:112[z];[z][la]overlay=1890-w:182"; ls=900; lh=150; h=76
  else
    c=1080x1080; lb=lb; bs=854:480; lay="[bg][b]overlay=113:60[x];[x][a]overlay=113:600[y];[y][lb]overlay=967-w:0[z];[z][la]overlay=967-w:542"; ls=760; lh=59; h=56
  fi
  $FF -v error -y -ss $2 -t $3 -i $O/before.mp4 -ss $2 -t $3 -i $O/after.mp4 -i $O/$lb.png -i $O/la.png -f lavfi -t $3 -i color=c=${BG}:s=${c}:r=24 \
    -filter_complex "[0:v]scale=${bs}[b];[1:v]scale=${bs}[a];[2:v]scale=${ls}:${lh}[lb];[3:v]scale=-1:${h}[la];[4:v]null[bg];$lay,$soft,fade=t=out:st=$(( $3 - 0.25 )):d=0.25:color=${BG}[v]" \
    -map "[v]" -map 1:a $enc $4
}

whole() {  # whole FORMAT OUT: all of after, with its label
  if [ $1 = 169 ]; then
    f="[0:v][1:v]overlay=main_w-w-30:24"
  else
    f="[2:v]scale=1080:608[a];[3:v][a]overlay=0:236[x];[x][1:v]overlay=main_w-w-30:150"; 
  fi
  if [ $1 = 169 ]; then
    $FF -v error -y -i $O/after.mp4 -i $O/la.png -filter_complex "$f,${soft}[v]" -map "[v]" -map 0:a $enc $2
  else
    $FF -v error -y -i $O/after.mp4 -i $O/la.png -i $O/after.mp4 -f lavfi -t 18 -i color=c=${BG}:s=1080x1080:r=24 -filter_complex "$f,${soft}[v]" -map "[v]" -map 0:a -shortest $enc $2
  fi
}

join() {  # join OUT SEG...
  out=$1; shift
  : > $O/seg/list.txt
  for s in $@; do echo "file '$PWD/$s'" >> $O/seg/list.txt; done
  $FF -v error -y -f concat -safe 0 -i $O/seg/list.txt -c copy -movflags +faststart $out
}

montage() {
  for fmt in 169 11; do
    n=$O/seg/$fmt
    card $fmt 0 2 $n-start.mp4
    card $fmt 2 3 $n-end.mp4
    both $fmt 0 18 $n-both.mp4
    both $fmt 2 2.5 $n-p1.mp4
    both $fmt 10.6 2.4 $n-p2.mp4
    both $fmt 13.4 2.6 $n-p3.mp4
    whole $fmt $n-whole.mp4
    join $O/grandma-A-$fmt.mp4 $n-start.mp4 $n-both.mp4 $n-end.mp4
    join $O/grandma-B-$fmt.mp4 $n-p1.mp4 $n-p2.mp4 $n-p3.mp4 $n-whole.mp4 $n-end.mp4
  done
}

case "$1" in
  parts) parts ;;
  render) parts; render_before; render_after; montage ;;
  after) render_after; montage ;;
  montage) montage ;;
  *) echo "use: parts, render, after or montage"; exit 2 ;;
esac
