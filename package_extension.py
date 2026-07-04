import os
import zipfile

def package_extension():
    archive_name = 'tweet2skill-extension.zip'
    
    # Files and folders to explicitly include in the zip
    includes = [
        'manifest.json',
        'popup.html',
        'popup.css',
        'popup.js',
        'auth.js',
        'background.js',
        'icons'
    ]
    
    print(f"Creating {archive_name}...")
    
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in includes:
            if not os.path.exists(item):
                print(f"Warning: {item} does not exist in current directory.")
                continue
                
            if os.path.isdir(item):
                for root, dirs, files in os.walk(item):
                    for file in files:
                        filepath = os.path.join(root, file)
                        # Exclude system files or hidden files
                        if file.startswith('.') or file.endswith('.svg'):
                            # Wait, we can include svg if we want, but let's keep only pngs if desired,
                            # actually icons/icon.svg is useful to keep. Let's include everything in icons/ except hidden files
                            pass
                        if file.startswith('.'):
                            continue
                        zipf.write(filepath, filepath)
                        print(f"  Added: {filepath}")
            else:
                zipf.write(item, item)
                print(f"  Added: {item}")
                
    print(f"\nSuccess! Extension has been packaged into: {archive_name}")
    print("This ZIP file is ready to be uploaded to the Chrome Developer Dashboard.")

if __name__ == '__main__':
    package_extension()
