# Local TrackNet Weights

This folder is for local TrackNet / TrackNetV2 / TrackNetV3 / TrackNetV4 assets.

Large model files must not be committed to Git.

Put weights in:

  models/tracknet/weights/

Accepted names:

  tracknet.pt
  tracknet.pth
  tracknetv2.pt
  tracknetv2.pth
  tracknetv3.pt
  tracknetv3.pth
  tracknetv4.pt
  tracknetv4.pth

Then run:

  python scripts/check_tracknet_integration.py

If the check reports that weights are present but architecture is missing, a
concrete TrackNet model class or inference wrapper still needs to be wired into
src/tennis_vision/model_adapters/tracknet_adapter.py.
