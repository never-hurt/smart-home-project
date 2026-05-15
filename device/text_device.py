from device.device_manager import DeviceStateMachine

if __name__ == "__main__":
    print("--- 1. 测试单例模式 ---")
    s1 = DeviceStateMachine()
    s2 = DeviceStateMachine()
    print(f"两个实例是否是同一个对象：{s1 is s2} (应该是True)")

    print("\n--- 2. 测试状态更新 ---")
    success, msg = s1.update_device_state("light", {"status": "on"})
    print(f"打开灯光结果：{success}, {msg} (应该是True)")

    print("\n--- 3. 测试状态读取 ---")
    success, state = s1.get_device_state("light")
    print(f"灯光当前状态：{state} (status应该是on)")

    print("\n--- 4. 测试越界保护 ---")
    success, msg = s1.update_device_state("air", {"temp": 35})
    print(f"温度调到35度结果：{success}, {msg} (应该是False，提示越界)")