# Visual style guide

A fast, presenter-free documentary explainer: mostly animated maps and moving objects, broken up by highlighted news clippings, honest charts and real photos. Calm narrator, no music by default.

## Palette (RGB, defined in the engine)

| Name | Use |
|---|---|
| `TEAL` (31,181,168) | the main country or side of the story |
| `ORANGE` (240,138,36) | the other side, date-card bars, name bars |
| `RED` (226,65,58) | strikes, attacks, deaths, warnings |
| `NAVY` (90,140,210) | navies, blockades, sea routes |
| `YELLOW` (255,214,64) | clipping highlights, one key word in a title |
| `WHITE` / `GREY` | text / secondary text and sources |

One accent per side, used the same way in every part. Never more than three accent colours on one frame.

## Maps

- Dark, desaturated shaded relief (Natural Earth) with near-black sea. Countries in the story get a soft accent fill (alpha about 0.4) plus a bright border; everything else stays grey.
- The camera never sits still: every map shot drifts or zooms slowly (`mapscene(c0, c1)`).
- **Opening move:** a dark globe that spins and dives into the region (`globescene`), dissolving into the flat map, then a zoom to the city or strait.
- **Traffic:** where shipping or flights are the story, keep ships moving in both lanes the whole shot (`traffic`); lanes are illustrative unless you have AIS data.
- Labels: country names in Bebas Neue capitals with letter spacing; cities in Inter semibold next to a pulsing pin. White with a soft shadow.
- Routes are dashed lines that draw on, with a jet, plane, ship, carrier, drone or missile icon riding the line, turned to its heading. Strikes end in a flash ring.
- Keep labels off routes, arcs and rings. If they collide, move the label, not the data.

## Cards

- **Date cards:** huge Bebas date that types on, a small grey subline (weekday or context), an orange bar on the left. Hold 2-3 s.
- **Lower thirds:** short Bebas headline + one grey line of detail, sliding in from the left.
- **Counters:** a number that counts up, a label under it, and the source in grey under that.
- **Chapter cards:** "PART 2" in small orange spaced capitals over a big title, on a dim map, before the part's voice starts.
- **Boards** (tolls, figures): numbers right-aligned in one column, descriptions left-aligned in the next.

## Kinetic text

- Key sentences can be typed on screen **word by word, exactly when the narrator says each word** (`kinetic` + `voice_words`), in Bebas capitals with one or two key words in yellow.
- Use it for the hook, for the one number that matters, and for the closing line. Not on every shot.
- Over footage or busy maps, put a soft gradient behind it (`fade_edge`), never a hard box.

## Source clippings

- The exact sentence from the article on a light paper card, slightly rotated, drop shadow, outlet name in dark red capitals at the top, "Source: outlet · date" at the bottom.
- The key phrase gets a yellow marker that draws on in sync with the narration.
- Only real sentences, quoted exactly. A clipping is a quotation, so it must match the source word for word.

## Photos and footage

- Real, credited, free-licence media only. Every photo and clip carries a small credit line bottom right **with its real date and place**: older footage can illustrate a general point ("a tanker in the strait") but must never pass for a newer event.
- Crop away burned-in captions, logos and redaction boxes (`crop=`).
- People (`p_*` files) use the portrait layout: blurred dark backdrop, the photo on the right with a feathered edge, name bar bottom left. Heads are never cropped.
- Other stills get a slow Ken Burns move. All media is slightly desaturated and darkened to sit with the maps.

## Charts

- Plot only the points you have a source for, with the value and date on each point.
- A period with no data is a dashed line labelled "values in between not shown". Never smooth or interpolate.
- Parliaments, polls and other non-regional splits use a split bar, not a coloured map.

## Pacing and transitions

- A new shot every 3-6 s; alternate map/data shots with photo/clipping shots.
- 0.25 s cross-dissolves between shots; slow pushes inside shots. No gimmicky wipes.
- Light film grain and a soft vignette on every frame tie it all together.

## Sound

- The voice is the master track, loudness-normalised to about -15 LUFS.
- Soft whooshes on cuts (about 30 dB under the voice) and a low hit under chapter cards. No music unless asked; if asked, a low bed about 20 dB under the voice.

## Consistency

Same basemap, accents, fonts, label style and clipping style in every part.
