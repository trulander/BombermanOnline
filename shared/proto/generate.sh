#!/bin/bash

#the script must be run from the root directory of any service that use the proto like game-service or ai-service

python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. ./app/shared/proto/bomberman_ai.proto

