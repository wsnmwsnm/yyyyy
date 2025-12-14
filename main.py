# -*- coding: utf-8 -*-
import os
import re
import time
import zipfile
import shutil
from dateutil import parser
from typing import List, Dict
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.utils import platform
from kivy.graphics import Color, Rectangle
from plyer import filechooser

# ===================== 路径适配（内置文件版） =====================
if platform == 'android':
    BASE_DIR = '/sdcard/game_mod/'
    REPLACE_FILES_DIR = '/sdcard/game_mod/built_in_replace/'
    TEMP_EXTRACT_DIR = '/sdcard/game_mod/temp/'
    INPUT_FILE_PATH = ""
else:
    BASE_DIR = 'C:/game_mod/'
    REPLACE_FILES_DIR = 'C:/game_mod/built_in_replace/'
    TEMP_EXTRACT_DIR = 'C:/game_mod/temp/'
    INPUT_FILE_PATH = ""
    ASSETS_DIR = 'assets'

# 时间阈值
CUTOFF_TIME1 = parser.parse("2026-01-28 00:00:00").timestamp()
CUTOFF_TIME2 = parser.parse("2026-02-25 00:00:00").timestamp()


# ===================== 内置文件提取（修复jnius导入） =====================
def extract_built_in_files():
    built_in_files = ['a', 'b', 'c', 'd', 'e']
    os.makedirs(REPLACE_FILES_DIR, exist_ok=True)

    try:
        if platform == 'android':
            import jnius
            context = jnius.autoclass('org.kivy.android.PythonActivity').mActivity
            am = context.getAssets()
            for file_name in built_in_files:
                input_stream = am.open(file_name)
                output_path = os.path.join(REPLACE_FILES_DIR, file_name)
                with open(output_path, 'wb') as f:
                    f.write(input_stream.read())
                input_stream.close()
        else:
            for file_name in built_in_files:
                src_path = os.path.join(ASSETS_DIR, file_name)
                dst_path = os.path.join(REPLACE_FILES_DIR, file_name)
                if os.path.exists(src_path):
                    shutil.copyfile(src_path, dst_path)
        return True
    except Exception as e:
        print(f"内置文件提取失败：{e}")
        return False


# ===================== 工具函数 =====================
def unicode_escape(s: str) -> str:
    return s.encode('unicode_escape').decode('utf-8').replace('\\\\', '\\')


def match_file_by_size_and_content(dir_path: str, target_size: float, target_content: str, size_error=0.03) -> List[
    str]:
    """原文本模式匹配（用于JSON文件，不改动）"""
    matched_files = []
    min_size = target_size * (1 - size_error)
    max_size = target_size * (1 + size_error)
    try:
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(".json"):  # 仅匹配JSON
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        if min_size <= file_size <= max_size:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if target_content in content:
                                    matched_files.append(file_path)
                    except:
                        continue
    except:
        pass
    return matched_files


def match_binary_file_by_size_and_content(dir_path: str, target_size: float, target_content: str, size_error=0.03) -> \
List[str]:
    """新增：二进制模式匹配（仅匹配bin/lh/lmat）"""
    matched_files = []
    min_size = target_size * (1 - size_error)
    max_size = target_size * (1 + size_error)
    target_bytes = target_content.encode('utf-8')  # 关键词转字节串
    supported_ext = ['.bin', '.lh', '.lmat']  # 仅匹配这三种后缀
    try:
        for root, _, files in os.walk(dir_path):
            for file in files:
                if any(file.endswith(ext) for ext in supported_ext):
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        if min_size <= file_size <= max_size:
                            with open(file_path, 'rb') as f:
                                content = f.read()
                                if target_bytes in content:
                                    matched_files.append(file_path)
                    except:
                        continue
    except:
        pass
    return matched_files


def modify_json_file(file_path: str, modify_func):
    """原JSON修改函数（不改动）"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        content = ''.join(lines)
        new_content = modify_func(content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    except:
        return False


def modify_binary_file(file_path: str, modify_func):
    """新增：二进制文件修改函数"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        new_content = modify_func(content)
        with open(file_path, 'wb') as f:
            f.write(new_content)
        return True
    except:
        return False


def update_all_file_times(dir_path: str):
    current_time = time.time()
    try:
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                os.utime(file_path, (current_time, current_time))
    except:
        pass


def unzip_file(zip_path: str, extract_dir: str):
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        zipf.extractall(extract_dir)


def zip_dir(dir_path: str, zip_path: str):
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dir_path)
                zipf.write(file_path, arcname)


# ===================== 核心功能函数 =====================
def method1_modify_text(content: str) -> str:
    """原文本修改逻辑（用于JSON，不改动）"""
    content = re.sub(r'"cull":2,\s*"blend":0,\s*"srcBlend":1,\s*"dstBlend":0',
                     '"cull":2,\n                "blend":1,\n                "srcBlend":770,\n                "dstBlend":771',
                     content)
    content = re.sub(r'"renderQueue":2000,\s*"albedoIntensity":1',
                     '"renderQueue":3500,\n        "albedoIntensity":1.3', content)
    content = re.sub(r'"name":"specularColor",\s*"value":\[.*?]',
                     '"name":"specularColor",\n                "value":[0.5]', content)
    content = re.sub(r'"name":"albedoColor",\s*"value":\[.*?]',
                     '"name":"albedoColor",\n                "value":[0,0,0,0.25]', content)
    return content


def method1_modify_binary(content: bytes) -> bytes:
    """新增：二进制版method1修改（对应原文本逻辑的字节替换）"""
    # 原文本正则 → 二进制字节串替换（保持参数含义一致）
    content = re.sub(rb'"cull":2,\s*"blend":0,\s*"srcBlend":1,\s*"dstBlend":0',
                     rb'"cull":2,\n                "blend":1,\n                "srcBlend":770,\n                "dstBlend":771',
                     content)
    content = re.sub(rb'"renderQueue":2000,\s*"albedoIntensity":1',
                     rb'"renderQueue":3500,\n        "albedoIntensity":1.3', content)
    content = re.sub(rb'"name":"specularColor",\s*"value":\[.*?]',
                     rb'"name":"specularColor",\n                "value":[0.5]', content)
    content = re.sub(rb'"name":"albedoColor",\s*"value":\[.*?]',
                     rb'"name":"albedoColor",\n                "value":[0,0,0,0.25]', content)
    return content


def method2_modify_text(content: str) -> str:
    """原文本修改逻辑（用于JSON，不改动）"""
    content = re.sub(r'"name":"tintColor",\s*"value":\[.*?]',
                     '"name":"tintColor",\n                "value":[0,0,0,1]', content)
    return content


def method2_modify_binary(content: bytes) -> bytes:
    """新增：二进制版method2修改"""
    content = re.sub(rb'"name":"tintColor",\s*"value":\[.*?]',
                     rb'"name":"tintColor",\n                "value":[0,0,0,1]', content)
    return content


def method3_modify_text(content: str) -> str:
    """原文本修改逻辑（用于JSON，不改动）"""
    content = re.sub(r'"ambientColor":\[.*?]', '"ambientColor":[0]', content)
    return content


def method3_modify_binary(content: bytes) -> bytes:
    """新增：二进制版method3修改"""
    content = re.sub(rb'"ambientColor":\[.*?]', rb'"ambientColor":[0]', content)
    return content


def modify_perspective(extract_dir: str, perspective_config):
    """透视功能：改用二进制匹配+修改（仅bin/lh/lmat）"""
    if perspective_config["dust2"]:
        dust2_files1 = [(1003, '"name":"Dust2_Merge02_HD_01"'), (1003, '"name":"Dust2_Merge02_HD_03"'),
                        (1003, '"name":"Dust2_Merge02_HD_04"'), (1021, '"name":"Dust2_Merge02_HD_02"'),
                        (991, '"name":"Dust2_Merge01"')]
        for size, content in dust2_files1:
            files = match_binary_file_by_size_and_content(extract_dir, size, content)
            for file in files:
                modify_binary_file(file, method1_modify_binary)
        files2 = match_binary_file_by_size_and_content(extract_dir, 601, '"name":"m_sky_blue"')
        for file in files2:
            modify_binary_file(file, method2_modify_binary)
        files3 = match_binary_file_by_size_and_content(extract_dir, 441.93 * 1024, '"name":"PVP_dust2"')
        for file in files3:
            modify_binary_file(file, method3_modify_binary)

    if perspective_config["new_year_square"]:
        nye_files1 = [(1.02 * 1024, '"name":"PVP_NewYearSquare_Merge03"'),
                      (1.00 * 1024, '"name":"PVP_NewYearSquare_Merge04"')]
        for size, content in nye_files1:
            files = match_binary_file_by_size_and_content(extract_dir, size, content)
            for file in files:
                modify_binary_file(file, method1_modify_binary)
        files2 = match_binary_file_by_size_and_content(extract_dir, 607, '"name":"m_sky_night"')
        for file in files2:
            modify_binary_file(file, method2_modify_binary)
        files3 = match_binary_file_by_size_and_content(extract_dir, 262.02 * 1024, '"name":"PVP_NewYearSquare"')
        for file in files3:
            modify_binary_file(file, method3_modify_binary)

    if perspective_config["victory_square"]:
        files = match_binary_file_by_size_and_content(extract_dir, 1.01 * 1024,
                                                      '"name":"PVP_BP_ShengLiGuangChang_Merge"')
        for file in files:
            modify_binary_file(file, method1_modify_binary)

    if perspective_config["power_plant"]:
        files1 = match_binary_file_by_size_and_content(extract_dir, 1.01 * 1024, '"name":"PVP_BP_GongDianSuo"')
        for file in files1:
            modify_binary_file(file, method1_modify_binary)
        files2 = match_binary_file_by_size_and_content(extract_dir, 392.60 * 1024,
                                                       '"props":{"name":"PVP_BP_GongDianSuo"')
        for file in files2:
            modify_binary_file(file, lambda c: re.sub(rb'"name":"CloudSky","active":true',
                                                      rb'"name":"CloudSky","active":false', c))

    if perspective_config["desert_duel"]:
        files = match_binary_file_by_size_and_content(extract_dir, 1.01 * 1024, '"name":"PVPCF_Dust1v1_ComText"')
        for file in files:
            modify_binary_file(file, method1_modify_binary)

    if perspective_config["transport_ship"]:
        ship_files = [(1.03 * 1024, '"name":"CF_Ship_Container1024_New"'), (1.00 * 1024, '"name":"CF_Ship_Box"')]
        for size, content in ship_files:
            files = match_binary_file_by_size_and_content(extract_dir, size, content)
            for file in files:
                modify_binary_file(file, method1_modify_binary)

    if perspective_config["cliff"]:
        files = match_binary_file_by_size_and_content(extract_dir, 1016, '"name":"4V4_ComAll"')
        for file in files:
            modify_binary_file(file, method1_modify_binary)

    if perspective_config["watch_city"]:
        watch_files = [(1.01 * 1024, '"name":"PVP_SW_City_Merge01"'), (1022, '"name":"PVP_SW_City_Merge03"'),
                       (1022, '"name":"PVP_SW_City_Merge02"')]
        for size, content in watch_files:
            files = match_binary_file_by_size_and_content(extract_dir, size, content)
            for file in files:
                modify_binary_file(file, method1_modify_binary)


def modify_character_color(extract_dir: str):
    """人物变色：改用二进制匹配+修改（仅bin/lh/lmat）"""
    files1 = match_binary_file_by_size_and_content(extract_dir, 962, '"name":"CF_FamilyB_LingHu_3P"')
    for file in files1:
        modify_binary_file(file, lambda c: re.sub(rb'"vectors":\[{"name":"_Color","value":\[.*?]',
                                                  rb'"vectors":\[{"name":"_Color","value":[0]', c))
    files2 = match_binary_file_by_size_and_content(extract_dir, 960, '"name":"CF_FamilyP_LingHu_3P"')
    for file in files2:
        modify_binary_file(file, lambda c: re.sub(rb'"vectors":\[{"name":"_Color","value":\[.*?]',
                                                  rb'"vectors":\[{"name":"_Color","value":[0]', c))


def modify_range(extract_dir: str):
    """范围功能：改用二进制匹配（仅bin/lh/lmat，优先lh）"""
    range_files = [
        (20.06 * 1024, '"props":{"name":"CF_FamilyB_Swat_3P_GO_L"', "a"),
        (20.08 * 1024, '"props":{"name":"CF_FamilyP_Swat_3P_GO_L"', "b"),
        (20.31 * 1024, '"props":{"name":"CF_FamilyP_LingHu_3P_GO_L"', "c"),
        (20.42 * 1024, '"props":{"name":"CF_FamilyB_LingHu_3P_GO_L"', "d")
    ]
    for size, content, replace_file in range_files:
        target_files = match_binary_file_by_size_and_content(extract_dir, size, content)
        replace_file_path = os.path.join(REPLACE_FILES_DIR, replace_file)
        if os.path.exists(replace_file_path):
            for target_file in target_files:
                try:
                    shutil.copyfile(replace_file_path, target_file)
                except:
                    continue


def modify_gun_content(content: str, config: Dict) -> str:
    """枪械修改：保持原文本逻辑（JSON文件）"""
    new_content = content
    aim_level = config["aim_level"]
    move_speed = config["move_speed"]
    fire_rate = config["fire_rate"]

    if aim_level:
        if '"m_OverrideAimAssistanceSpeed":' in new_content:
            new_content = re.sub(r'"m_OverrideAimAssistanceSpeed":\s*[^,}]+',
                                 f'"m_OverrideAimAssistanceSpeed":{aim_level},', new_content)
        else:
            new_content = new_content.replace('"m_WeaponNickName"',
                                              f'"m_OverrideAimAssistanceSpeed":{aim_level},"m_WeaponNickName"')
        if '"m_AimMoveScale"' in new_content:
            new_content = new_content.replace('"m_AimMoveScale"',
                                              f'"m_OverrideAimAssistanceSpeed":{aim_level},"m_AimMoveScale"')

    if move_speed:
        new_content = re.sub(r'"m_MovementScale":\s*[^,}]+', f'"m_MovementScale":{move_speed},', new_content)

    if fire_rate:
        new_content = re.sub(r'"m_FireInterval":\s*[^,}]+', f'"m_FireInterval":{fire_rate},', new_content)

    if config["double_penetration"]:
        new_content = re.sub(r'"m_MaxThroughWall":\s*[^,}]+', '"m_MaxThroughWall":15,', new_content)

    if config["infinite_ammo"]:
        new_content = re.sub(r'"m_ShotCost":\s*[^,}]+', '"m_ShotCost":0.00001,', new_content)

    dispersion_fields = [
        "m_MaxInaccuracy", "m_MinInaccuracy", "m_DisperseBase",
        "m_DisperseModifierStanding", "m_DisperseModifierJumping", "m_DisperseModifierWalking"
    ]
    if config["dispersion"] == "no":
        for field in dispersion_fields:
            new_content = re.sub(rf'"{field}":\s*[^,}}]+', f'"{field}":0,', new_content)
    elif config["dispersion"] == "has":
        for field in dispersion_fields:
            new_content = re.sub(rf'"{field}":\s*[^,}}]+', f'"{field}":0.018,', new_content)

    recoil_up_fields = ["m_RecoilUpBase", "m_RecoilUpModifier", "m_RecoilUpMax"]
    recoil_lateral_fields = ["m_RecoilLateralBase", "m_RecoilLateralModifier", "m_RecoilLateralMax"]
    if config["recoil"] == "no":
        for field in recoil_up_fields + recoil_lateral_fields:
            new_content = re.sub(rf'"{field}":\s*[^,}}]+', f'"{field}":0,', new_content)
    elif config["recoil"] == "has":
        new_content = re.sub(r'"m_RecoilUpBase":\s*[^,}]+', '"m_RecoilUpBase":0.08,', new_content)
        new_content = re.sub(r'"m_RecoilUpModifier":\s*[^,}]+', '"m_RecoilUpModifier":0.04,', new_content)
        new_content = re.sub(r'"m_RecoilUpMax":\s*[^,}]+', '"m_RecoilUpMax":2,', new_content)
        for field in recoil_lateral_fields:
            new_content = re.sub(rf'"{field}":\s*[^,}}]+', f'"{field}":0,', new_content)

    if config["sniper_no_dispersion"]:
        sniper_dispersion_fields = [
            "m_IgnoreShotSpreadTime", "m_MaxInaccuracy", "m_MinInaccuracy", "m_DisperseBase",
            "m_DisperseModifierStanding", "m_DisperseModifierJumping", "m_DisperseModifierWalking"
        ]
        for field in sniper_dispersion_fields:
            new_content = re.sub(rf'"{field}":\s*[^,}}]+', f'"{field}":0,', new_content)

    if config["sniper_fast_reload"]:
        new_content = re.sub(r'"m_ZoomingMovementScale":\s*[^,}]+', '"m_ZoomingMovementScale":1,', new_content)
        new_content = re.sub(r'"m_ZoomInFOVRate":\s*[^,}]+', '"m_ZoomInFOVRate":1000,', new_content)
        new_content = re.sub(r'"m_EquipTime":\s*[^,}]+', '"m_EquipTime":0.7,', new_content)
        new_content = re.sub(r'"m_FireInterval":\s*[^,}]+', '"m_FireInterval":0.9,', new_content)

    if config["melee_fast_attack"]:
        new_content = re.sub(r'"m_DelayMeleeHeavyAttackHitTime":\s*[^,}]+', '"m_DelayMeleeHeavyAttackHitTime":0.05,',
                             new_content)
        new_content = re.sub(r'"m_MeleeWeaponHeavyAttackAngle":\s*[^,}]+', '"m_MeleeWeaponHeavyAttackAngle":360,',
                             new_content)
        new_content = re.sub(r'"m_HeavyAttackInterval":\s*[^,}]+', '"m_HeavyAttackInterval":0.1,', new_content)

    return new_content


def modify_guns(extract_dir: str, gun_configs):
    """枪械修改：保持原逻辑（仅JSON）"""
    for config in gun_configs:
        weapon_name = config["weapon_name"]
        if not weapon_name:
            continue
        escaped_name = unicode_escape(weapon_name)
        target_str = f'"m_WeaponNickName":"{escaped_name}"'
        for root, _, files in os.walk(extract_dir):
            for file in files:
                if file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    if 1024 <= file_size <= 9216:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            if target_str in content:
                                new_content = modify_gun_content(content, config)
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                        except:
                            continue


def modify_no_popup(extract_dir: str):
    """无弹窗：保持原逻辑（仅JSON）"""
    weapon_name = "AK47-木兰"
    escaped_name = unicode_escape(weapon_name)
    target_str = f'"m_WeaponNickName":"{escaped_name}"'
    target_files = []
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                if 1024 <= file_size <= 9216:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            if target_str in f.read():
                                target_files.append(file_path)
                    except:
                        continue
    replace_file_e = os.path.join(REPLACE_FILES_DIR, "e")
    if os.path.exists(replace_file_e):
        for target_file in target_files:
            try:
                shutil.copyfile(replace_file_e, target_file)
            except:
                continue


# ===================== 自定义组件 =====================
# 绿色勾选框
class GreenCheckCheckBox(CheckBox):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (30, 30)
        self.color = (0, 0, 0, 1)
        self.active_color = (0, 0.8, 0, 1)


# 自定义展开面板（替代原ExpandablePanel）
class CustomExpandPanel(BoxLayout):
    def __init__(self, panel_title: str, content, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.size_hint_y = None
        self.collapsed = True
        self.content_widget = content

        # 头部按钮
        self.header_btn = Button(
            text=panel_title, font_size=14, color=(0, 0, 0, 1),
            background_color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height=50
        )
        self.header_btn.bind(on_press=self.toggle_panel)
        self.add_widget(self.header_btn)

        # 内容区域（默认隐藏）
        self.content_widget.size_hint_y = None
        self.content_widget.bind(minimum_height=self.content_widget.setter('height'))
        self.content_widget.opacity = 0
        self.content_widget.height = 0
        self.add_widget(self.content_widget)

        self.height = 50

    def toggle_panel(self, instance):
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.content_widget.opacity = 0
            self.content_widget.height = 0
            self.height = 50
        else:
            self.content_widget.opacity = 1
            self.content_widget.height = self.content_widget.minimum_height
            self.height = 50 + self.content_widget.height


# 枪械配置面板
class GunConfigPanel(CustomExpandPanel):
    def __init__(self, panel_title: str, **kwargs):
        # 内容布局
        content = GridLayout(cols=1, spacing=8, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # 输入项
        self.weapon_name = TextInput(hint_text="武器名称（如AK47-无影）", size_hint_y=None, height=45)
        content.add_widget(self.weapon_name)

        self.aim_level = TextInput(hint_text="自瞄等级（数字）", size_hint_y=None, height=45)
        content.add_widget(self.aim_level)

        self.move_speed = TextInput(hint_text="移速（数字）", size_hint_y=None, height=45)
        content.add_widget(self.move_speed)

        self.fire_rate = TextInput(hint_text="射速（数字）", size_hint_y=None, height=45)
        content.add_widget(self.fire_rate)

        # 双穿
        double_pen_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=35)
        double_pen_layout.add_widget(Label(text="双穿", font_size=14))
        self.double_penetration = GreenCheckCheckBox(active=False)
        double_pen_layout.add_widget(self.double_penetration)
        content.add_widget(double_pen_layout)

        # 无限子弹
        infinite_ammo_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=35)
        infinite_ammo_layout.add_widget(Label(text="无限子弹", font_size=14))
        self.infinite_ammo = GreenCheckCheckBox(active=False)
        infinite_ammo_layout.add_widget(self.infinite_ammo)
        content.add_widget(infinite_ammo_layout)

        # 散发功能
        content.add_widget(Label(text="散发功能", font_size=14, color=(0.5, 0, 0.5, 1)))
        dispersion_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=None, height=35)
        self.dispersion_no = GreenCheckCheckBox(active=False)
        self.dispersion_has = GreenCheckCheckBox(active=False)
        dispersion_layout.add_widget(BoxLayout(orientation='horizontal', spacing=5,
                                               children=[Label(text="无散发", font_size=14), self.dispersion_no]))
        dispersion_layout.add_widget(BoxLayout(orientation='horizontal', spacing=5,
                                               children=[Label(text="有散发", font_size=14), self.dispersion_has]))
        content.add_widget(dispersion_layout)

        # 上台功能
        content.add_widget(Label(text="上台功能", font_size=14, color=(0.5, 0, 0.5, 1)))
        recoil_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=None, height=35)
        self.recoil_no = GreenCheckCheckBox(active=False)
        self.recoil_has = GreenCheckCheckBox(active=False)
        recoil_layout.add_widget(BoxLayout(orientation='horizontal', spacing=5,
                                           children=[Label(text="无上台", font_size=14), self.recoil_no]))
        recoil_layout.add_widget(BoxLayout(orientation='horizontal', spacing=5,
                                           children=[Label(text="有上台", font_size=14), self.recoil_has]))
        content.add_widget(recoil_layout)

        # 狙击相关
        sniper_no_disp_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=35)
        sniper_no_disp_layout.add_widget(Label(text="狙击无散发", font_size=14))
        self.sniper_no_dispersion = GreenCheckCheckBox(active=False)
        sniper_no_disp_layout.add_widget(self.sniper_no_dispersion)
        content.add_widget(sniper_no_disp_layout)

        sniper_fast_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=35)
        sniper_fast_layout.add_widget(Label(text="狙击换弹快", font_size=14))
        self.sniper_fast_reload = GreenCheckCheckBox(active=False)
        sniper_fast_layout.add_widget(self.sniper_fast_reload)
        content.add_widget(sniper_fast_layout)

        # 近战快刀
        melee_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=35)
        melee_layout.add_widget(Label(text="近战快刀", font_size=14))
        self.melee_fast_attack = GreenCheckCheckBox(active=False)
        melee_layout.add_widget(self.melee_fast_attack)
        content.add_widget(melee_layout)

        # 绑定互斥逻辑
        self.dispersion_no.bind(active=self.on_dispersion_toggle)
        self.dispersion_has.bind(active=self.on_dispersion_toggle)
        self.recoil_no.bind(active=self.on_recoil_toggle)
        self.recoil_has.bind(active=self.on_recoil_toggle)

        super().__init__(panel_title=panel_title, content=content, **kwargs)

    def on_dispersion_toggle(self, instance, value):
        if value:
            if instance == self.dispersion_no:
                self.dispersion_has.active = False
            else:
                self.dispersion_no.active = False

    def on_recoil_toggle(self, instance, value):
        if value:
            if instance == self.recoil_no:
                self.recoil_has.active = False
            else:
                self.recoil_no.active = False

    def get_config(self):
        dispersion = "none"
        if self.dispersion_no.active:
            dispersion = "no"
        elif self.dispersion_has.active:
            dispersion = "has"

        recoil = "none"
        if self.recoil_no.active:
            recoil = "no"
        elif self.recoil_has.active:
            recoil = "has"

        return {
            "weapon_name": self.weapon_name.text.strip(),
            "aim_level": float(self.aim_level.text) if self.aim_level.text.strip() else None,
            "move_speed": float(self.move_speed.text) if self.move_speed.text.strip() else None,
            "fire_rate": float(self.fire_rate.text) if self.fire_rate.text.strip() else None,
            "double_penetration": self.double_penetration.active,
            "infinite_ammo": self.infinite_ammo.active,
            "dispersion": dispersion,
            "recoil": recoil,
            "sniper_no_dispersion": self.sniper_no_dispersion.active,
            "sniper_fast_reload": self.sniper_fast_reload.active,
            "melee_fast_attack": self.melee_fast_attack.active
        }


# ===================== 主应用 =====================
class GameModApp(App):
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)

        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=20)

        # 1. 文件导入区域
        import_layout = FloatLayout(size_hint_y=None, height=150)
        with import_layout.canvas.before:
            Color(1, 1, 1, 1)
            self.import_rect = Rectangle(size=import_layout.size, pos=import_layout.pos)
        import_layout.bind(size=self.update_rect, pos=self.update_rect)

        with import_layout.canvas:
            Color(0.5, 0, 0.5, 1)
            Rectangle(size=(import_layout.width - 4, import_layout.height - 4),
                      pos=(import_layout.x + 2, import_layout.y + 2))

        self.import_btn = Button(text="+", font_size=40, size_hint=(None, None), size=(80, 80),
                                 background_color=(0.2, 0.8, 0.2, 1), pos_hint={'center_x': 0.5, 'center_y': 0.6})
        self.import_btn.bind(on_press=self.select_file)
        import_layout.add_widget(self.import_btn)

        self.import_label = Label(text="点击加号导入压缩包", font_size=16, color=(0, 0, 0, 1),
                                  pos_hint={'center_x': 0.5, 'center_y': 0.3})
        import_layout.add_widget(self.import_label)
        main_layout.add_widget(import_layout)

        # 2. 状态提示
        self.status_label = Label(text="准备就绪", font_size=14, color=(0, 0, 0, 1), size_hint_y=None, height=30)
        main_layout.add_widget(self.status_label)

        # 3. 透视功能
        main_layout.add_widget(
            Label(text="=== 透视功能 ===", font_size=18, color=(0.5, 0, 0.5, 1), size_hint_y=None, height=40))
        perspective_grid = GridLayout(cols=1, spacing=8, size_hint_y=None)
        perspective_grid.bind(minimum_height=perspective_grid.setter('height'))

        maps = [("沙漠灰", "dust2"), ("新年广场", "new_year_square"), ("胜利广场", "victory_square"),
                ("供电所", "power_plant"), ("沙漠对决", "desert_duel"), ("运输船", "transport_ship"),
                ("悬崖", "cliff"), ("守望之城", "watch_city")]

        self.perspective_cbs = {}
        for name, key in maps:
            layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=35)
            layout.add_widget(Label(text=name, font_size=14, color=(0, 0, 0, 1)))
            cb = GreenCheckCheckBox(active=False)
            layout.add_widget(cb)
            self.perspective_cbs[key] = cb
            perspective_grid.add_widget(layout)
        main_layout.add_widget(perspective_grid)

        # 4. 人物变色
        char_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        char_layout.add_widget(Label(text="人物变色", font_size=16, color=(0.5, 0, 0.5, 1)))
        self.char_cb = GreenCheckCheckBox(active=False)
        char_layout.add_widget(self.char_cb)
        main_layout.add_widget(char_layout)

        # 5. 范围功能
        range_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        range_layout.add_widget(Label(text="范围功能", font_size=16, color=(0.5, 0, 0.5, 1)))
        self.range_cb = GreenCheckCheckBox(active=False)
        range_layout.add_widget(self.range_cb)
        main_layout.add_widget(range_layout)

        # 6. 枪械修改
        main_layout.add_widget(
            Label(text="=== 枪械修改功能 ===", font_size=18, color=(0.5, 0, 0.5, 1), size_hint_y=None, height=40))
        self.gun_panels = []
        for i in range(1, 7):
            panel = GunConfigPanel(f"武器{i}")
            self.gun_panels.append(panel)
            main_layout.add_widget(panel)

        # 7. 无弹窗
        popup_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        popup_layout.add_widget(Label(text="无弹窗功能", font_size=16, color=(0.5, 0, 0.5, 1)))
        self.popup_cb = GreenCheckCheckBox(active=False)
        popup_layout.add_widget(self.popup_cb)
        main_layout.add_widget(popup_layout)

        # 8. 开始修改
        modify_btn = Button(text="开始修改", font_size=20, background_color=(0.2, 0.8, 0.2, 1),
                            size_hint_y=None, height=70)
        modify_btn.bind(on_press=self.start_modify)
        main_layout.add_widget(modify_btn)

        # 滚动视图
        scroll = ScrollView()
        scroll.add_widget(main_layout)

        # 初始化目录和内置文件
        os.makedirs(BASE_DIR, exist_ok=True)
        os.makedirs(REPLACE_FILES_DIR, exist_ok=True)
        self.status_label.text = "提取内置文件..."
        if extract_built_in_files():
            self.status_label.text = "内置文件提取成功"
        else:
            self.status_label.text = "内置文件提取失败（仅安卓端有效）"

        return scroll

    def update_rect(self, instance, value):
        self.import_rect.pos = instance.pos
        self.import_rect.size = instance.size

    def select_file(self, instance):
        filechooser.open_file(filters=[("ZIP文件", "*.zip")], on_selection=self.on_file_selected)

    def on_file_selected(self, selection):
        if selection:
            global INPUT_FILE_PATH
            INPUT_FILE_PATH = selection[0]
            self.import_label.text = f"已导入：{os.path.basename(INPUT_FILE_PATH)}"
            self.status_label.text = "文件导入成功"

    def start_modify(self, instance):
        global INPUT_FILE_PATH
        if not INPUT_FILE_PATH:
            self.status_label.text = "请先导入压缩包！"
            return

        try:
            self.status_label.text = "开始处理..."
            # 收集配置
            perspective_cfg = {k: v.active for k, v in self.perspective_cbs.items()}
            gun_cfgs = [p.get_config() for p in self.gun_panels]

            # 解压
            unzip_file(INPUT_FILE_PATH, TEMP_EXTRACT_DIR)

            # 检查layaairfiles.txt
            layaair_path = None
            for root, _, files in os.walk(TEMP_EXTRACT_DIR):
                if "layaairfiles.txt" in files:
                    layaair_path = os.path.join(root, "layaairfiles.txt")
                    break

            # 功能生效判断
            if layaair_path:
                layaair_time = os.path.getmtime(layaair_path)
                p_en = layaair_time < CUTOFF_TIME1
                c_en = layaair_time < CUTOFF_TIME1
                r_en = layaair_time < CUTOFF_TIME1
                g_en = layaair_time < CUTOFF_TIME2
                n_en = True
            else:
                p_en = c_en = r_en = g_en = n_en = True

            # 执行修改（仅修改文件匹配和读取方式，逻辑不变）
            if p_en and any(perspective_cfg.values()):
                self.status_label.text = "修改透视..."
                modify_perspective(TEMP_EXTRACT_DIR, perspective_cfg)
            if c_en and self.char_cb.active:
                self.status_label.text = "修改人物变色..."
                modify_character_color(TEMP_EXTRACT_DIR)
            if r_en and self.range_cb.active:
                self.status_label.text = "修改范围功能..."
                modify_range(TEMP_EXTRACT_DIR)
            if g_en and any([g["weapon_name"] for g in gun_cfgs]):
                self.status_label.text = "修改枪械..."
                modify_guns(TEMP_EXTRACT_DIR, gun_cfgs)
            if n_en and self.popup_cb.active:
                self.status_label.text = "修改无弹窗..."
                modify_no_popup(TEMP_EXTRACT_DIR)

            # 更新文件时间
            self.status_label.text = "更新文件时间..."
            update_all_file_times(TEMP_EXTRACT_DIR)

            # 打包输出
            self.status_label.text = "打包文件..."
            output_path = os.path.join(os.path.dirname(INPUT_FILE_PATH), "极速换肤.zip")
            zip_dir(TEMP_EXTRACT_DIR, output_path)

            # 清理
            shutil.rmtree(TEMP_EXTRACT_DIR)
            self.status_label.text = f"修改完成！文件：极速换肤.zip"

        except zipfile.BadZipFile:
            self.status_label.text = "错误：不是有效的ZIP文件"
        except FileNotFoundError:
            self.status_label.text = "错误：文件路径不存在"
        except Exception as e:
            self.status_label.text = f"失败：{str(e)[:20]}"


if __name__ == '__main__':
    GameModApp().run()