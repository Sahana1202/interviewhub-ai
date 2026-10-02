# College Query Chatbot

A simple AI-style chatbot for answering college-related questions on a website.

## Features

- Ask about fees, timetable, and departments
- Instant responses through a lightweight backend API
- Website-ready chat interface
- Easy-to-edit college data stored in one place

## Project Structure

- `server.js` handles the web server and chatbot API
- `data/collegeData.js` stores sample college information and response logic
- `public/` contains the website UI

## Run the Project

```bash
npm start
```

Then open `http://localhost:3000`.

## Customize It

Edit `data/collegeData.js` to update:

- College name
- Fees
- Timetable
- Departments
- Contact details
- Suggested quick reply questions

## Website Integration

This project already exposes a reusable endpoint:

- `POST /api/chat`

Example request body:

```json
{
  "message": "What are the B.Tech fees?"
}
```

Example response:

```json
{
  "reply": "B.Tech annual tuition fee is Rs. 95,000."
}
```
