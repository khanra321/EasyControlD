import os
import subprocess
import sys
import mediapipe

def build():
    print("Building EasyControlD Desktop App (Fixing MediaPipe & Icon)...")
    
    # 1. MediaPipe library path khuje ber kora jate model files gulo EXE te thake
    mediapipe_path = os.path.dirname(mediapipe.__file__)
    
    # 2. Path settings for Windows (Source;Destination)
    icon_path = "gesture.png"
    icon_data = "gesture.png;."
    
    # MediaPipe er puro folder ta data hisebe add kora hocche (Khub dorkari)
    mediapipe_data = f"{mediapipe_path};mediapipe"
    
    command = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        f"--add-data={icon_data}",
        f"--add-data={mediapipe_data}", # MediaPipe error fix korbe
        f"--icon={icon_path}",          # EXE file er logo
        "--name=EasyControlD",
        "--clean",
        "upvb_simple.py"
    ]
    
    try:
        # Pillow install kora thakle PNG auto ICO te convert korbe PyInstaller
        subprocess.check_call(command)
        print("\nSUCCESS: Apnar EXE file 'dist' folder a toiri hoyeche.")
    except Exception as e:
        print(f"\nERROR: Build failed! {e}")

if __name__ == "__main__":
    # Dorkari libraries check
    libraries = ["pyinstaller", "Pillow", "mediapipe"]
    for lib in libraries:
        try:
            if lib == "Pillow":
                import PIL
            else:
                __import__(lib)
        except ImportError:
            print(f"{lib} install kora nei. Install kora hocche...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
        
    build()
