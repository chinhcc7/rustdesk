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
LANGS = [x.strip() for x in B.get("languages", [])]

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

# 5. Language list: only keep the languages listed in brand.json "languages"
if LANGS:
    path = p("src/lang.rs")
    with open(path, encoding="utf-8") as f:
        s = f.read()
    m = re.search(r'pub const LANGS: &\[\(&str, &str\)\] = &\[(.*?)\n\];', s, re.S)
    if not m:
        errors.append("src/lang.rs: khong tim thay danh sach LANGS")
    else:
        avail = dict(re.findall(r'\("([^"]+)",\s*"([^"]+)"\)', m.group(1)))
        missing = [c for c in LANGS if c not in avail]
        if missing:
            errors.append(f"brand.json languages: ma ngon ngu khong ton tai {missing}")
        else:
            body = "".join(f'\n    ("{c}", "{avail[c]}"),' for c in LANGS)
            s = s[:m.start(1)] + body + s[m.end(1):]
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(s)
            print("patched src/lang.rs ->", ", ".join(LANGS))

# 6. Language button next to the Settings button (desktop + Android)
if B.get("language_button", True):
    shutil.copyfile(os.path.join(HERE, "flutter", "anthy_lang_button.dart"),
                    p("flutter/lib/desktop/widgets/anthy_lang_button.dart"))
    print("copied  flutter/lib/desktop/widgets/anthy_lang_button.dart")
    sub("flutter/lib/desktop/pages/desktop_tab_page.dart", [
        ("import 'package:flutter_hbb/desktop/widgets/tabbar_widget.dart';",
         "import 'package:flutter_hbb/desktop/widgets/tabbar_widget.dart';\n"
         "import 'package:flutter_hbb/desktop/widgets/anthy_lang_button.dart';"),
        (re.compile(r"tail: Offstage\((.*?isClose: false,\s*\),)\s*\),", re.S),
         r"tail: Row(mainAxisSize: MainAxisSize.min, children: [const AnthyLangButton(), Offstage(\1)]),"),
    ])
    sub("flutter/lib/mobile/pages/home_page.dart", [
        ("actions: _pages.elementAt(_selectedIndex).appBarActions,",
         "actions: [IconButton(icon: const Icon(Icons.translate), "
         "tooltip: translate('Language'), "
         "onPressed: () => showLanguageSettings(gFFI.dialogManager)), "
         "..._pages.elementAt(_selectedIndex).appBarActions],"),
    ])

# 7. Company name + hotline at the bottom of the main screen (desktop + Android)
HOTLINE = B.get("hotline", "").strip()
if HOTLINE:
    def dart_str(v):
        return v.replace("\\", "\\\\").replace("'", "\\'").replace("$", "\\$")
    with open(os.path.join(HERE, "flutter", "anthy_company_info.dart"), encoding="utf-8") as f:
        src = f.read()
    src = (src.replace("__COMPANY__", dart_str(B.get("company_display", COMPANY)))
              .replace("__HOTLINE__", dart_str(HOTLINE))
              .replace("__TAXCODE__", dart_str(B.get("tax_code", "").strip()))
              .replace("__WEBSITE__", dart_str(B.get("website", "").strip())))
    with open(p("flutter/lib/common/widgets/anthy_company_info.dart"), "w",
              encoding="utf-8", newline="") as f:
        f.write(src)
    print("wrote   flutter/lib/common/widgets/anthy_company_info.dart")
    sub("flutter/lib/desktop/pages/desktop_home_page.dart", [
        ("import 'package:flutter_hbb/common.dart';",
         "import 'package:flutter_hbb/common.dart';\n"
         "import 'package:flutter_hbb/common/widgets/anthy_company_info.dart';"),
        ("                Expanded(child: Container())\n",
         "                Expanded(child: Container()),\n"
         "                const AnthyCompanyInfo(),\n"),
    ])
    sub("flutter/lib/mobile/pages/home_page.dart", [
        ("import 'package:flutter/material.dart';",
         "import 'package:flutter/material.dart';\n"
         "import 'package:flutter_hbb/common/widgets/anthy_company_info.dart';"),
        ("body: _pages.elementAt(_selectedIndex),",
         "body: Column(children: [Expanded(child: _pages.elementAt(_selectedIndex)), const AnthyCompanyInfo()]),"),
    ])


# 8. Windows installer: rename the copied rustdesk.exe to <app_name>.exe on a fresh
#    install too (upstream only renames on update, so shortcuts and the service
#    would point at a missing <app_name>.exe)
sub("src/platform/windows.rs", [
    ('md \\"{path}\\"\n{copy_exe}\nreg add {subkey} /f\n',
     'md \\"{path}\\"\n{copy_exe}\n{rename_exe}\nreg add {subkey} /f\n'),
    ("        copy_exe = copy_exe_cmd(&src_exe, &exe, &path)?,\n"
     "        import_config = get_import_config(&exe),\n",
     "        copy_exe = copy_exe_cmd(&src_exe, &exe, &path)?,\n"
     "        rename_exe = rename_exe_cmd(&src_exe, &path)?,\n"
     "        import_config = get_import_config(&exe),\n"),
])

# 9. "Powered by" link + About page -> company info and website
WEBSITE = B.get("website", "").strip()
if WEBSITE:
    WEB_URL = WEBSITE if WEBSITE.startswith("http") else "https://" + WEBSITE
    WEB_LABEL = re.sub(r"^https?://", "", WEBSITE).rstrip("/")
    # top-left "Powered by me" link on the desktop home page
    sub("flutter/lib/common.dart", [
        ("        launchUrl(Uri.parse('https://rustdesk.com'));\n      },\n      child: Opacity(",
         f"        launchUrl(Uri.parse('{WEB_URL}'));\n      }},\n      child: Opacity("),
        ('            translate("powered_by_me"),', f"            '{WEB_LABEL}',"),
    ])
    # Android: About section / dialog link
    sub("flutter/lib/mobile/pages/settings_page.dart", [
        ("'https://rustdesk.com/'", f"'{WEB_URL}'"),
        ("Text('rustdesk.com',", f"Text('{WEB_LABEL}',"),
    ])
if HOTLINE:
    # desktop Settings -> About: company info in the blue box, RustDesk credit kept small
    sub("flutter/lib/desktop/pages/desktop_setting_page.dart", [
        ("import 'package:flutter_hbb/common.dart';",
         "import 'package:flutter_hbb/common.dart';\n"
         "import 'package:flutter_hbb/common/widgets/anthy_company_info.dart';"),
        ("""                          Text(
                            'Copyright © ${DateTime.now().toString().substring(0, 4)} Purslane Tech Pte. Ltd.\\n$license',
                            style: const TextStyle(color: Colors.white),
                          ),
                          Text(
                            translate('Slogan_tip'),
                            style: TextStyle(
                                fontWeight: FontWeight.w800,
                                color: Colors.white),
                          )
""",
         """                          Text(
                            kAnthyCompany,
                            style: const TextStyle(
                                fontWeight: FontWeight.w800,
                                color: Colors.white),
                          ),
                          Text(
                            [
                              if (kAnthyTaxCode.isNotEmpty) 'MST: $kAnthyTaxCode',
                              'Hotline: $kAnthyHotline',
                              if (kAnthyWebsite.isNotEmpty) 'Web: $kAnthyWebsite',
                            ].join('\\n'),
                            style: const TextStyle(color: Colors.white),
                          ).marginOnly(top: 4),
                          Text(
                            'Based on RustDesk - Copyright © ${DateTime.now().toString().substring(0, 4)} Purslane Tech Pte. Ltd.\\n$license',
                            style: const TextStyle(
                                color: Colors.white70, fontSize: 11),
                          ).marginOnly(top: 10),
"""),
    ])
    if WEBSITE:
        sub("flutter/lib/desktop/pages/desktop_setting_page.dart", [
            ("launchUrlString('https://rustdesk.com');", f"launchUrlString('{WEB_URL}');"),
        ])


# 10. Status bar: replace "set up your own server" tip with hotline + website
if HOTLINE and WEBSITE:
    sub("flutter/lib/desktop/pages/connection_page.dart", [
        ("onTap: onUsePublicServerGuide,", f"onTap: () => launchUrlString('{WEB_URL}'),"),
        ("translate('setup_server_tip'),", f"'Hotline: {dart_str(HOTLINE)} · {dart_str(WEB_LABEL)}',"),
    ])


# 11. Android: Accessibility prominent disclosure (Google Play User Data policy)
#     + rename the "RustDesk Input" service name in the permission tips
A11Y = {
    "en": ("{app} uses the Android Accessibility service only to carry out the taps, swipes and key presses sent by the technician you allow to connect, so they can control this device remotely. When text is typed, it is entered into the field you have selected. {app} does not use Accessibility to collect, store or share your personal data or screen content. You can turn this permission off at any time in Settings.",
           "Agree and open settings"),
    "vi": ("{app} chỉ dùng dịch vụ Trợ năng (Accessibility) của Android để thực hiện các thao tác chạm, vuốt và gõ phím do kỹ thuật viên mà bạn cho phép kết nối gửi tới, giúp họ điều khiển thiết bị này từ xa. Khi gõ chữ, nội dung được nhập vào ô bạn đang chọn. {app} không dùng Trợ năng để thu thập, lưu trữ hay chia sẻ dữ liệu cá nhân hoặc nội dung màn hình của bạn. Bạn có thể tắt quyền này bất cứ lúc nào trong Cài đặt.",
           "Đồng ý và mở Cài đặt"),
    "cn": ("{app} 仅使用 Android 无障碍服务来执行您允许连接的技术人员发送的点按、滑动和按键操作，以便其远程控制本设备。输入文字时，内容会输入到您当前选中的输入框。{app} 不会使用无障碍服务收集、存储或分享您的个人数据或屏幕内容。您可以随时在设置中关闭此权限。",
           "同意并打开设置"),
    "ko": ("{app}은(는) 연결을 허용한 기술자가 보내는 탭, 스와이프, 키 입력을 실행하여 이 기기를 원격으로 제어할 수 있도록 Android 접근성 서비스만 사용합니다. 텍스트를 입력하면 선택한 입력란에 입력됩니다. {app}은(는) 접근성 서비스로 개인 정보나 화면 내용을 수집, 저장 또는 공유하지 않습니다. 설정에서 언제든지 이 권한을 끌 수 있습니다.",
           "동의하고 설정 열기"),
}
for code, (text, agree) in A11Y.items():
    rel = f"src/lang/{code}.rs"
    if not os.path.exists(p(rel)):
        continue
    with open(p(rel), encoding="utf-8") as f:
        s = f.read()
    s = s.replace("[RustDesk Input]", f"[{DISPLAY} Input]").replace("[RustDesk 입력]", f"[{DISPLAY} Input]")
    m = re.search(r'\n(\s*)\("android_input_permission_tip2",[^\n]*\n', s)
    if not m:
        errors.append(f"{rel}: khong tim thay android_input_permission_tip2")
        continue
    esc = lambda v: v.replace("\\", "\\\\").replace('"', '\\"')
    add = (f'{m.group(1)}("anthy_a11y_disclosure", "{esc(text.format(app=DISPLAY))}"),\n'
           f'{m.group(1)}("anthy_a11y_agree", "{esc(agree)}"),\n')
    s = s[:m.end()] + add + s[m.end():]
    with open(p(rel), "w", encoding="utf-8", newline="") as f:
        f.write(s)
    print("patched", rel, "(a11y disclosure)")

sub("flutter/lib/models/server_model.dart", [
    ('''          Text(translate("android_input_permission_tip1")),''',
     '''          Text(translate("anthy_a11y_disclosure")),
          const SizedBox(height: 10),
          Text(translate("android_input_permission_tip1")),'''),
    ('''        dialogButton("Open System Setting", onPressed: submit),''',
     '''        dialogButton("anthy_a11y_agree", onPressed: submit),'''),
])

if errors:
    print("\n".join("LOI: " + e for e in errors))
    sys.exit(1)
print(f"\nOK - da gan thuong hieu {DISPLAY} ({APP}), server {SERVER}")
