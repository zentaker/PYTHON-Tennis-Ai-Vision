# TrackNet Setup

WHY TRACKNET IS NEEDED
  The YOLO/HSV/local candidate baseline failed the full-rally replay feasibility
  test. Manual event timing was correct, but the local detector selected
  high-scoring false-positive blobs. Tennis ball tracking needs temporal
  context, not isolated color/motion detections.

WHAT FILES ARE NEEDED
  A compatible pretrained TrackNet, TrackNetV2, TrackNetV3, or TrackNetV4
  weight file.
  Accepted local formats for the current adapter:
  - .pt
  - .pth

WHERE TO PLACE WEIGHTS
  models/tracknet/weights/tracknet.pt
  models/tracknet/weights/tracknet.pth
  models/tracknet/weights/tracknetv2.pt
  models/tracknet/weights/tracknetv2.pth
  models/tracknet/weights/tracknetv3.pt
  models/tracknet/weights/tracknetv3.pth
  models/tracknet/weights/tracknetv4.pt
  models/tracknet/weights/tracknetv4.pth

ARCHITECTURE VS WEIGHTS VS ADAPTER
  Architecture code:
    The Python class that defines the TrackNet network.

  Weights:
    The trained parameters saved as .pt or .pth.

  Inference adapter:
    The wrapper that preprocesses a temporal clip, runs the model, and decodes
    heatmaps or coordinates into per-frame ball positions.

  All three pieces must match. A state_dict without architecture code is not
  enough to run inference.

CREATE THE FOLDER
  mkdir models\tracknet\weights

CHECK INTEGRATION
  python scripts/check_tracknet_integration.py

CHECK A SPECIFIC FILE
  python scripts/check_tracknet_integration.py --weights models/tracknet/weights/tracknet.pth

RUN THE PIPELINE
  python scripts/run_tracknet_replay_pipeline.py

RUN WITH EXPLICIT WEIGHTS
  python scripts/run_tracknet_replay_pipeline.py --tracknet-weights "PATH_TO_WEIGHTS"

EXPECTED OUTPUT CONTRACT
  The TrackNet path expects temporal clip input and per-frame ball output:
  - frame_index
  - ball_x
  - ball_y
  - confidence

CURRENT LIMITATION
  The project can now run a full PyTorch model file when the .pt/.pth contains
  the serialized model object and its forward method accepts one of the generic
  temporal clip layouts.

  If the weight file is a state_dict or framework-specific checkpoint, the
  matching TrackNet architecture wrapper is still required. The adapter will
  report architecture_missing instead of guessing.

GENERIC FULL-MODEL PATH
  For a full PyTorch model file, the adapter:
  - loads the model locally with PyTorch;
  - reads the manual rally range from video_01;
  - preprocesses clips as temporal tensors;
  - tries common TrackNet channel-stack and sequence tensor layouts;
  - decodes heatmap peaks or direct coordinate outputs into ball x/y rows.

  This path is best-effort because TrackNet variants differ. If the model uses
  custom preprocessing or output decoding, add a concrete wrapper rather than
  changing the generic path to guess.

REGISTRY
  configs/models/tracknet_registry.json lists known variants:
  - tracknet_v1
  - tracknet_v2
  - tracknet_v3
  - tracknet_v4
  - custom_tracknet

IMPORTANT RULES
  TrackNet is the primary replacement path for the failed YOLO/HSV baseline.
  Do not download huge weights automatically.
  Do not commit model weights.
  Do not fall back to YOLO/HSV in the TrackNet replay path.
  Do not fake ball positions.
