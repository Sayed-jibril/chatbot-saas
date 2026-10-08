# BotSaaS - AI Chatbot Platform

A multi-tenant AI chatbot platform where users can create custom chatbots trained on their own data.

## Features

- Multi-user support with plan limits
- Upload documents (PDF, DOCX, TXT)
- AI-powered responses using OpenAI
- Embed chatbots via iframe or JavaScript widget
- Analytics dashboard
- Token usage tracking

## Installation

1. Create database: `mysql -u root -p < database_schema.sql`
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.env` file
4. Run: `cd app && python main.py`

## Default Admin

- Email: admin@example.com
- Password: admin123
