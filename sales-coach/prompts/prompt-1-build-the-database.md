Paste into Claude with Fireflies, Gmail and HubSpot connected.

1. Use the Fireflies API to list every call I hosted in the last [12 months] and download each one's audio into ~/sales-coach/calls/, named by its transcript id.

2. Send each audio file to the Gemini API (gemini-3.8-flash) and transcribe it with speaker labels, timestamps and a tone tag on every line: hesitant, rushed, confident, laughing, flat, or matching their energy. Save each one as calls/[id].json.

3. For every prospect on those calls, pull every email I sent them and every reply from Gmail, with the date and word count.

4. Look up each prospect's deal in HubSpot and record closed won, closed lost or open, plus the amount.

5. Put it all in one SQLite file, ~/sales-coach/sales.db, with calls, emails and deals joined on the prospect.

6. Show me the row counts and any call you couldn't match.
