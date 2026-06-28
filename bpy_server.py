import sys
import os
import site

# Fix for Blender ignoring user site-packages
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.server.bpy_server import run

def main():
    run()

if __name__ == "__main__":
    main()
