#!/bin/bash
ollama create pixy -f Pixy.modelfile 
ollama run pixy:latest
python3 code/main.py
echo pixy out
