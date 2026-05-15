# gesture/gesture_listener.py — 整合摄像头采集 + 手势识别 + 骨骼绘制
import threading
import cv2
from gesture.hand_gesture import HandGestureRecognizer

# 手部关键点连线定义（相邻骨骼对）
BONE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),       # 拇指
    (0, 5), (5, 6), (6, 7), (7, 8),       # 食指
    (0, 9), (9, 10), (10, 11), (11, 12),   # 中指
    (0, 13), (13, 14), (14, 15), (15, 16), # 无名指
    (0, 17), (17, 18), (18, 19), (19, 20), # 小指
    (5, 9), (9, 13), (13, 17),             # 掌心横线
]


class GestureListener:
    """
    手势监听器（独立线程）：
      1. 摄像头实时采集
      2. 调用 HandGestureRecognizer 识别人体动作
      3. 在帧上绘制关键点和骨骼连线
      4. 通过回调传给 GUI 显示
    """

    # 防抖：同一手势需连续出现 N 帧才触发回调
    DEBOUNCE_FRAMES = 10

    def __init__(self, on_gesture=None, on_frame=None, on_error=None, camera_index=0):
        """
        :param on_gesture(gesture_name): 稳定手势触发时回调
        :param on_frame(frame_bgr):      每帧回调，已绘制骨骼的 BGR 数组
        :param on_error(msg):            异常回调
        :param camera_index:             摄像头编号
        """
        self.on_gesture = on_gesture
        self.on_frame = on_frame
        self.on_error = on_error
        self.camera_index = camera_index
        self.running = False
        self.thread = None
        self.cap = None

        self.recognizer = None
        self._last_gesture = None
        self._gesture_count = 0

    def start(self):
        """启动手势识别线程"""
        if self.thread and self.thread.is_alive():
            return
        self.running = True
        self.thread = threading.Thread(target=self._detect_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """停止手势识别（不阻塞，快速响应）"""
        self.running = False
        # 先释放摄像头，让 cap.read() 立即返回
        if self.cap:
            cap = self.cap
            self.cap = None
            cap.release()
        # 异步关闭识别器
        if self.recognizer:
            try:
                self.recognizer.close()
            except Exception:
                pass
            self.recognizer = None
        self.thread = None

    # ──────────── 主循环 ────────────
    def _detect_loop(self):
        try:
            self.recognizer = HandGestureRecognizer()
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                self._emit_error(f"无法打开摄像头 (设备编号 {self.camera_index})")
                self.running = False
                return

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    continue
                frame = cv2.flip(frame, 1)

                gesture, points = self.recognizer.detect(frame)

                if points:
                    # 在帧上绘制骨骼 + 关键点
                    self._draw_landmarks(frame, points)
                    # 在帧上显示手势名称
                    if gesture:
                        cv2.putText(frame, gesture, (30, 60),
                                    cv2.FONT_HERSHEY_DUPLEX, 1.2,
                                    (0, 255, 170), 2, cv2.LINE_AA)

                    # 防抖触发手势回调
                    self._handle_gesture(gesture)

                # 回调帧给 GUI
                if self.on_frame:
                    self.on_frame(frame)

        except Exception as e:
            self._emit_error(f"手势识别异常：{e}")
        finally:
            if self.cap:
                self.cap.release()
            self.cap = None

    # ──────────── 骨骼绘制 ────────────
    def _draw_landmarks(self, frame, points):
        """在 BGR 帧上绘制 21 个关键点 + 骨骼连线"""
        h, w = frame.shape[:2]

        # 转换归一化坐标 → 像素坐标
        px = [(int(p[0] * w), int(p[1] * h)) for p in points]

        # 绘制连线（青色半透明感）
        for i, j in BONE_CONNECTIONS:
            cv2.line(frame, px[i], px[j], (0, 200, 200), 2, cv2.LINE_AA)

        # 绘制关键点（绿点 + 白边）
        for x, y in px:
            cv2.circle(frame, (x, y), 5, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, (x, y), 4, (0, 255, 170), -1, cv2.LINE_AA)

        # 手腕用更大红点突出
        cv2.circle(frame, px[0], 7, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, px[0], 6, (70, 130, 255), -1, cv2.LINE_AA)

    # ──────────── 防抖 + 回调 ────────────
    def _handle_gesture(self, gesture):
        if gesture == self._last_gesture:
            self._gesture_count += 1
            if self._gesture_count == self.DEBOUNCE_FRAMES and self.on_gesture:
                self.on_gesture(gesture)
        else:
            self._last_gesture = gesture
            self._gesture_count = 1

    def _emit_error(self, msg):
        if self.on_error:
            self.on_error(msg)
