# control/cmd_parser.py
# control/cmd_parser.py
from typing import Tuple
from device.device_manager import DeviceStateMachine


class CmdParser:
    def __init__(self):
        self.state_machine = DeviceStateMachine()
        # 指令映射字典，支持同义指令，后续可扩展
        self.cmd_map = {
            # 灯光控制
            "打开灯光": ("light", {"status": "on"}),
            "开灯": ("light", {"status": "on"}),
            "关闭灯光": ("light", {"status": "off"}),
            "关灯": ("light", {"status": "off"}),
            # 空调控制
            "打开空调": ("air", {"status": "on"}),
            "开空调": ("air", {"status": "on"}),
            "关闭空调": ("air", {"status": "off"}),
            "关空调": ("air", {"status": "off"}),
            "温度调高": ("air", "temp_up"),
            "温度调低": ("air", "temp_down"),
            "空调24度": ("air", {"temp": 24}),
            "空调26度": ("air", {"temp": 26}),
        }

    # 唯一指令执行入口，所有识别模块只调用这个方法
    def parse_and_execute(self, cmd_text: str) -> Tuple[bool, str]:
        # 模糊匹配，只要指令里包含关键词就匹配
        match_cmd = None
        for cmd in self.cmd_map.keys():
            if cmd in cmd_text:
                match_cmd = cmd
                break

        if not match_cmd:
            return False, f"未匹配到有效指令：{cmd_text}"

        device, action = self.cmd_map[match_cmd]

        # 处理温度加减的特殊动作
        if device == "air" and action == "temp_up":
            success, state = self.state_machine.get_device_state("air")
            if not success:
                return False, "获取空调状态失败"
            new_temp = state["temp"] + 1
            action = {"temp": new_temp}
        elif device == "air" and action == "temp_down":
            success, state = self.state_machine.get_device_state("air")
            if not success:
                return False, "获取空调状态失败"
            new_temp = state["temp"] - 1
            action = {"temp": new_temp}

        # 执行状态更新
        success, msg = self.state_machine.update_device_state(device, action)
        return success, msg