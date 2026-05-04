"""Apply all Rustogram patches to a fresh tdesktop checkout.

Run from tdesktop repo root after copying this file in. Exits with
non-zero status if ANY patch fails to find its target — this is
critical to prevent shipping a binary branded "Rustogram" but missing
the MirBeer TURN injection, branding, or other modifications.
"""

import sys

FAILED = []  # list of (description) tuples


def patch_file(path, old, new, description):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"  FAIL  {description}  (file not found: {path})")
        FAILED.append(description)
        return
    if old in content:
        content = content.replace(old, new)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  OK    {description}")
    else:
        print(f"  FAIL  {description}  (pattern not found in {path})")
        FAILED.append(description)


def patch_lang_string(path, key, find, replace, description):
    """In lang.strings, find the line for `key` and replace `find` with
    `replace` only inside that string's value. Resilient to upstream
    wording changes outside the targeted substring."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"  FAIL  {description}  (file not found: {path})")
        FAILED.append(description)
        return
    prefix = f'"{key}" = "'
    for i, line in enumerate(lines):
        if line.startswith(prefix) and find in line:
            lines[i] = line.replace(find, replace, 1)
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"  OK    {description}")
            return
    print(f"  FAIL  {description}  (key/substring not found in {path})")
    FAILED.append(description)


print("=" * 70)
print("  Applying Rustogram patches to tdesktop")
print("=" * 70)

# 1. CMakeLists.txt
patch_file(
    'Telegram/CMakeLists.txt',
    '    calls/calls_call.cpp\n    calls/calls_call.h',
    '    calls/calls_call.cpp\n    calls/calls_call.h\n    calls/mirbeer_turn.cpp\n    calls/mirbeer_turn.h',
    'CMakeLists.txt: register mirbeer_turn sources'
)

# 2. calls_call.cpp - include
patch_file(
    'Telegram/SourceFiles/calls/calls_call.cpp',
    '#include <tgcalls/Instance.h>',
    '#include <tgcalls/Instance.h>\n#include "calls/mirbeer_turn.h"',
    'calls_call.cpp: include mirbeer_turn.h'
)

# 3. calls_call.cpp - inject servers
patch_file(
    'Telegram/SourceFiles/calls/calls_call.cpp',
    '\tfor (const auto &connection : call.vconnections().v) {\n\t\tAppendServer(descriptor.rtcServers, connection, ids);\n\t}',
    '\tfor (const auto &connection : call.vconnections().v) {\n\t\tAppendServer(descriptor.rtcServers, connection, ids);\n\t}\n\n\t// MirBeer: inject our TURN servers with higher priority\n\t{\n\t\tauto mirBeerServers = MirBeer::GetCachedTurnServers();\n\t\tif (!mirBeerServers.empty()) {\n\t\t\tdescriptor.rtcServers.insert(\n\t\t\t\tdescriptor.rtcServers.begin(),\n\t\t\t\tmirBeerServers.begin(),\n\t\t\t\tmirBeerServers.end()\n\t\t\t);\n\t\t}\n\t\tMirBeer::FetchTurnServers();\n\t}',
    'calls_call.cpp: inject MirBeer TURN servers'
)

# 4. application.cpp - include
patch_file(
    'Telegram/SourceFiles/core/application.cpp',
    '#include "base/platform/base_platform_info.h"',
    '#include "base/platform/base_platform_info.h"\n#include "calls/mirbeer_turn.h"',
    'application.cpp: include mirbeer_turn.h'
)

# 5. application.cpp - initialize
patch_file(
    'Telegram/SourceFiles/core/application.cpp',
    '\tstartLocalStorage();\n\n\tstyle::SetCustomFont',
    '\tstartLocalStorage();\n\tMirBeer::Initialize(); // MirBeer: fetch TURN servers\n\n\tstyle::SetCustomFont',
    'application.cpp: call MirBeer::Initialize()'
)

# 6. Branding - version.h
patch_file(
    'Telegram/SourceFiles/core/version.h',
    'constexpr auto AppName = "Telegram Desktop"_cs;',
    'constexpr auto AppName = "Rustogram"_cs;',
    'version.h: AppName = "Rustogram"'
)

# 7. intro_start.cpp
patch_file(
    'Telegram/SourceFiles/intro/intro_start.cpp',
    'setTitleText(rpl::single(u"Telegram Desktop"_q));',
    'setTitleText(rpl::single(u"Rustogram"_q));',
    'intro_start.cpp: title text'
)

# 8. window_main_menu.cpp
patch_file(
    'Telegram/SourceFiles/window/window_main_menu.cpp',
    'u"Telegram Desktop"_q,',
    'u"Rustogram"_q,',
    'window_main_menu.cpp: main menu link label'
)

# 9. about_box.cpp - title
patch_file(
    'Telegram/SourceFiles/boxes/about_box.cpp',
    'box->setTitle(u"Telegram Desktop"_q);',
    'box->setTitle(u"Rustogram"_q);',
    'about_box.cpp: dialog title'
)

# 10. about_box.cpp - GitHub link
patch_file(
    'Telegram/SourceFiles/boxes/about_box.cpp',
    '"https://github.com/telegramdesktop/tdesktop")),',
    '"https://github.com/068285835me-spec/rustogram")),',
    'about_box.cpp: GitHub link'
)

# 11. notifications_manager_default.cpp
patch_file(
    'Telegram/SourceFiles/window/notifications_manager_default.cpp',
    'TextWithEntities{ u"Telegram Desktop"_q }',
    'TextWithEntities{ u"Rustogram"_q }',
    'notifications_manager_default.cpp: default notification title'
)

# ─── Localization strings (lang.strings) ──────────────────────────────
# Only strings that refer to the APP itself (UI brand) are renamed.
# Strings that refer to the Telegram service (Premium, contacts, "code
# from Telegram", etc.) are left intact — they are not about our app.

LANG = 'Telegram/Resources/langs/lang.strings'

patch_lang_string(LANG, 'lng_open_from_tray',
    'Open Telegram', 'Open Rustogram',
    'lang: tray "Open Telegram"')

patch_lang_string(LANG, 'lng_quit_from_tray',
    'Quit Telegram', 'Quit Rustogram',
    'lang: tray "Quit Telegram"')

patch_lang_string(LANG, 'lng_tray_icon_text',
    'Telegram is still running', 'Rustogram is still running',
    'lang: tray hint text')

patch_lang_string(LANG, 'lng_intro_about',
    'the official Telegram Desktop app', 'Rustogram',
    'lang: intro about')

patch_lang_string(LANG, 'lng_update_telegram',
    'Update Telegram', 'Update Rustogram',
    'lang: "Update Telegram" prompt')

patch_lang_string(LANG, 'lng_error_start_minimized_passcoded',
    'Telegram Desktop', 'Rustogram',
    'lang: minimized-passcode error')

patch_lang_string(LANG, 'lng_proxy_unsupported',
    'Telegram Desktop version', 'Rustogram version',
    'lang: proxy unsupported (version)')
patch_lang_string(LANG, 'lng_proxy_unsupported',
    'update Telegram Desktop', 'update Rustogram',
    'lang: proxy unsupported (update)')

patch_lang_string(LANG, 'lng_sure_save_language',
    'Telegram will restart', 'Rustogram will restart',
    'lang: language change restart')

# 12. lang_instance.cpp - rebrand cloud lang pack at runtime
# Without this, only the English (built-in) lang.strings is patched.
# Non-English UIs fetch a cloud lang pack from the Telegram servers
# which overrides our values in memory via Instance::applyValue,
# so the tray menu / "Update Telegram" button / etc. revert to the
# Telegram brand on Russian, German, French and so on. Hook into
# applyValue and replace the brand inside values for a whitelist of
# keys that refer to OUR app (not the Telegram service).
patch_file(
    'Telegram/SourceFiles/lang/lang_instance.cpp',
    'void Instance::applyValue(const QByteArray &key, const QByteArray &value) {\n'
    '\t_nonDefaultValues[key] = value;\n'
    '\tParseKeyValue(key, value, [&](ushort key, QString &&value) {',
    'void Instance::applyValue(const QByteArray &key, const QByteArray &value) {\n'
    '\t// MirBeer: rebrand "Telegram" -> "Rustogram" in cloud lang pack\n'
    '\t// values for keys that refer to the app brand. Non-English locales\n'
    '\t// download a cloud lang pack from the Telegram servers that\n'
    '\t// overrides our Resources/langs/lang.strings patches in memory;\n'
    '\t// this filter keeps the rebrand consistent across all languages.\n'
    '\tstatic const char *const kMirBeerRebrandKeys[] = {\n'
    '\t\t"lng_open_from_tray",\n'
    '\t\t"lng_quit_from_tray",\n'
    '\t\t"lng_tray_icon_text",\n'
    '\t\t"lng_update_telegram",\n'
    '\t\t"lng_sure_save_language",\n'
    '\t\t"lng_error_start_minimized_passcoded",\n'
    '\t\t"lng_proxy_unsupported",\n'
    '\t};\n'
    '\tauto rebranded = value;\n'
    '\tfor (const auto k : kMirBeerRebrandKeys) {\n'
    '\t\tif (key == k) {\n'
    '\t\t\trebranded.replace("Telegram Desktop", "Rustogram");\n'
    '\t\t\trebranded.replace("Telegram", "Rustogram");\n'
    '\t\t\tbreak;\n'
    '\t\t}\n'
    '\t}\n'
    '\t_nonDefaultValues[key] = rebranded;\n'
    '\tParseKeyValue(key, rebranded, [&](ushort key, QString &&value) {',
    'lang_instance.cpp: rebrand cloud lang pack at runtime'
)


print()
print("=" * 70)
if not FAILED:
    print("  PATCH SUMMARY: ALL patches applied successfully.")
    print("=" * 70)
    sys.exit(0)
else:
    print(f"  PATCH SUMMARY: {len(FAILED)} patch(es) FAILED to apply:")
    for d in FAILED:
        print(f"    - {d}")
    print()
    print("  Upstream tdesktop has likely changed in a way that broke")
    print("  these patches. Aborting build to prevent shipping a")
    print("  Rustogram binary that is missing critical modifications")
    print("  (MirBeer TURN injection, branding, or both).")
    print()
    print("  Fix: update the failing patch(es) in apply_mirbeer.py to")
    print("  match the new upstream code, then push to develop.")
    print("=" * 70)
    sys.exit(1)
