# TrackNet Next Steps

The TrackNet replay path is scaffolded, but it is not ready for inference until
real local model assets are added.

Required artifacts:

1. Get TrackNet architecture code.
   - TrackNet / TrackNetV2 / TrackNetV3 / TrackNetV4 architecture must match
     the pretrained weights.
   - A state_dict alone is not runnable.

2. Get compatible pretrained weights.
   - Accepted local filenames include:
     - `models/tracknet/weights/tracknet.pt`
     - `models/tracknet/weights/tracknet.pth`
     - `models/tracknet/weights/tracknetv2.pt`
     - `models/tracknet/weights/tracknetv2.pth`
     - `models/tracknet/weights/tracknetv3.pt`
     - `models/tracknet/weights/tracknetv3.pth`
     - `models/tracknet/weights/tracknetv4.pt`
     - `models/tracknet/weights/tracknetv4.pth`

3. Ensure the adapter knows the model input contract.
   - input frame count;
   - image size;
   - normalization;
   - channel layout;
   - batch layout.

4. Ensure the adapter knows the output decode contract.
   - heatmap peak decode, or
   - coordinate output decode.

5. Run:
   `python scripts/check_tracknet_integration.py`

6. If ready, run:
   `python scripts/run_tracknet_replay_pipeline.py`

Important:
  Do not download huge weights automatically.
  Do not commit model weights.
  Do not fake TrackNet outputs.
  Do not fall back to YOLO/HSV in the TrackNet replay path.
