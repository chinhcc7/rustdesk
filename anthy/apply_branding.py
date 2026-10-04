#!/usr/bin/env python3
"""Apply AnThy Remote branding to a RustDesk source tree.

Run from the repository root (after `git checkout` with submodules):
    python3 anthy/apply_branding.py

Reads anthy/brand.json. Fails loudly if an expected string is not found,
so an upstream change never silently produces an un-branded build.
"""
import json
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

with open(os.path.join(HERE, "brand.json"), encoding="utf-8") as f:
    B = json.load(f)

APP = B["app_name"]
DISPLAY = B["display_name"]
COMPANY = B["company"]
SERVER = B["server"].strip()
KEY = B["key"].strip()
ANDROID_ID = B["android_id"].strip()

errors = []

if not re.fullmatch(r"[A-Za-z0-9-]+", APP):
    errors.append(f"app_name '{APP}' chi duoc dung chu, so va dau '-' (khong dau cach)")
if not SERVER:
    errors.append("brand.json: 'server' dang trong")
if not KEY:
    errors.append("brand.json: 'key' dang trong - hay dan public key cua server (id_ed25519.pub)")
if errors:
    for e in errors:
        print("LOI:", e)
    sys.exit(1)


def p(rel):
    return os.path.join(ROOT, rel)


def sub(rel, pairs, required=True):
    path = p(rel)
    with open(path, encoding="utf-8") as f:
        s = f.read()
    orig = s
    for old, new in pairs:
        if isinstance(old, re.Pattern):
            s, n = old.subn(new, s)
        else:
            n = s.count(old)
            s = s.replace(old, new)
        if n == 0 and required:
            errors.append(f"{rel}: khong tim thay '{old if isinstance(old, str) else old.pattern}'")
    if s != orig:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(s)
        print("patched", rel)


def copy(src, dst):
    shutil.copyfile(os.path.join(ASSETS, src), p(dst))
    print("copied ", dst)


# 1. Core config: app name, ID/relay server, server public key
sub("libs/hbb_common/src/config.rs", [
    (re.compile(r'(APP_NAME: RwLock<String> = RwLock::new\(")RustDesk("\.to_owned\(\)\))'),
     rf'\g<1>{APP}\g<2>'),
    (re.compile(r'pub const RENDEZVOUS_SERVERS: &\[&str\] = &\[[^\]]*\];'),
     f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{SERVER}"];'),
    (re.compile(r'pub const RS_PUB_KEY: &str = "[^"]*";'),
     f'pub const RS_PUB_KEY: &str = "{KEY}";'),
])

# 2. Windows executable metadata
sub("flutter/windows/runner/Runner.rc", [
    ('"Purslane Tech Pte. Ltd."', f'"{COMPANY}"'),
    ('"RustDesk Remote Desktop"', f'"{DISPLAY}"'),
    ('"ProductName", "RustDesk"', f'"ProductName", "{DISPLAY}"'),
    (re.compile(r'"Copyright © \d+ Purslane Tech Pte\. Ltd\. All rights reserved\."'),
     f'"Copyright (C) {COMPANY}"'),
])
sub("flutter/windows/runner/main.cpp", [('std::wstring app_name = L"RustDesk";',
                                         f'std::wstring app_name = L"{APP}";')])
sub("libs/portable/Cargo.toml", [
    ('ProductName = "RustDesk"', f'ProductName = "{DISPLAY}"'),
    ('FileDescription = "RustDesk Remote Desktop"', f'FileDescription = "{DISPLAY}"'),
    (re.compile(r'LegalCopyright = "[^"]*"'), f'LegalCopyright = "Copyright (C) {COMPANY}"'),
])
sub("Cargo.toml", [
    ('ProductName = "RustDesk"', f'ProductName = "{DISPLAY}"'),
    ('FileDescription = "RustDesk Remote Desktop"', f'FileDescription = "{DISPLAY}"'),
    (re.compile(r'LegalCopyright = "[^"]*"'), f'LegalCopyright = "Copyright (C) {COMPANY}"'),
], required=False)

# 3. Icons / logos (desktop)
for src, dst in [
    ("icon.png", "res/icon.png"),
    ("32.png", "res/32x32.png"),
    ("64.png", "res/64x64.png"),
    ("128.png", "res/128x128.png"),
    ("256.png", "res/128x128@2x.png"),
    ("icon.ico", "res/icon.ico"),
    ("tray-icon.ico", "res/tray-icon.ico"),
    ("icon.ico", "flutter/windows/runner/resources/app_icon.ico"),
    ("icon.png", "flutter/assets/icon.png"),
    ("logo.png", "flutter/assets/logo.png"),
    ("logo.png", "flutter/assets/logo_light.png"),
    ("logo_dark.png", "flutter/assets/logo_dark.png"),
]:
    copy(src, dst)

# 4. Android
sub("flutter/android/app/src/main/res/values/strings.xml",
    [('<string name="app_name">RustDesk</string>', f'<string name="app_name">{DISPLAY}</string>')])
sub("flutter/android/app/src/main/AndroidManifest.xml", [
    ('android:label="RustDesk"', f'android:label="{DISPLAY}"'),
    ('android:label="RustDesk Input"', f'android:label="{DISPLAY} Input"'),
])
sub("flutter/android/app/build.gradle",
    [('applicationId "com.carriez.flutter_hbb"', f'applicationId "{ANDROID_ID}"')])
for d in ("mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"):
    for n in ("ic_launcher", "ic_launcher_round", "ic_launcher_foreground", "ic_stat_logo"):
        copy(f"android/mipmap-{d}/{n}.png",
             f"flutter/android/app/src/main/res/mipmap-{d}/{n}.png")

if errors:
    print("\n".join("LOI: " + e for e in errors))
    sys.exit(1)
print(f"\nOK - da gan thuong hieu {DISPLAY} ({APP}), server {SERVER}")
