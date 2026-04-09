try:
    from pytorch_grad_cam import GradCAM
    print("pytorch-grad-cam is available")
except ImportError as e:
    print(f"pytorch-grad-cam not available: {e}")