import threading
import json
from vosk import Model, KaldiRecognizer
from pypinyin import lazy_pinyin, Style
from Levenshtein import distance
from acquisition.audio_capture import AudioCapture


class VoiceListener:
    def __init__(self, root, on_recognize_callback, on_listen_complete=None, on_error=None, on_status=None):
        self.root = root
        self.on_recognize_callback = on_recognize_callback
        self.on_listen_complete = on_listen_complete
        self.on_error = on_error
        self.on_status = on_status  # (status_type, message) 用于实时GUI状态更新
        self.running = False
        self.thread = None

        self.audio_capture = AudioCapture()

        try:
            self.model = Model("vosk-model-small-cn-0.22")
            self.recognizer = KaldiRecognizer(self.model, 16000)
            self.recognizer.SetWords(True)
            print("\n✅ Vosk中文模型加载成功！")
        except Exception as e:
            error_msg = f"模型加载失败！\n请确认：\n1. 项目根目录有 vosk-model-small-cn-0.22 文件夹\n2. 文件夹名没有拼写错误\n\n错误信息：{str(e)}"
            if self.on_error:
                self.on_error("致命错误", error_msg)
            raise e

        self.COMMAND_MAP = {
            "打开灯光": [
                "打开灯光", "开灯", "打开灯", "开个灯", "灯打开",
                "把灯打开", "灯光打开", "开下灯", "灯开一下"
            ],
            "关闭灯光": [
                "关闭灯光", "关灯", "关闭灯", "关个灯", "灯关闭",
                "把灯关掉", "灯光关闭", "关下灯", "灯关一下"
            ],
            "打开空调": [
                "打开空调", "开空调", "打开个空调", "空调打开",
                "把空调打开", "开下空调", "空调开一下"
            ],
            "关闭空调": [
                "关闭空调", "关空调", "关闭个空调", "空调关闭",
                "把空调关掉", "空调关一下", "空调关一下"
            ],
            "温度调高": [
                "温度调高", "调高温度", "升温", "温度高一点",
                "温度加一点", "温度上升", "调高一度", "温度加"
            ],
            "温度调低": [
                "温度调低", "调低温度", "降温", "温度低一点",
                "温度减一点", "温度下降", "调低一度", "温度减"
            ]
        }

        self._precompute_pinyin_map()

    def _precompute_pinyin_map(self):
        self.pinyin_map = {}
        for standard_cmd, keywords in self.COMMAND_MAP.items():
            self.pinyin_map[standard_cmd] = []
            for kw in keywords:
                pinyin_list = lazy_pinyin(kw, style=Style.NORMAL)
                pinyin_str = "".join(pinyin_list)
                self.pinyin_map[standard_cmd].append((kw, pinyin_str))

    def _text_to_pinyin(self, text):
        if not text:
            return ""
        pinyin_list = lazy_pinyin(text, style=Style.NORMAL)
        return "".join(pinyin_list)

    def _pinyin_similarity_match(self, text_pinyin, threshold=2):
        best_match = None
        min_distance = float('inf')

        for standard_cmd, kw_pinyin_list in self.pinyin_map.items():
            for kw, kw_pinyin in kw_pinyin_list:
                dist = distance(text_pinyin, kw_pinyin)
                if dist <= threshold and dist < min_distance:
                    min_distance = dist
                    best_match = standard_cmd
                    best_kw = kw

        if best_match:
            print(f"✅ 拼音匹配成功：关键词【{best_kw}】")
            return best_match
        return None

    def start(self):
        if self.thread and self.thread.is_alive():
            if self.on_error:
                self.on_error("提示", "正在录音中，请稍候...")
            return

        self.running = True
        self.thread = threading.Thread(target=self._listen_task, daemon=True)
        self.thread.start()

    def stop_listening(self):
        self.running = False
        self.audio_capture.stop()
        if self.thread:
            self.thread.join(timeout=1)
        print("\n监听已停止")

    def _listen_task(self):
        try:
            # ====== 阶段1：校准环境噪音 ======
            self._notify_status("calibrating", "🔇 正在测量环境噪音...")
            print("\n🔇 正在测量环境噪音...")
            avg_noise, threshold = self.audio_capture.calibrate_noise(duration=0.8)
            self._notify_status("calibrated", f"📊 环境噪音: {avg_noise:.0f} | 阈值: {threshold:.0f}")
            
            if not self.running:
                return

            # ====== 阶段2：等待用户说话 ======
            self._notify_status("waiting_voice", "👂 等待语音指令，请说话...")
            
            voice_detected = self.audio_capture.wait_for_voice(
                timeout=8.0,
                on_level=lambda rms, thr: self._notify_status("noise_level", f"{rms:.0f},{thr:.0f}")
            )
            
            if not self.running:
                return
                
            if not voice_detected:
                self._notify_status("matched", "❌ 超时未检测到语音，请重试")
                if self.running:
                    self.root.after(0, lambda: self.on_recognize_callback("", "[识别失败] 超时未检测到语音"))
                    if self.on_listen_complete:
                        self.root.after(500, self.on_listen_complete)
                return

            # ====== 阶段3：录音 ======
            self._notify_status("recording", "🎤 正在录音，请继续说话...")
            audio_frames = self.audio_capture.record_voice(
                max_duration=5.0,
                silence_duration=1.5,
                on_level=lambda rms, thr: self._notify_status("noise_level", f"{rms:.0f},{thr:.0f}")
            )
            
            if not self.running:
                return

            if len(audio_frames) < int(self.audio_capture.RATE / self.audio_capture.CHUNK * 0.5):
                self._notify_status("matched", "❌ 录音太短，未检测到有效语音")
                if self.running:
                    self.root.after(0, lambda: self.on_recognize_callback("", "[识别失败] 录音太短"))
                    if self.on_listen_complete:
                        self.root.after(500, self.on_listen_complete)
                return

            # 保存录音
            self.audio_capture.save_recording(audio_frames)

            # ====== 阶段4：语音识别 ======
            self._notify_status("recognizing", "🔍 正在识别语音...")
            print("\n🔍 正在识别...")
            self.recognizer.Reset()

            full_text = ""
            for frame in audio_frames:
                if self.recognizer.AcceptWaveform(frame):
                    result = json.loads(self.recognizer.Result())
                    full_text = result.get("text", "").strip()
                    print(f"📝 Vosk完整识别结果：{result}")

            if not full_text:
                partial_result = json.loads(self.recognizer.PartialResult())
                full_text = partial_result.get("partial", "").strip()
                print(f"📝 Vosk部分识别结果：{partial_result}")

            # ====== 阶段5：显示结果 ======
            print(f"\n🎉 最终识别文字：【{full_text}】")
            self._notify_status("raw_text", f"识别文字：{full_text if full_text else '(未识别到语音)'}")
            
            matched_cmd = self._multi_level_match(full_text)
            print(f"🎯 最终匹配到的指令：{matched_cmd}")

            if "[识别失败]" in matched_cmd:
                self._notify_status("matched", f"❌ {matched_cmd}")
            else:
                self._notify_status("matched", f"✅ 匹配指令：{matched_cmd}")

            # 同时传递原始识别文字和匹配后的指令
            if self.running:
                self.root.after(0, lambda: self.on_recognize_callback(full_text, matched_cmd))
                # 通知监听完成，由调用方决定是否继续
                if self.on_listen_complete:
                    self.root.after(800, self.on_listen_complete)

        except Exception as e:
            print(f"\n❌ 识别异常：{str(e)}")
            self._notify_status("error", f"❌ 识别异常：{str(e)}")
            if self.on_error:
                self.on_error("错误", f"识别异常：{str(e)}")
            self.running = False

    def _notify_status(self, status_type, message):
        """安全地向GUI发送状态更新（防止窗口关闭后崩溃）"""
        if self.on_status and self.running:
            try:
                self.root.after(0, lambda: self.on_status(status_type, message))
            except Exception:
                pass

    def _multi_level_match(self, text):
        if not text:
            return "[识别失败] 未识别到任何语音"

        clean_text = text.replace(" ", "").replace("\n", "").replace("\t", "")
        print(f"🔧 处理后的识别文字：【{clean_text}】")

        for standard_cmd, keywords in self.COMMAND_MAP.items():
            for kw in keywords:
                clean_kw = kw.replace(" ", "")
                if clean_kw in clean_text:
                    print(f"✅ 原文字匹配成功：关键词【{kw}】")
                    return standard_cmd

        text_pinyin = self._text_to_pinyin(clean_text)
        print(f"🔤 识别结果拼音：【{text_pinyin}】")
        pinyin_match = self._pinyin_similarity_match(text_pinyin)
        if pinyin_match:
            return pinyin_match

        if ("开" in clean_text or "kai" in text_pinyin) and ("灯" in clean_text or "deng" in text_pinyin):
            return "打开灯光"
        if ("关" in clean_text or "guan" in text_pinyin) and ("灯" in clean_text or "deng" in text_pinyin):
            return "关闭灯光"
        if ("开" in clean_text or "kai" in text_pinyin) and ("空调" in clean_text or "kongtiao" in text_pinyin):
            return "打开空调"
        if ("关" in clean_text or "guan" in text_pinyin) and ("空调" in clean_text or "kongtiao" in text_pinyin):
            return "关闭空调"
        if ("高" in clean_text or "gao" in text_pinyin) or ("加" in clean_text or "jia" in text_pinyin):
            return "温度调高"
        if ("低" in clean_text or "di" in text_pinyin) or ("减" in clean_text or "jian" in text_pinyin):
            return "温度调低"

        return f"[识别失败] 未匹配到指令：{text}"

    # _ask_continue 已移除，改为通过 on_listen_complete 回调由调用方处理