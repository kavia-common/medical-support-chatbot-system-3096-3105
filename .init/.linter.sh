#!/bin/bash
cd /home/kavia/workspace/code-generation/medical-support-chatbot-system-3096-3105/medical_chatbot_frontend
npm run build
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
   exit 1
fi

