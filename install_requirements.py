import sys
import subprocess

def install(package):
    print(f"--- Installing {package} ---")
    try:
        # This forces the current Python to install the package
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully!\n")
    except Exception as e:
        print(f"❌ Failed to install {package}. Error: {e}\n")

# Install the 3 key libraries
print(f"Python Location: {sys.executable}\n")

install("numpy")
install("pandas")
install("sentence-transformers")

print("--- INSTALLATION COMPLETE: You are ready for Step 3! ---")