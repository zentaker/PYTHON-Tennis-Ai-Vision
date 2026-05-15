# TrackNet Model Requirements

Required:

- TrackNet architecture code or compatible model class
- Pretrained weights
- Input preprocessing details
- Output decoding details
- Expected frame sequence length
- Heatmap-to-coordinate logic
- License/source notes

Accepted weights paths:

- models/tracknet/weights/tracknet.pt
- models/tracknet/weights/tracknet.pth
- models/tracknet/weights/tracknetv2.pt
- models/tracknet/weights/tracknetv2.pth
- models/tracknet/weights/tracknetv3.pt
- models/tracknet/weights/tracknetv3.pth
- models/tracknet/weights/tracknetv4.pt
- models/tracknet/weights/tracknetv4.pth

Notes:

- Do not commit large weights.
- Do not fake inference if the architecture and weights do not match.
- The replay pipeline requires per-frame ball coordinates or heatmaps that can
  be decoded into coordinates.
