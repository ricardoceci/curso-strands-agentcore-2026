from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as lambda_,
)
from constructs import Construct


class WeatherLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # El handler solo usa stdlib (urllib), no necesita bundling ni capas extra.
        weather_fn = lambda_.Function(
            self,
            "WeatherFunction",
            function_name="agentcore-weather-tool",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            description="get_weather tool expuesto via AgentCore Gateway Lambda target",
        )

        # Resource-based policy: permite que AgentCore Gateway invoque la función.
        # AgentCore usa bedrock-agentcore.amazonaws.com como service principal.
        # source_account evita el confused deputy problem.
        weather_fn.add_permission(
            "AllowAgentCoreGateway",
            principal=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=self.account,
        )

        self.lambda_arn = weather_fn.function_arn

        CfnOutput(
            self,
            "WeatherLambdaArn",
            value=weather_fn.function_arn,
            description="ARN de la Lambda — úsalo como WEATHER_LAMBDA_ARN en el .env",
        )
