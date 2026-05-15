from control.cmd_parser import CmdParser

if __name__ == "__main__":
    parser = CmdParser()

    print("--- 1. 测试灯光指令 ---")
    success, msg = parser.parse_and_execute("打开灯光")
    print(f"结果：{success}, {msg} (应该是True)")

    print("\n--- 2. 测试空调指令 ---")
    success, msg = parser.parse_and_execute("打开空调")
    print(f"结果：{success}, {msg} (应该是True)")

    print("\n--- 3. 测试温度调高 ---")
    success, msg = parser.parse_and_execute("温度调高")
    print(f"结果：{success}, {msg} (应该是True，温度变成25)")

    print("\n--- 4. 测试无效指令 ---")
    success, msg = parser.parse_and_execute("打开电视")
    print(f"结果：{success}, {msg} (应该是False，提示未匹配)")