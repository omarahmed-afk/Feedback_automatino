# WebPT visits automation

`visits.py` exports today's visits from WebPT and appends history to the Google Sheet's
`All` and `Initial Examination` tabs. The report date uses America/New_York.

Visits are matched by EMR ID, clinic, patient name, appointment type, and date
(A:E). Existing visits have only their status in F updated. New visits are
appended in A:F; column G (Phone), including its header and formatting, is never
written. Add the Phone header manually on a new tab if desired. Visits on a
different date get a new row. Empty reports leave
history intact. History accumulates from subsequent runs; past dates are not
automatically backfilled. Local Excel tests still produce a single-run workbook.

## GitHub Actions setup

1. Add `visits.py`, `requirements.txt`, `.gitignore`, this README, and
   `.github/workflows/visits.yml` to your GitHub repository's default branch.
   Keep the local Google service account JSON key, CSV exports, Excel files,
   and timeout screenshots out of the repository.
2. Under **Settings > Secrets and variables > Actions > New repository secret**,
   create these four secrets:

   | Secret | Value |
   | --- | --- |
   | `WEBPT_USERNAME` | Your WebPT login username |
   | `WEBPT_PASSWORD` | Your WebPT login password |
   | `GOOGLE_SHEET_ID` | The text between `/d/` and `/edit` in your Sheet URL |
   | `GOOGLE_SERVICE_ACCOUNT_JSON` | The complete contents of your local service account JSON key file, including braces |

3. Enable the Google Sheets and Google Drive APIs in the service account's
   Google Cloud project. Share the target spreadsheet with the key's
   `client_email` as **Editor**.
4. Open **Actions > WebPT visits > Run workflow** whenever you want to run it.
   A successful run updates the live spreadsheet.

The workflow runs only when you start it manually. There is no automatic schedule.

Each job runs once using headless Chrome on Ubuntu, with a 20-minute timeout.
Selenium manages the Chrome driver. Runs are serialized to avoid concurrent
sheet updates. Missing configuration, browser failures, and missing or empty
CSV downloads fail the job. Logs appear in Actions; exports and screenshots
are not uploaded as artifacts. WebPT must allow an unattended login from the
GitHub runner; an interactive MFA challenge would require additional handling.

## Local runs

Install dependencies with `python -m pip install -r requirements.txt`.
Set `WEBPT_USERNAME`, `WEBPT_PASSWORD`, and `GOOGLE_SHEET_ID` in your environment.
For Google authentication, set `GOOGLE_SERVICE_ACCOUNT_JSON` or
`GOOGLE_SERVICE_ACCOUNT_FILE`; the existing local key filename is still the
default for local use. Then run `python visits.py`.

Run `python visits.py --test-excel` for a sample-data Excel smoke test without
logging into WebPT or modifying Google Sheets. Each local run executes once
when you start it; there is no built-in scheduling loop.
