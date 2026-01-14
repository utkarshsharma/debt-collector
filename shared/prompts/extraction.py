"""
Extraction prompt for post-call analysis.

This prompt is used with GPT-5.2 to extract structured data from call transcripts
and produce a CallExtraction object.
"""

EXTRACTION_PROMPT = """
You are analyzing a debt collection call transcript. Extract the following information
and return it as a JSON object. Be precise and only include information that is
explicitly stated or clearly implied in the transcript.

## Required Output Schema

```json
{
  "confirmed_identity": boolean,  // Did the debtor verify their identity?
  "speaking_with_debtor": boolean,  // Were we speaking with the actual debtor?
  "wrong_number": boolean,  // Was this a wrong number?

  "outcome": string,  // One of: "promised_to_pay", "partial_promise", "disputed",
                      // "hardship", "wrong_number", "no_answer", "voicemail",
                      // "callback_requested", "refused_to_pay", "hung_up", "other"

  "promise_made": boolean,  // Did they make a payment promise?
  "promise": {  // Only if promise_made is true
    "amount": number,  // Amount promised (as decimal, e.g., 150.00)
    "promise_date": string  // Date promised in YYYY-MM-DD format
  } | null,

  "hardship_reason": string | null,  // If they claimed hardship, what was the reason?
  "dispute_reason": string | null,  // If they disputed, what was the reason?

  "callback_requested": boolean,  // Did they request a callback?
  "preferred_callback_time": string | null,  // If callback requested, when?

  "requested_no_calls": boolean,  // Did they ask to stop receiving calls?

  "debtor_sentiment": integer,  // 1-5 scale: 1=hostile, 2=frustrated, 3=neutral, 4=cooperative, 5=very cooperative

  "call_summary": string,  // 2-3 sentence summary of the call (10-500 chars)

  "final_state": string  // One of: "greeting", "verification", "purpose",
                         // "negotiation", "objection_handling", "commitment",
                         // "closing", "wrong_number", "hardship", "callback"
}
```

## Rules

1. **Identity Verification**
   - `confirmed_identity` = true only if they correctly verified (account number, DOB, etc.)
   - `speaking_with_debtor` = true only if we confirmed we're speaking with the named person
   - `wrong_number` = true if the person says the debtor doesn't live there or we reached the wrong person

2. **Payment Promise**
   - `promise_made` = true only if they explicitly agreed to pay a specific amount by a specific date
   - `promise.amount` must be greater than 0
   - `promise.promise_date` must be a valid future date in YYYY-MM-DD format
   - If they said "I'll try to pay" without specific amount/date, that is NOT a promise

3. **Outcome Classification**
   - "promised_to_pay": Full payment commitment made
   - "partial_promise": Committed to pay less than full amount
   - "disputed": They dispute owing the money
   - "hardship": They expressed financial difficulty
   - "callback_requested": They asked us to call back later
   - "refused_to_pay": Explicitly said they won't pay
   - "hung_up": They ended the call abruptly
   - "wrong_number": Not the correct person

4. **Sentiment Scale**
   - 1 = Hostile (threatening, swearing, aggressive)
   - 2 = Frustrated (annoyed, short, defensive)
   - 3 = Neutral (matter-of-fact, neither positive nor negative)
   - 4 = Cooperative (willing to discuss, receptive)
   - 5 = Very Cooperative (appreciative, proactive about resolving)

5. **Call Summary**
   - Write a brief 2-3 sentence summary
   - Focus on: who answered, what was discussed, what was the outcome
   - Keep it between 10-500 characters

6. **Final State**
   - Indicate which conversation state the call ended in
   - Most successful calls end in "closing"
   - If they hung up during verification, final_state = "verification"

## Important

- If information is not available, use null for optional fields
- If `promise_made` is false, `promise` MUST be null
- If `promise_made` is true, `promise` MUST have valid amount and date
- Do NOT guess or make up information not in the transcript
- Return ONLY the JSON object, no additional text
"""
