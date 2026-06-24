#!/usr/bin/env python3
import sys, os, subprocess, platform, shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IS_WIN = platform.system() == "Windows"
PATH_SEP = ";" if IS_WIN else ":"


def find_cmd(name):
    return shutil.which(name)


def run(cmd, cwd=None, env=None):
    subprocess.run(cmd, check=True, cwd=cwd, env=env)


def check_go():
    go = find_cmd("go")
    if not go:
        print("ERROR: Go not found. Install from https://go.dev/dl/")
        sys.exit(1)
    print(f"  Go: {go}")
    return go


def ensure_gomobile(go):
    gomobile = find_cmd("gomobile")
    if not gomobile:
        print("  Installing gomobile...")
        run([go, "install", "golang.org/x/mobile/cmd/gomobile@latest"])
        gomobile = find_cmd("gomobile")
        if not gomobile:
            gopath = subprocess.check_output([go, "env", "GOPATH"]).decode().strip()
            gomobile = os.path.join(gopath, "bin", "gomobile" + (".exe" if IS_WIN else ""))
        if not os.path.isfile(gomobile):
            print("ERROR: gomobile not found after install")
            sys.exit(1)
    print(f"  gomobile: {gomobile}")
    return gomobile


def ensure_wails(go):
    wails = find_cmd("wails")
    if not wails:
        print("  Installing Wails CLI...")
        run([go, "install", "github.com/wailsapp/wails/v2/cmd/wails@latest"])
        wails = find_cmd("wails")
        if not wails:
            gopath = subprocess.check_output([go, "env", "GOPATH"]).decode().strip()
            wails = os.path.join(gopath, "bin", "wails" + (".exe" if IS_WIN else ""))
        if not os.path.isfile(wails):
            print("ERROR: Wails CLI not found after install")
            sys.exit(1)
    print(f"  Wails: {wails}")
    return wails


def build_desktop():
    print("=== Building Desktop ===")
    go = check_go()
    wails = ensure_wails(go)
    os.chdir(SCRIPT_DIR)
    print("  go mod tidy...")
    run([go, "mod", "tidy"])
    print("  wails build...")
    run([wails, "build"])
    bin_dir = os.path.join(SCRIPT_DIR, "build", "bin")
    if os.path.isdir(bin_dir):
        for f in os.listdir(bin_dir):
            fp = os.path.join(bin_dir, f)
            if os.path.isfile(fp):
                print(f"  Binary: {fp}")
    print("=== Desktop build OK ===")


def build_android():
    print("=== Building Android APK ===")
    android_dir = os.path.join(SCRIPT_DIR, "for_android")
    if not os.path.isdir(android_dir):
        print("ERROR: for_android/ not found")
        sys.exit(1)

    jdk_base = os.path.join(android_dir, "jdk")
    jdk_list = [d for d in os.listdir(jdk_base) if d.startswith("jdk-17")] if os.path.isdir(jdk_base) else []
    if not jdk_list:
        print("ERROR: JDK 17 not found in for_android/jdk/")
        sys.exit(1)
    jdk_home = os.path.join(jdk_base, jdk_list[0])

    sdk_dir = os.path.join(android_dir, "android-sdk")
    if not os.path.isdir(sdk_dir):
        print("ERROR: Android SDK not found in for_android/android-sdk/")
        sys.exit(1)

    env = os.environ.copy()
    env["JAVA_HOME"] = jdk_home
    env["ANDROID_HOME"] = sdk_dir
    env["ANDROID_SDK_ROOT"] = sdk_dir
    path_add = os.path.join(jdk_home, "bin") + PATH_SEP + os.path.join(sdk_dir, "platform-tools")
    env["PATH"] = path_add + PATH_SEP + env["PATH"]

    go = check_go()
    gomobile = ensure_gomobile(go)

    os.chdir(android_dir)
    print("[1/4] go mod tidy...")
    run([go, "mod", "tidy"], env=env)

    print("[2/4] Copying frontend to Android assets...")
    web_dir = os.path.join(android_dir, "android", "ymusic", "app", "src", "main", "assets", "web")
    if os.path.isdir(web_dir):
        shutil.rmtree(web_dir)
    shutil.copytree(os.path.join(SCRIPT_DIR, "frontend"), web_dir)

    print("[3/4] gomobile bind...")
    aar_path = os.path.join(android_dir, "android", "ymusic", "app", "libs", "ymobile.aar")
    os.makedirs(os.path.dirname(aar_path), exist_ok=True)
    run([gomobile, "bind", "-target=android", "-androidapi=24", "-o", aar_path, "ymusic/mobile"], env=env)

    print("[4/4] Gradle APK...")
    gradle_project = os.path.join(android_dir, "android", "ymusic")
    gradlew = "gradlew.bat" if IS_WIN else "gradlew"
    gradlew_path = os.path.join(gradle_project, gradlew)
    if os.path.isfile(gradlew_path):
        run([gradlew_path, "assembleRelease"], cwd=gradle_project, env=env)
    else:
        print(f"ERROR: {gradlew_path} not found")
        sys.exit(1)

    apk_path = os.path.join(gradle_project, "app", "build", "outputs", "apk", "release", "app-release.apk")
    if os.path.isfile(apk_path):
        size_mb = os.path.getsize(apk_path) / 1048576
        print(f"  APK: {apk_path} ({size_mb:.2f} MB)")
    print("=== Android build OK ===")


def help():
    print("YMusic Build Script")
    print()
    print("Usage: python build.py <argument>")
    print()
    print("Arguments:")
    print("  -Desktop    Build desktop app  (Wails, for Windows/Linux)")
    print("  -Android    Build Android APK  (requires for_android/ toolchain)")
    print("  -h, -help   Show this help")
    print()
    print("Dependencies are installed automatically (Go, Wails, gomobile).")


def main():
    args = [a.lower() for a in sys.argv[1:]]
    if not args or "-h" in args or "-help" in args:
        help()
        return
    if "-desktop" in args:
        build_desktop()
    elif "-android" in args:
        build_android()
    else:
        print(f"Unknown argument: {sys.argv[1]}")
        help()
        sys.exit(1)


if __name__ == "__main__":
    main()
