import re
import time

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

import cv2
from pathlib import Path

class Resource:
    def __init__(self):
        self.component = 0
        self.device = 0
    
    def roi_image(self, image, roi):
        x, y, w, h = roi
        roi_img = image[y:y+h, x:x+w]
        gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        # Otsu 自动计算最佳阈值
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary = cv2.resize(binary, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
        binary_3ch = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        return binary_3ch
    
    def ocr(self, context: Context, image):
        reco_detail = context.run_recognition("number_ocr", image)
        try:
            text = reco_detail.best_result.text
            # print(text)
        except Exception as e:
            print("OCR 识别失败:", e)
            exit(1)
        return text

    def update(self, context: Context):
        # 这里可以添加一些扫描环境的代码，更新状态
        context.tasker.controller.post_screencap().wait()
        image = context.tasker.controller.cached_image
        compent_roi = [228,36,62,23]
        device_roi = [391,35,65,23]
        compent_crop = self.roi_image(image, compent_roi)
        device_crop = self.roi_image(image, device_roi)
        # 保存调试图
        Path("debug").mkdir(exist_ok=True)
        cv2.imwrite("debug/compent_roi.png", compent_crop)
        cv2.imwrite("debug/device_roi.png", device_crop)

        self.component = int(self.ocr(context, compent_crop))
        self.device = int(self.ocr(context, device_crop))
        self.show()
        self.init = True
    
    def show(self):
        print(f"compents={self.component}, devices={self.device}")

resource = Resource()

@AgentServer.custom_action("Reclamation_algorithm")
class Reclamation_algorithm(CustomAction):
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        max_times = 1
        for _ in range(max_times):
            # todo
            resource.update(context)
            context.run_task("enter_ra_4")
        return True
        