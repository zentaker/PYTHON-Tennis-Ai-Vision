# Local SAM2 Weights

This folder is for optional local SAM2 assets used by the experimental
SAM-assisted replay path.

Large model files must not be committed to Git.

Accepted local paths:

- `models/sam2/weights/sam2.pt`
- `models/sam2/weights/sam2.pth`
- `models/sam2/checkpoints/`

SAM2 support still needs a concrete video predictor wrapper before inference.
TrackNet remains the preferred primary path for tennis ball tracking.
