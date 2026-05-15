# recognition/speech_recognizer.py 课程要求特征识别层
import speech_recognition as sr
from typing import Tuple

class SpeechRecognizer:
    """
    语音识别类：课程要求特征识别层核心
    支持中文语音转文本
    """
    def __init__(self):
        # 初始化识别器
        self.recognizer = sr.Recognizer()

    def recognize_audio(self, audio: sr.AudioData) -> Tuple[bool, str]:
        """
        将音频数据转换为中文文本
        :param audio: 采集到的音频数据
        :return: (是否识别成功, 识别文本/错误信息)
        """
        try:
            # ---------------------- 课程要求：中文语音转文本 ----------------------
            # 调用在线识别API，指定语言为中文（zh-CN）
            text = self.recognizer.recognize_google(audio, language="zh-CN")
            return True, text
        except sr.UnknownValueError:
            return False, "无法识别语音内容"
        except sr.RequestError as e:
            return False, f"识别服务请求失败：{e}"
        except Exception as e:
            return False, f"识别发生未知错误：{e}"