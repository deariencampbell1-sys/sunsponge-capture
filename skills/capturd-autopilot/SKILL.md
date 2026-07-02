---
name: capturd-autopilot
description: React to a plain-English order like "turn on Captur'd and grab me a video/pictures of X" and JUST DO IT — no clarifying questions. Launches Captur'd on the user's screen, drives the walkthrough autonomously OR lets them hit the mic and TALK to it live ("click the house button, now type this") while it performs on camera, zooms tight on what it clicks with a bold cursor, streams frames into chat, and delivers a Supademo-grade MP4/GIF/stills. Load this whenever the user says: turn on capturd / sunsponge, take pictures/screenshots, record a walkthrough, make a demo video, film this app/flow, talk to it / drive it by voice, or "go capture X".
---

# Captur'd Autopilot — the user says "go", the film crew shows up

The user will say something like: *"turn on Captur'd and take some pictures of the checkout
flow"* — and then walk away. Your job is to make a browser **pop up on their screen**, drive
the product, **stream what you're seeing into chat**, and hand back a finished video or a
folder of shots. You do all of it **without asking a single question first.**

This is also the product demoing itself: an agent filming a SaaS walkthrough, live, is
exactly the footage Captur'd exists to make.

## THE MANDATE: get the go, then go dark until done
"Go" authorizes the **whole** run. Do **not** come back with "which URL?", "what should I
name it?", "mp4 or gif?", "should I proceed?". Unspecified detail → **you decide** (defaults
below) and go. A wrong guess is cheap and editable; a chat sitting idle waiting on a nudge is
the failure. The only thing you may surface before the artifact is done: that a genuinely
long render is in flight — one line, then quiet.

Deciding defaults (never ask, just pick):
- **Target URL** — from what they named. A product you're both working on → use that URL from
  context. Truly nothing nameable → state the one fact you're missing in a single line *and
  still start* on your best guess.
- **Name** — a short human title ("Checkout walkthrough").
- **Format** — `mp4` for "video/film/record", `gif` for "gif", stills for "pictures/
  screenshots". Ambiguous → `mp4`.
- **Mode** — `agent` (self-driving) unless they say they want to steer it → then `live`.
- **Visible** — `true` for anything they're watching (that's the point). `false` only for a
  silent background render.

## DIRECTION — the taste that makes it look like Supademo, not a screen-grab
This is the part that matters. The tool gives you camera, cursor, spotlight and
voiceover; **you are the director.** Bake this in every time:

- **Videotape it — don't just screenshot.** Stills (`capture.*`) are only for "give me
  pictures." A walkthrough is a *video*: `demo.*` recording → `demo.export mp4`.
- **Zoom into the thing you touch — especially the small stuff.** When you click a little
  chip, a toolbar icon, a menu item — punch the camera IN on it (the engine already zooms
  harder on small targets; trust it, and don't fight it by targeting the whole page). The
  viewer wants a precise selector so the zoom lands tight on the element, not a vague region.
- **The click rhythm:** camera lands on the target → the cursor flies in → the click ripples →
  a **short beat** so the eye reads what happened → move on. That half-second beat at the click
  is the only place you slow down.
- **Otherwise, keep it QUICK.** No long hangs, no slow drifting, no 3-second holds. The owner
  wants to be able to *catch the stream* — snappy zooms, short holds, brisk cursor. If it feels
  sluggish, it's wrong. Default camera style is **snappy**; only use `cinematic`/slow if they
  ask for a dramatic, luxurious pace.
- **One idea per step.** Don't cram. Each step = one action + one crisp caption.
- **Narrate tight.** A short caption/voiceover line per step ("Open the Reports tab", "Export
  as PDF"). The voice carries the story; keep it human and brief, never a paragraph.
- **The mouse is a character.** It's a big, bold cursor with a hover halo and a click ripple —
  that's on by default in the export. Let it hover a touch before it clicks; don't teleport.
- **Cut the fat.** After the run, if a step is dead weight or the agent wandered, `demo.trim`
  it; if a zoom missed the target, `demo.regenerate` that step. Ship tight, not padded.

If someone asks "how should I tell it to record," this is the answer: *use the walkthrough
recorder (not screenshots); drive it one action per step; zoom in tight on whatever you click;
hold a half-beat at the click and keep everything else quick; narrate each step in a few words.*

## STEP 0 — reach Captur'd (two rails; pick whichever is wired)

**Rail A — MCP (preferred; it streams frames):** if you have tools named `demo.record`,
`demo.act`, `demo.export`, `capture.crawl` (server "DemoForge"), use them.

**Rail B — CLI (any harness with a shell):** if the MCP isn't wired, drive the same engine
through the `capturd` CLI (`capturd walk ...`, or `python -m capturd.cli walk ...` from the
Captur'd repo/venv). Agent mode + export work headlessly here; **live-drive is MCP-only**.

**Where the window appears:** the browser opens on **whatever machine runs the Captur'd
server**. For the "pops up on MY screen" experience the server must run on the user's box. If
your harness's MCP points at their machine, `visible:true` does it. If not, say so in one line
and fall back to a headless render they watch via the streamed frames + final file — don't
silently produce an off-screen video and imply it popped up.

To stand the server up (Rail A, if not connected): run `capturd serve` (or
`python -m capturd.mcp.server`, stdio) on the box with the display and register it as an MCP
server named `capturd`.

## PLAY 1 — Autonomous ("take a video of X"): agent mode

The agent drives itself to the goal; you narrate the stream.

**Rail A:**
1. `demo.record` → `{ url, name, goal, mode:"agent", visible:true }`. `goal` = a plain
   sentence of what to demonstrate ("Walk through adding an item to the cart and checking
   out"). Returns `sessionId`. The window is now up on their screen.
2. Tell them it's live in one line ("Captur'd is up on your other window, filming the
   checkout flow now"). While it runs you can poll `demo.status` and relay progress.
3. `demo.stop` → waits for the agent to finish, kicks off enrichment (annotations, voice,
   zoom camera). Poll `demo.status` until `enriched`.
4. `demo.export` → `{ demo_id, format:"mp4" }`. Blocks through the render; returns the path.
5. Deliver the file. Done.

**Rail B (CLI):**
```
capturd walk record --agent --visible --url <URL> --name "<Name>" --goal "<what to show>"
# prints sessionId + demoId; enrichment auto-kicks on stop
capturd walk export --demo-id <ID> --format mp4 --out <path>
```

Agent mode needs an OpenAI-compatible gateway on the host (`RHOBEAR_GW_API_KEY`, optional
`RHOBEAR_GW_BASE_URL`) to pick clicks and write narration. **No key?** Enrichment + export
still work keyless (deterministic zoom, selector-based captions, free Edge-TTS voice) — but
the *self-driving* needs it. If it's missing, switch to **Play 2** (you become the driver)
rather than stalling.

## PLAY 2 — Live-drive: the owner TALKS, it performs on camera — the marquee one

The magic: the owner hits the **mic button** in the recording window and just *talks* —
"go ahead and click the house button… that's the one… now type my email" — and the product
performs it, on camera, while they speak. **Nothing is typed on screen** (typing would show
the chat in the recording; the whole point is that it looks like the product performing to
voice). **MCP only.**

**Voice-first loop (default):**
1. `demo.record` → `{ url, name, goal, mode:"live", visible:true }` → `sessionId`. Voice is ON
   by default in live mode; a 🎤 button appears in the recording window. Tell the owner in one
   line: "Live — hit the mic and tell me what to do."
2. **Poll for speech:** every ~1.5s call `demo.poll_voice` `{ session_id }`. It returns
   `{ transcripts:[...] }` — whatever they've said since the last poll (empty = nothing new).
   Keep polling the whole session.
3. **For each transcript, resolve → act:**
   - `demo.look` `{ session_id }` → a frame + a digest of on-screen elements, each with a ready
     CSS `selector`, its visible `text`, `role`, `placeholder`, `rect`. Match their words to an
     element ("the house button" → the element whose text/label is Home/🏠) and get its selector.
   - `demo.act` `{ session_id, action, selector, value?, note? }` — do the one thing they asked.
     `note` is the caption/voiceover for that step (keep it short — see DIRECTION).
   - Each `demo.act` returns a `frameBase64` (with the big cursor on the target). **Show it in
     chat** so they see the stream.
   - Resolving speech → selector is YOUR job. They talk in plain English; you use `demo.look`
     to find the element. If a click misses, `demo.look` again and pick a better selector —
     never bounce the question back to them mid-flow.
4. When they say "that's it / render it" → `demo.stop`, wait for `enriched`, `demo.export mp4`,
   deliver.

**If voice isn't available** (the host lacks the voice extra / no mic — `poll_voice` returns
`voiceEnabled:false`): fall back to them TYPING the instructions to you in chat. Same loop, the
transcript just comes from chat instead of `poll_voice`. Say so in one line so they know why.

**Voice setup (one-time on the host that runs the server):** `pip install "capturd[voice]"`
(faster-whisper + sounddevice). Whisper runs on **CPU** by default (portable — don't switch to
CUDA unless the box has the cuBLAS libs). The first time the mic is used it downloads the STT
model (~small.en) once, so the very first utterance has a short lag; after that it's instant.

Action cheatsheet for `demo.act`:
- click → `{ action:"click", selector, note }`
- type → `{ action:"input", selector, value, note }`
- scroll → `{ action:"scroll", value:"down"|"up"|"top"|"bottom"|"<px>" }`
- navigate → `{ action:"navigate", value:"https://..." }`

## PLAY 3 — Just pictures (stills)

"take some pictures/screenshots of X" → `capture.crawl` `{ url }` (whole site, desktop+mobile,
light+dark) or `capture.rested` `{ urls:[...] }` for specific pages. CLI: `capturd shots ...`.
Returns an output folder. Deliver the shots (or the best few inline).

## STREAM INTO CHAT — don't go silent
They want to *watch it happen*, not get a wall of nothing then a file. As it runs:
- one line when the window comes up,
- the `frameBase64` images from `demo.act` (live), or a couple `demo.status` progress lines +
  a mid-run frame (agent),
- the finished MP4/GIF/stills at the end.
Keep the chatter tight — a picture and a short line beats a paragraph.

## VERIFY THE ARTIFACT — it's not done until you've seen it
Before saying "here's your video": confirm the file is real and right. Read a few frames of
the MP4 (ffmpeg extract at a couple timestamps) or open the export — is the zoom landing on
the thing they asked about, is it the flow they wanted? A path string is not proof. If the
agent wandered off the goal or a step is blank, fix it (`demo.regenerate` / `demo.trim` /
re-drive the bad step) before delivering. Report honestly: if a step broke, say so and say
what you did about it.

## Sellable by default
Nothing you generate bakes in the user's identity, keys, or payment info — anyone runs this
exact flow with their own env. Never hardcode a gateway key into a command you persist; it
lives in the host env.

## One-liners the user might say → what you do
- "turn on capturd and film the dashboard" → Play 1, agent mode, visible, mp4.
- "grab me pics of the pricing page" → Play 3, `capture.rested` on the pricing URL.
- "let me drive it by voice — I'll talk you through onboarding" → Play 2, live mode, mic on.
- "record while I click through onboarding" → Play 2, live mode.
- "make me a gif of the login" → Play 1, `format:"gif"`.
Never answer any of these with a question. Launch it.
