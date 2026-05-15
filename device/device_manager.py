# device/device_manager.py
import threading
from typing import Dict, Tuple


class DeviceStateMachine:
    # 单例模式，全局唯一设备状态，避免多实例错乱
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        # 线程锁，保护所有状态读写，杜绝多线程数据竞争
        self.lock = threading.Lock()
        # 设备全局状态定义，固化数据结构
        self.device_state: Dict[str, Dict] = {
            "light": {
                "status": "off",  # 合法状态：on/off
                "brightness": 50,  # 亮度范围0-100
                "valid_status": ["on", "off"]
            },
            "air": {
                "status": "off",
                "temp": 24,  # 温度范围16-30℃
                "valid_status": ["on", "off"],
                "temp_min": 16,
                "temp_max": 30
            }
        }
        self._initialized = True

    # 唯一合法的状态读取方法，线程安全
    def get_device_state(self, device_name: str) -> Tuple[bool, Dict]:
        with self.lock:
            if device_name not in self.device_state:
                return False, {}
            return True, self.device_state[device_name].copy()

    # 唯一合法的状态修改方法，自带合法性校验
    # ---------------------- 唯一合法的状态修改方法（线程安全+合法性校验+重复操作拦截） ----------------------
    def update_device_state(self, device_name: str, update_dict: Dict) -> Tuple[bool, str]:
        """
        更新指定设备的状态，自带合法性校验+有限状态机管控+重复操作拦截
        :param device_name: 设备名（light/air）
        :param update_dict: 要更新的状态字典
        :return: (是否成功, 提示信息)
        """
        with self.lock:
            # 1. 校验设备是否存在
            if device_name not in self.device_state:
                return False, f"无效设备：{device_name}"

            device = self.device_state[device_name]

            # 2. 新增：重复操作拦截，判断是否需要更新
            need_update = False
            for key, target_value in update_dict.items():
                if key not in device:
                    continue
                # 只要有一个字段和当前值不一样，就需要更新
                if device[key] != target_value:
                    need_update = True
                    break
            # 如果所有字段都和当前状态一致，直接返回重复提示，不执行更新
            if not need_update:
                if "status" in update_dict:
                    status_desc = "开启" if update_dict["status"] == "on" else "关闭"
                    return True, f"设备{device_name}已处于{status_desc}状态，无需重复操作"
                else:
                    return True, f"设备{device_name}状态无变化，无需重复操作"

            # 3. 校验状态是否合法（有限状态机）
            if "status" in update_dict:
                new_status = update_dict["status"]
                if new_status not in device["valid_status"]:
                    return False, f"设备{device_name}不支持{new_status}状态"

            # 4. 校验参数是否越界
            if device_name == "light" and "brightness" in update_dict:
                new_bright = update_dict["brightness"]
                if not 0 <= new_bright <= 100:
                    return False, "亮度必须在0-100之间"

            if device_name == "air" and "temp" in update_dict:
                new_temp = update_dict["temp"]
                if not device["temp_min"] <= new_temp <= device["temp_max"]:
                    return False, f"温度必须在{device['temp_min']}-{device['temp_max']}℃之间"
                # 状态机规则：关闭的空调不能调温度
                if device["status"] == "off":
                    return False, "空调未开启，无法调节温度"

            # 5. 执行状态更新
            device.update(update_dict)
            return True, f"设备{device_name}状态更新成功"