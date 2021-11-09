# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import Telemetry_pb2 as Telemetry__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


class TelemetryModuleStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.PostTelemetry = channel.stream_unary(
                '/TelemetryModule/PostTelemetry',
                request_serializer=Telemetry__pb2.Telemetry.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )


class TelemetryModuleServicer(object):
    """Missing associated documentation comment in .proto file."""

    def PostTelemetry(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_TelemetryModuleServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'PostTelemetry': grpc.stream_unary_rpc_method_handler(
                    servicer.PostTelemetry,
                    request_deserializer=Telemetry__pb2.Telemetry.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'TelemetryModule', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class TelemetryModule(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def PostTelemetry(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_unary(request_iterator, target, '/TelemetryModule/PostTelemetry',
            Telemetry__pb2.Telemetry.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
