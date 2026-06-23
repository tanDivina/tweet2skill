#!/usr/bin/env python3
import os
import sys
import json

def main():
    print("==================================================")
    print("   Tweet2Skill - Installer")
    print("==================================================")

    # 1. Determine local paths
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    launcher_path = os.path.join(workspace_dir, "save_skill.sh")

    if not os.path.exists(launcher_path):
        print(f"Error: Launcher script not found at {launcher_path}")
        sys.exit(1)

    # Make launcher and python scripts executable
    os.chmod(launcher_path, 0o755)
    os.chmod(os.path.join(workspace_dir, "save_skill.py"), 0o755)
    print("✓ Configured scripts to be executable.")

    # 2. Get Extension ID from command line or prompt
    extension_id = ""
    if len(sys.argv) > 1:
        extension_id = sys.argv[1].strip()
    else:
        print("\nTo continue, please load the extension folder in Chrome first:")
        print("  1. Go to chrome://extensions/")
        print("  2. Enable 'Developer mode' (top right toggle)")
        print("  3. Click 'Load unpacked' and select:")
        print(f"     {workspace_dir}")
        print("  4. Copy the Extension ID (looks like 'abcdefghijklmnopabcdefghijklmnop')")
        
        extension_id = input("\nEnter Extension ID: ").strip()

    if not extension_id or not extension_id.isalpha() or len(extension_id) != 32:
        print("Error: Invalid Extension ID format. It must be exactly 32 alphabetical characters.")
        sys.exit(1)

    # 3. Create host manifest file in the workspace
    manifest = {
        "name": "com.antigravity.linker",
        "description": "Bridge Chrome to Antigravity Skill Python Script",
        "path": launcher_path,
        "type": "stdio",
        "allowed_origins": [
            f"chrome-extension://{extension_id}/"
        ]
    }

    local_manifest_path = os.path.join(workspace_dir, "com.antigravity.linker.json")
    with open(local_manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"✓ Created local host manifest: {local_manifest_path}")

    # 4. Install manifest in Chrome's NativeMessagingHosts directory
    chrome_hosts_dir = os.path.expanduser(
        "~/Library/Application Support/Google/Chrome/NativeMessagingHosts"
    )
    os.makedirs(chrome_hosts_dir, exist_ok=True)

    target_manifest_path = os.path.join(chrome_hosts_dir, "com.antigravity.linker.json")
    with open(target_manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"✓ Installed Chrome host manifest to:\n  {target_manifest_path}")

    # 5. Output confirmation & logs location
    log_path = os.path.join(workspace_dir, "host.log")
    print("\n✓ Setup Complete! 🎉")
    print("--------------------------------------------------")
    print("Next Steps:")
    print("1. Click the Tweet2Skill extension in Chrome.")
    print("2. Open 'Settings' (top-right tab).")
    print("3. Enter your Gemini API key and Workspace Path, then click Save.")
    print("4. Try visiting any web page (or X/Twitter detail page).")
    print("5. Open the extension, select scope, and click 'Turn into Skill' or 'Turn into Rule'.")
    print(f"\nNote: If you run into issues, inspect logs at: {log_path}")
    print("==================================================")

if __name__ == "__main__":
    main()
