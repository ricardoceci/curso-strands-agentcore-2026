import aws_cdk as cdk
from cdk_weather_lambda.stack import WeatherLambdaStack

app = cdk.App()

WeatherLambdaStack(
    app,
    "WeatherLambdaStack",
    # La cuenta y región se leen de las variables de entorno AWS_DEFAULT_REGION
    # y CDK_DEFAULT_ACCOUNT al hacer `cdk deploy`.
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region"),
    ),
)

app.synth()
