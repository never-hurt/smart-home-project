# gesture/hand_gesture.py — 基于 MediaPipe 21个手部关键点的手势分类器
import os
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# MediaPipe 手部关键点索引常量
WRIST = 0
THUMB_CMC = 1; THUMB_MCP = 2; THUMB_IP = 3; THUMB_TIP = 4
INDEX_MCP = 5; INDEX_PIP = 6; INDEX_DIP = 7; INDEX_TIP = 8
MIDDLE_MCP = 9; MIDDLE_PIP = 10; MIDDLE_DIP = 11; MIDDLE_TIP = 12
RING_MCP = 13; RING_PIP = 14; RING_DIP = 15; RING_TIP = 16
PINKY_MCP = 17; PINKY_PIP = 18; PINKY_DIP = 19; PINKY_TIP = 20


class HandGestureRecognizer:
    """手势识别器：输入 BGR 帧 → 返回手势名称和关键点坐标"""

    # 手指定义：(指尖, 指根PIP)
    FINGERS = [
        ("thumb",  THUMB_TIP,  THUMB_IP),
        ("index",  INDEX_TIP,  INDEX_PIP),
        ("middle", MIDDLE_TIP, MIDDLE_PIP),
        ("ring",   RING_TIP,   RING_PIP),
        ("pinky",  PINKY_TIP,  PINKY_PIP),
    ]

    def __init__(self, model_path=None):
        if model_path is None:
            # 模型文件与 hand_gesture.py 在同一目录下
            model_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "hand_landmarker.task"
            )
        base = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base,
            num_hands=1,
            running_mode=vision.RunningMode.VIDEO,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self._frame_counter = 0

    def detect(self, frame_bgr):
        """
        输入 BGR 帧 → 返回 (手势名称, 关键点列表) 或 (None, None)
        关键点列表: [(x, y, z), ...] 共21个，x/y 归一化[0,1]，z 相对于手腕深度
        """
        self._frame_counter += 1
        rgb = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_bgr)
        result = self.detector.detect_for_video(rgb, self._frame_counter * 33)

        if not result.hand_landmarks:
            return None, None

        lm = result.hand_landmarks[0]
        points = [(p.x, p.y, p.z) for p in lm]
        gesture = self._classify(points)
        return gesture, points

    def _classify(self, points):
        """
        纯手指数量分类 —— 按伸出数量 (0-5) 直接映射手势。
        伸出判断：指尖 y < 指根 PIP y（y轴向下，指尖在上=伸出）
        优势：不再区分具体哪根手指，区分度极大，误识别率极低
        """
        extended = []
        for name, tip_id, pip_id in self.FINGERS:
            if points[tip_id][1] < points[pip_id][1]:
                extended.append(name)

        num = len(extended)

        # ── 纯数量映射 ──
        gesture_map = {
            0: "✊ 握拳",
            1: "☝ 伸出1指",
            2: "✌ 伸出2指",
            3: "👌 伸出3指",
            4: "🖖 伸出4指",
            5: "🖐 五指张开",
        }
        return gesture_map.get(num, None)

    def close(self):
        self.detector.close()
