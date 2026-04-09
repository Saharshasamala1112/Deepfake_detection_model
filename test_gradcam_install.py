try:
    from pytorch_grad_cam import GradCAM
    print('Grad-CAM available')
except ImportError as e:
    print(f'Grad-CAM not available: {e}')