# Local SAM/SAM2 Weights

This folder is for optional local SAM assets used by the experimental
SAM-assisted replay path.

TrackNet remains the preferred primary path for tennis ball tracking. SAM is a
segmentation/prompting tool and should not be expected to solve fast tennis
ball tracking alone.

Large model files must not be committed to Git.

Accepted local paths:

- `models/sam/weights/sam.pt`
- `models/sam/weights/sam.pth`
- `models/sam/weights/sam_vit_b.pth`
- `models/sam/weights/sam_vit_l.pth`
- `models/sam/weights/sam_vit_h.pth`
- `models/sam2/weights/sam2.pt`
- `models/sam2/weights/sam2.pth`
- `models/sam2/checkpoints/`

SAM-assisted tracking requires a trusted ball seed point near the event
window. It must not invent ball positions when no seed exists.
