import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, CompletionsFinishReason
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.core.tracing.decorator import distributed_trace
from azure.core.settings import settings
from azure.core.tracing.ai.inference import AIInferenceInstrumentor


def setup_azure_monitor_trace_exporter():
    from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    connection_string = os.environ.get("APPINSIGHTS_CONNECTIONSTRING")
    span_processor = BatchSpanProcessor(
        AzureMonitorTraceExporter.from_connection_string(
            connection_string
        )
    )
    trace.get_tracer_provider().add_span_processor(span_processor)


def setup_console_trace_exporter():
    exporter = ConsoleSpanExporter()
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(exporter))


def sample_chat_completions():
    import os

    try:
        endpoint = "{}openai/deployments/{}".format(
            os.environ['AZURE_OPENAI_ENDPOINT'], os.environ['AZURE_OPENAI_CHAT_DEPLOYMENT'])

    except KeyError:
        print(
            "Missing environment variable 'AZURE_AI_CHAT_ENDPOINT' or 'AZURE_AI_CHAT_KEY'")
        print("Set them before running this sample.")
        exit()

    # [START chat_completions]
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(
            exclude_interactive_browser_credential=False),
        credential_scopes=["https://cognitiveservices.azure.com/.default"],
        api_version="2023-03-15-preview",
        logging_enable=True,
    )

    response = client.complete(
        messages=[
            SystemMessage(content="You are a helpful assistant."),
            UserMessage(content="How many feet are in a mile?"),
        ]
    )

    print(response.choices[0].message.content)
    # [END chat_completions]


if __name__ == "__main__":
    settings.tracing_implementation = "OpenTelemetry"

    # setup_console_trace_exporter()
    setup_azure_monitor_trace_exporter()

    # Instrument AI Inference API
    AIInferenceInstrumentor().instrument()

    sample_chat_completions()
    print("===== chat_with_function_tool() done =====")
    AIInferenceInstrumentor().uninstrument()
