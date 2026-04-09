import subprocess
import sys

try:
    # Try to install grad-cam, which provides the pytorch_grad_cam import path
    result = subprocess.run([sys.executable, "-m", "pip", "install", "grad-cam"],
                          capture_output=True, text=True, timeout=60)

    if result.returncode == 0:
        print("Successfully installed grad-cam")
    else:
        print(f"Failed to install grad-cam: {result.stderr}")

    # Test the import
    from pytorch_grad_cam import GradCAM
    print("grad-cam is working correctly")

except Exception as e:
    print(f"Error: {e}")