# QA checklist (every part, before showing the user)

Run `$PY $SK/render.py sheet <part> 2` and look at every tile, then open full-size stills of anything doubtful (`render.py stills <part> <t>`).

## Overlaps (the most common fault)
- [ ] No text crosses another text, a route, an arc, a ring, a pin or a country border it's not about.
- [ ] Date cards and lower thirds don't sit on the part of the map where the action is; move the card, not the action.
- [ ] Two cards are never on screen in the same corner at once.
- [ ] Dots, icons and arcs fade out before a counter or card appears over them.
- [ ] Stacked titles ("A DEAL?" / "OR A NEW WAR?") have clear space between lines.
- [ ] Table/board rows: numbers and descriptions in separate columns, nothing touching.

## Readability
- [ ] Every label readable at 1080p and still roughly readable on a phone.
- [ ] Nothing important within 60 px of the frame edge; nothing cut off.
- [ ] Map labels don't sit on bright fills; tone the fill down instead.

## Truth
- [ ] Every number on screen matches the script and the research brief.
- [ ] Every chart point has a source; gaps are dashed and labelled.
- [ ] Clippings match their source word for word, with outlet and date.
- [ ] Every photo/clip has a credit line with the date; no watermark visible.
- [ ] No coloured map used for a non-regional result.

## Timing and sound
- [ ] Each shot appears with the words it illustrates (not late).
- [ ] No black or frozen frames; cuts are dissolves, not jumps.
- [ ] Voice clear, loudness about -15 LUFS (`ffmpeg -i out.mp4 -af ebur128 -f null -`), no music unless asked.

## Finish
- [ ] Versioned file name; no older render overwritten or deleted.
- [ ] Tell the user which shots use fallbacks instead of real media.
