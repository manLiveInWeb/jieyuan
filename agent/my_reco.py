from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context


@AgentServer.custom_recognition("my_reco_222")
class MyRecongition(CustomRecognition):

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        
        import cv2
        cv2.imwrite('test.png', argv.image)
        print("my_reco_222 is analyzing!")

        return CustomRecognition.AnalyzeResult(
            box=(100, 100, 100, 100), detail="Hello World!"
        )
