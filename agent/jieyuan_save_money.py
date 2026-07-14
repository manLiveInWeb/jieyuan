import re
import time

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

import cv2
from pathlib import Path

class ShopStatus:

    def __init__(self):
        self.init = False
        self.coin_history = []
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
        coin_roi = [139,488,42,22]
        coin_crop = self.roi_image(image, coin_roi)
        # 保存调试图
        Path("debug").mkdir(exist_ok=True)
        cv2.imwrite("debug/shop_coin.png", coin_crop)
        cv2.imwrite("debug/full_shop_coin.png", image)

        self.coin_history.append(self.ocr(context, coin_crop))
        self.show()
        self.init = True

    def show(self):
        if len(self.coin_history) == 1:
            print(f"当前余额: {self.coin_history[-1]}")
        else:
            print(f"当前余额: {self.coin_history[-1]}(本轮存钱：{self.coin_history[-1] - self.coin_history[-2]})")


status = ShopStatus()

recruitment_times = 3
retry_times = 4
target = "代币"

@AgentServer.custom_action("save_money_epoch")
class SaveMoney(CustomAction):

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        status.update(context)
        start = time.perf_counter()
        loop = 0
        while True:
            lucky = False
            EnterJieyuan().run(context, argv)
            for _ in range(retry_times):
                context.run_task("coin_view")
                context.tasker.controller.post_screencap().wait()
                image = context.tasker.controller.cached_image
                crop = [59,301,816,38]
                x, y, w, h = crop
                image = image[y : y + h, x : x + w]
                cv2.imwrite("debug/info_test.png", image)
                result = context.run_recognition("text_ocr", image)
                key_texts = [res.text for res in result.filtered_results]
                detail_key_texts = [text[-2:] for text in key_texts]
                print(f"识别结果: {key_texts}")
                if target in detail_key_texts:
                    print(f"识别到目标钱币: {target}\n执行存钱分支")
                    lucky = True
                    context.run_task("throw_target")
                    break
                context.run_task("retry_throw")
            if not lucky:
                context.run_task("back_view")
                print("未投出目标钱币，结束存钱任务")
            else:
                print("已投出目标钱币，结束存钱任务")
            context.run_task("exit_game")
            time.sleep(5)
            loop += 1
            print(f"探索第{loop}次结束")
            if lucky:
                status.update(context)
            if status.coin_history[-1] >= 900:
                print("余额已达上限，结束存钱任务")
                break
        end = time.perf_counter()
        elapsed = end - start
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = elapsed % 60
        print(f"耗时: {hours:02d}:{minutes:02d}:{seconds:06.3f},每小时存源石锭{(status.coin_history[-1] - status.coin_history[0]) / (elapsed / 3600):.2f}秒")
        return True

class EnterJieyuan(CustomAction):

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        print("开始执行存钱任务")
        context.run_task("enter_jieyuan")
        print("放弃三次招募更快")
        for _ in range(recruitment_times):
            context.run_task("recruitment")
        print("进入界园")
        context.run_task("enter_game")
        print("查看钱盒")
        context.run_task("enter_box")
        return True


