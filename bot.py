import os
import random
import pandas as pd
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# ✅ Clés API depuis variables Render
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ✅ Lecture des situations
df = pd.read_csv("SITUATIONS.csv", sep="