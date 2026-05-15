# gesture/camera_preview.py — 摄像头实时预览（纯画面，无手势识别）
import threading
import cv2


class CameraPreview:
    """
    摄像头预览类：独立线程读取摄像头画面，通过回调传递给 GUI。
    暂不做任何手势识别，只负责画面采集与分发。
    """
    def __init__(self, on_frame=None, on_error=None, camera_index=0):
        """
        :param on_frame(frame_bgr):  每捕获一帧回调，传 BGR 格式 numpy 数组
        :param on_error(msg):        摄像头打开失败等错误回调
        :param camera_index:         摄像头设备编号，默认 0（前置摄像头）
        """
        self.on_frame = on_frame
        self.on_error = on_error
        self.camera_index = camera_index
        self.running = False
        self.thread = None
        self.cap = None

    def start(self):
        """启动摄像头预览线程"""
        if self.thread and self.thread.is_alive():
            return

        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """停止摄像头预览"""
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.thread:
            self.thread.join(timeout=1.5)
        self.thread = None

    def _capture_loop(self):
        """摄像头线程主循环"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                if self.on_error:
                    self.on_error(f"无法打开摄像头 (设备编号 {self.camera_index})")
                self.running = False
                return

            # 设置较低分辨率以提高流畅度
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    continue
                # 水平镜像（模拟镜子效果）
                frame = cv2.flip(frame, 1)

                if self.on_frame:
                    self.on_frame(frame)

        except Exception as e:
            if self.on_error:
                self.on_error(f"摄像头异常：{e}")
        finally:
            if self.cap:
                self.cap.release()
            self.cap = None
