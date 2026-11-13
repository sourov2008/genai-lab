# Error Alerting Workflow (n8n) SOP

This SOP describes how to receive ClauseDesk extraction-failure alerts in n8n and how to import a workflow JSON after you export it.

When `extract_clauses_from_contract` still cannot parse valid JSON after two attempts, the API sets the contract to `FAILED` and `app/services/n8n_service.py` POSTs:

```json
{
  "contract_id": 1,
  "error": "…",
  "level": "error",
  "source": "ClauseDesk API"
}
```

If `N8N_WEBHOOK_URL` is empty, the API logs a warning and skips the POST. If n8n is down, the API logs the error and does not crash.

---

## Setup

1. **Create a Webhook node in n8n. Set to POST.**
   - Open n8n (local Docker: http://localhost:5678).
   - New workflow → add a **Webhook** node.
   - HTTP Method: **POST**.
   - Path: any unique path (n8n generates one if you leave the default).
   - Respond: **Immediately** (or “When Last Node Finishes”) so FastAPI is not blocked waiting for email/Slack.
   - Save the workflow and **Activate** it. Copy the **Production** URL, not the Test URL, unless you are clicking “Listen for Test Event”.

2. **Copy the Webhook URL and paste it into FastAPI's `.env` as `N8N_WEBHOOK_URL`.**
   - In `clausedesk/.env` set:

     ```
     N8N_WEBHOOK_URL="https://your-n8n-host/webhook/…"
     ```

   - Keep `N8N_WEBHOOK_SECRET` in `.env` for later auth; this first workflow does not require it.
   - Restart the API so `get_settings()` reloads the file.

3. **Connect the Webhook node to a "Send Email" or "Slack" node for notifications.**
   - Drag from the Webhook output to **Send Email** (SMTP / Gmail) or **Slack** (channel message).
   - Map fields from the webhook JSON, for example:
     - Subject / title: `ClauseDesk extraction failed (contract {{ $json.contract_id }})`
     - Body: `{{ $json.error }}` (source: `{{ $json.source }}`, level: `{{ $json.level }}`)
   - Execute a test: fail an extraction (or POST the JSON above with `curl` to the webhook URL) and confirm the email or Slack message arrives.

---

## Daily Eval Digest

This workflow pulls `GET /analytics/daily-digest` once a day and sends a readable summary (token usage, cost, contracts processed/failed for the last 24 hours). The endpoint requires a JWT (`get_current_user`).

1. **Create a new workflow in n8n.**
   - Open n8n (local Docker: http://localhost:5678).
   - New workflow. Name it something like `ClauseDesk daily eval digest`.

2. **Add a "Schedule Trigger" node (set to run daily at 9:00 AM).**
   - Trigger interval: **Days**, every **1** day.
   - Trigger at: **9:00 AM**.
   - Timezone: match `GENERIC_TIMEZONE` on the n8n container (currently `Europe/Berlin`) so 9:00 is the hour you expect.

3. **Add an "HTTP Request" node: GET `http://host.docker.internal:8000/analytics/daily-digest` (Requires Bearer Token).**
   - Method: **GET**.
   - URL: `http://host.docker.internal:8000/analytics/daily-digest` (n8n in Docker reaching the API on the host). If the API also runs in Compose as `api`, you can use `http://api:8000/analytics/daily-digest` instead.
   - Authentication: **Generic Credential Type** → **Header Auth**, or set header `Authorization` to `Bearer <JWT>`.
   - Obtain a token from `POST /auth/login`, then store it in n8n credentials (do not hard-code it in the exported JSON).
   - Connect Schedule Trigger → HTTP Request.

4. **Add a "Send Email" or "Slack" node to format the JSON data into a readable message and send it.**
   - Connect HTTP Request → **Send Email** or **Slack**.
   - Example body using the digest keys:

     ```
     ClauseDesk daily digest (last {{ $json.period_hours }}h)
     Runs: {{ $json.total_runs }}
     Input tokens: {{ $json.total_input_tokens }}
     Output tokens: {{ $json.total_output_tokens }}
     Cost USD: {{ $json.total_cost_usd }}
     Contracts processed: {{ $json.contracts_processed }}
     Contracts failed: {{ $json.contracts_failed }}
     ```

   - Activate the workflow. Use **Execute Workflow** once to confirm email/Slack before waiting for 9:00 AM.

---

## Importing an exported workflow JSON

After you export the workflow from n8n (workflow menu → **Download** / **Export**), store the JSON with the project (for example `docs/n8n_error_alert.json`) and import it on another machine as follows.

1. Open n8n.
2. From the workflows list, choose **Import from File** (or **Import from URL** if the JSON is hosted).
3. Select the exported `.json` file.
4. Confirm the canvas shows the Webhook node plus Email or Slack.
5. Open the Webhook node and copy the **new** Production URL (n8n assigns webhook IDs per instance).
6. Paste that URL into `.env` as `N8N_WEBHOOK_URL` and restart the API.
7. Re-enter credentials on Email/Slack nodes if they did not travel with the export, then **Activate** the workflow.

Do not commit secrets (SMTP passwords, Slack tokens, or a live `N8N_WEBHOOK_URL` with credentials) in the exported JSON or in git.
