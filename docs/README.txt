MULTILINGUAL VIDEO STUDIO — ON-DEVICE AUTOMATIC TRANSCRIPTION (v2)

Features: choose video, capture its audio in real time using browser Web Audio,
transcribe locally with multilingual Whisper Tiny through Transformers.js / ONNX Runtime Web,
show timed captions over the video, edit start/end/text, export real SRT and project JSON.

Supported: Android Chrome and Windows Chrome/Edge where Web Audio, WASM and browser memory allow.
No paid API; no server uploads. The Whisper model downloads on first use from Hugging Face.
Choose source language Telugu/Hindi/English, or auto-detect. The caption-language selector
is informational in this version; translation is NOT implemented. Select original language
for transcription. Model accuracy varies substantially with accents, noise, and language.

Important limitations:
- Real-time audio capture means capture takes the video duration; then inference takes extra time.
- Keep page foreground and screen awake. Audio capture may stop in the background.
- Browser models can use 100s of MB RAM; Android may close the tab on low-memory phones.
- Some browsers/codecs may not expose video audio through Web Audio.
- The selected video must contain an audio track.
- Captions are sentence/chunk-level approximations, not word-perfect alignments.
- Browser storage/model cache may be evicted. First model download requires internet.
- 8-minute limit on mobile; 20-minute limit on desktop for this version.
- No voice cloning, translation, background-music separation or MP4 rendering yet.
- SRT is a text subtitle file; play it with video in VLC or another subtitle-capable player.

Deploy: replace files in existing GitHub repository /docs folder; keep /docs/.nojekyll.
GitHub Pages source: main /docs. Refresh or reopen app after deployment.
