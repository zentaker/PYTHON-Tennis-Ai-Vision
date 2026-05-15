# Labeling Outputs

This folder is for exported files from local labeling tools.

Recommended workflow:

1. Open `tools/labeling_editor/index.html`.
2. Load a local video.
3. Add timecode labels.
4. Export JSON into this folder or another local folder.
5. Convert the JSON into Stage 8.2-compatible labels:

```powershell
python scripts\convert_timecode_labels.py --input outputs\labeling\video_01_labels.json --output-dir outputs\timeline\stage_8_2_event_labels --fps 60
```

Do not commit large videos or generated media artifacts.
