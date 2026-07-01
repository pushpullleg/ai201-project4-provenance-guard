# pg-ratelimit

Test rate limiting on POST /submit. Fires 12 rapid requests and captures the HTTP status codes showing the 429 responses — this output is the evidence needed for the README.

## Steps

1. Confirm the app is running:
   ```bash
   curl -s http://localhost:5001/log > /dev/null && echo "App running" || echo "Start: python3 app.py"
   ```

2. Fire 12 rapid requests and capture status codes:
   ```bash
   for i in $(seq 1 12); do
     curl -s -o /dev/null -w "Request $i: %{http_code}\n" -X POST http://localhost:5001/submit \
       -H "Content-Type: application/json" \
       -d '{"text": "This is a rate limit test submission number '"$i"'.", "creator_id": "ratelimit-test"}'
   done
   ```

3. Expected output:
   ```
   Request 1:  200
   Request 2:  200
   ...
   Request 10: 200
   Request 11: 429
   Request 12: 429
   ```

4. If you see 429s after request 10: PASS — rate limiting is working.

5. If all 12 return 200:
   - Check that `@limiter.limit("10 per minute;100 per day")` decorator is on the `/submit` route in `app.py`
   - Check that `Limiter` is initialized with `storage_uri="memory://"` 
   - Restart the app and try again — the counter resets on restart

6. If you see an error instead of 429:
   - Check the Flask startup output for limiter warnings
   - Verify Flask-Limiter version: `pip show flask-limiter`

7. Copy and save the status-code output — paste it into the README rate limiting section
   as the evidence for the grader.

## Note on the minute window
The 10/minute limit uses a sliding window. If you need to re-run this test,
wait 60 seconds or restart the app to reset the in-memory counter.
