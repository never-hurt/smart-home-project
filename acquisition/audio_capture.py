import pyaudio
import wave
import time
import struct
import math


class AudioCapture:
    def __init__(self):
        # VOSK强制要求的唯一格式，绝对不能改
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 3  # 固定录音3秒，确保录完完整句子

        self.p = pyaudio.PyAudio()
        self.stream = None
        self.recording_count = 0
        self.noise_threshold = 500  # 默认噪音阈值

        # 初始化并列出所有可用麦克风
        self._init_stream()

    def _init_stream(self):
        """列出所有麦克风并让用户选择，解决设备选错问题"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        print("\n=== 可用麦克风设备列表 ===")
        input_devices = []
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if dev['maxInputChannels'] > 0:
                input_devices.append(i)
                print(f"[{i}] {dev['name']}")
        print("==========================\n")

        # 默认使用第一个可用麦克风，如果不行，改成你看到的设备编号
        selected_device = input_devices[0]
        print(f"正在使用麦克风：[{selected_device}] {self.p.get_device_info_by_index(selected_device)['name']}")

        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index=selected_device,
            frames_per_buffer=self.CHUNK
        )

    def _get_rms(self, data):
        """计算音频数据的RMS音量"""
        count = len(data) // 2
        fmt = f"{count}h"
        shorts = struct.unpack(fmt, data)
        sum_squares = sum(s * s for s in shorts)
        rms = math.sqrt(sum_squares / count) if count > 0 else 0
        return rms

    def calibrate_noise(self, duration=1.0):
        """测量环境噪音水平，返回噪音阈值"""
        print("\n🔇 正在测量环境噪音...")
        frames_to_read = int(self.RATE / self.CHUNK * duration)
        rms_values = []
        
        for _ in range(frames_to_read):
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            rms = self._get_rms(data)
            rms_values.append(rms)
        
        avg_noise = sum(rms_values) / len(rms_values) if rms_values else 0
        # 阈值设为环境噪音的2倍，但至少300
        self.noise_threshold = max(avg_noise * 2.0, 300)
        print(f"📊 环境噪音RMS: {avg_noise:.1f}, 语音检测阈值: {self.noise_threshold:.1f}")
        return avg_noise, self.noise_threshold

    def wait_for_voice(self, timeout=8.0, on_level=None):
        """等待用户说话，检测到声音后返回True，超时返回False"""
        print("👂 等待语音输入...")
        max_frames = int(self.RATE / self.CHUNK * timeout)
        frame_count = 0
        
        for _ in range(max_frames):
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            rms = self._get_rms(data)
            frame_count += 1
            
            # 每10帧回调一次音量等级（用于GUI显示）
            if on_level and frame_count % 10 == 0:
                on_level(rms, self.noise_threshold)
            
            if rms > self.noise_threshold:
                print(f"🎙️ 检测到语音！(RMS: {rms:.1f} > 阈值: {self.noise_threshold:.1f})")
                return True
        
        print("⏰ 等待超时，未检测到语音")
        return False

    def record_voice(self, max_duration=5.0, silence_duration=1.5, on_level=None):
        """录音直到检测到连续静音，或达到最大时长"""
        print("\n🎤 开始录音...")
        frames = []
        max_frames = int(self.RATE / self.CHUNK * max_duration)
        silence_frames = int(self.RATE / self.CHUNK * silence_duration)
        silent_count = 0
        has_voice = False
        
        for i in range(max_frames):
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            frames.append(data)
            rms = self._get_rms(data)
            
            if on_level and i % 10 == 0:
                on_level(rms, self.noise_threshold)
            
            if rms > self.noise_threshold:
                has_voice = True
                silent_count = 0
            else:
                silent_count += 1
            
            # 检测到声音后，如果连续静音超过阈值则停止
            if has_voice and silent_count >= silence_frames:
                print(f"🔇 检测到 {silence_duration}秒 静音，录音结束")
                break
        
        if not has_voice:
            print("⚠️ 未检测到有效语音")
        
        print(f"✅ 录音结束，共 {len(frames)} 帧 ({len(frames)*self.CHUNK/self.RATE:.1f}秒)")
        return frames

    def record_fixed(self):
        """固定3秒录音，100%能录到声音（保留作为备用）"""
        print("\n🎤 开始录音，请说话！")
        frames = []

        for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            frames.append(data)

        print("✅ 录音结束")

        # 保存录音文件
        self.recording_count += 1
        filename = f"录音_{self.recording_count}.wav"
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"💾 录音已保存：{filename}")

        return frames

    def save_recording(self, frames):
        """保存录音到wav文件"""
        self.recording_count += 1
        filename = f"录音_{self.recording_count}.wav"
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"💾 录音已保存：{filename}")
        return filename

    def stop(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()