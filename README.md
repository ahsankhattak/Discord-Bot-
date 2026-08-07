# SlotWise — AI Booking Concierge Bot

An AI-powered booking automation bot built for the DevSynt Summer Internship (AI Automation Engineering track). SlotWise lets users book a restaurant table or a salon appointment through natural conversation on Discord — no forms, no menus, just chat.

## What it does

1. Greets the user and asks if they want to book a table or an appointment
2. Collects service details (party size + occasion for tables, or service type for appointments)
3. Asks for preferred day and time
4. Offers 3 available time slots
5. Collects a phone number to confirm the booking
6. Confirms the booking with a full summary
7. Logs every confirmed booking to Google Sheets automatically
8. Hands off to a human for anything off-script (pricing negotiation, complaints, etc.)

## Tech stack

- n8n — workflow automation engine (local instance)
- Discord — messaging interface, connected via a custom Node.js bridge (discord.js) since n8n doesn't ship a native Discord trigger
- Groq API (Llama 3.3 70B) — handles natural language understanding and tracks conversation state across multiple turns
- Google Sheets — stores confirmed bookings in real time

## How it works

Discord message -> Node.js bridge (discord.js) -> n8n Webhook -> Code node (builds prompt + conversation memory) -> Groq LLM (Llama 3.3 70B) -> Code node (parses structured JSON reply) -> If node (checks booking status)
  - confirmed -> Google Sheets (log booking) -> Discord reply
  - in progress -> Discord reply

The bot maintains conversation memory per Discord channel using n8n's workflow static data, so it remembers earlier answers (party size, date, etc.) instead of repeating questions.

## Files in this repo

- project1/*.json — exported n8n workflow
- project1/*.png — screenshot of the workflow canvas

## Author

Ahsan Khattak — DevSynt AI Automation Engineering Internship
