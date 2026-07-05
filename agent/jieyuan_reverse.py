import re
import time

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

import cv2
from pathlib import Path

class Status:

    def __init__(self):
        self.init = False
        self.coin = 0
        self.candlelight = 0
        self.ticket = 0
        self.error_times = 0

    def roi_image(self, image, roi):
        x, y, w, h = roi
        image = image[y : y + h, x : x + w]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(
            gray,
            185,
            255,
            cv2.THRESH_BINARY
        )
        binary = cv2.resize(
            binary,
            None,
            fx=3,
            fy=3
        )
        binary_3ch = cv2.cvtColor(
            binary,
            cv2.COLOR_GRAY2BGR
        )
        return binary_3ch

    def ocr(self, context: Context, image):
        reco_detail = context.run_recognition("number_ocr", image)
        try:
            text = int(reco_detail.best_result.text)
            # print(text)
        except Exception as e:
            print("OCR 识别失败:", e)
            self.error_times += 1
            return -1
        return text

    def update(self, context: Context):
        # 这里可以添加一些扫描环境的代码，更新状态
        context.tasker.controller.post_screencap().wait()
        image = context.tasker.controller.cached_image
        coin_roi = [1050, 20, 100, 30]
        ticket_roi = [1190, 20, 100, 30]
        candlelight_roi = [1165, 100, 70, 50]
        coin_crop = self.roi_image(image, coin_roi)
        ticket_crop = self.roi_image(image, ticket_roi)
        candlelight_crop = self.roi_image(image, candlelight_roi)
        # 保存调试图
        Path("debug").mkdir(exist_ok=True)
        cv2.imwrite("debug/coin_roi.png", coin_crop)
        cv2.imwrite("debug/ticket_roi.png", ticket_crop)
        cv2.imwrite("debug/candlelight_roi.png", candlelight_crop)

        self.coin = self.ocr(context, coin_crop)
        self.ticket = self.ocr(context, ticket_crop)
        self.candlelight = self.ocr(context, candlelight_crop)
        self.show()
        self.init = True

    def show(self):
        print(f"coin={self.coin}, candlelight={self.candlelight}, ticket={self.ticket}")


status = Status()


@AgentServer.custom_action("CenterClick")
class CenterClick(CustomAction):
    def run(
        self, 
        context: Context, 
        argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        x, y, w, h = argv.box
        cx, cy = x + w // 2, y + h // 2
        context.tasker.controller.post_click(cx, cy).wait()
        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("enter2choice")
class Enter2choice(CustomAction):

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        count = 0
        while True:
            status.update(context)
            way = choice_way()
            print(f"当前选择: {way}")

            retry_task(context, "enter_changle")
            context.tasker.controller.post_click(
                640,
                360
            ).wait()
            retry_task(context, "start_node", prev_task="enter_changle")
            context.tasker.controller.post_click(
                640,
                360
            ).wait()
            retry_task(context, "answer")
            retry_task(context, "ensure", prev_task="answer")
            if way == "get_coin":
                retry_task(context, "hengruchang", prev_task="ensure")
                retry_task(context, "sure_to_do", prev_task="hengruchang")
                retry_task(context, "skip")
                retry_task(context, "ok")
                time.sleep(3)
                retry_task(context, "take_it")
                retry_task(context, "sure_to_do", prev_task="take_it")
                retry_task(context, "ok")
            elif way == "get_collection":
                retry_task(context, "lirufeng", prev_task="ensure")
                retry_task(context, "sure_to_do", prev_task="lirufeng")
                retry_task(context, "skip")
                retry_task(context, "ok")
                time.sleep(3)
                retry_task(context, "take_collection")
                retry_task(context, "sure_to_do", prev_task="take_collection")
                for i in range(6):
                    context.run_task("pass_collections")
                    time.sleep(2)
                retry_task(context, "ok")
            elif way == "get_ticket":
                retry_task(context, "lirufeng", prev_task="ensure")
                retry_task(context, "sure_to_do", prev_task="lirufeng")
                retry_task(context, "skip")
                retry_task(context, "ok")
                time.sleep(3)
                retry_task(context, "take_ticket")
                retry_task(context, "sure_to_do", prev_task="take_ticket")
                retry_task(context, "ok")
            elif way == "get_candlelight":
                retry_task(context, "lirufeng", prev_task="ensure")
                retry_task(context, "sure_to_do", prev_task="lirufeng")
                retry_task(context, "skip")
                retry_task(context, "ok")
                time.sleep(3)
                retry_task(context, "take_candle")
                retry_task(context, "sure_to_do", prev_task="take_candle")
                retry_task(context, "ok")
            time.sleep(5)
            count += 1
            print(f"完成 { count } 次循环，重新选择")
        return True

def choice_way():
    if status.error_times >= 20:
        exit(1)
    if status.candlelight == 2 and status.coin < 100:
        return "get_error"
    if status.candlelight <= 20 and status.coin >= 100:
        return "get_candlelight"
    if status.candlelight > 20 and status.coin >= 500:
        if status.ticket <= 200:
            return "get_ticket"
        return "get_collection"
    return "get_coin"



def retry_task(
    context: Context,
    task_name: str,
    prev_task:None|str=None,
    retry=3,
    interval=2.0,
):
    print(f"[{task_name}] start ...")
    for i in range(retry):
        result = context.run_task(task_name)
        # print(f"[{task_name}] result = {result}")
        if result:
            # print(f"[{task_name}] success")
            return True
        print(f"[{task_name}] attempt {i+1} failed")
        if prev_task:
            result = context.run_task(prev_task, {"repeat": 1})
        time.sleep(interval)
    print(f"[{task_name}] all retry failed")
    return False
