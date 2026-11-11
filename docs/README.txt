MULTILINGUAL VIDEO STUDIO — PWA PROTOTYPE

This ZIP contains a mobile-installable PWA prototype, not a completed AI video-captioning/dubbing product.

CURRENTLY WORKING:
- Responsive mobile web interface
- PWA manifest and service worker
- Install prompt where supported
- Select and preview a video locally in the browser
- Add/edit/delete sample subtitle lines
- Export SRT and project JSON

NOT YET IMPLEMENTED:
- On-device Whisper transcription
- Telugu/Hindi/English AI translation
- Voice cloning or TTS
- Music/dialogue separation
- Final MP4 subtitle rendering
These require compatible, tested on-device model builds and platform-specific performance work.

HOW TO TEST:
1. Extract this ZIP on a computer.
2. Serve the folder over HTTPS (or localhost for local testing). Do not open index.html as a file.
3. For quick local testing with Python:
   python -m http.server 8000
   Then open http://localhost:8000 on the same computer.
4. For phone installation, deploy the folder to an HTTPS static host, or serve it from a secure local network setup.
5. On Android Chrome: browser menu → Install app / Add to Home screen.
6. On iPhone Safari: Share → Add to Home Screen.

IMPORTANT:
- PWA installation requires HTTPS, except localhost development.
- This prototype previews selected video locally; it does not upload it to a server.
- Browser support and local file storage vary by device.
- Do not use sensitive/private videos on an untrusted hosting provider.
