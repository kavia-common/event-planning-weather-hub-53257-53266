#!/bin/bash
cd /home/kavia/workspace/code-generation/event-planning-weather-hub-53257-53266/event_planner_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

