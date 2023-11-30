#!/bin/bash
uvicorn score:app --host 0.0.0.0 --port $PORT