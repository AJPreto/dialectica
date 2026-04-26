You are answering a closed-world logic benchmark.

Rules:
- Use only the supplied context.
- Do not use outside knowledge.
- If the context contains a contradiction that affects the conclusion, answer conservatively and do not assert a positive conclusion that depends on the contradicted premise.
- Return JSON only.
- Use this exact shape:

```json
{"answer":"yes, no, or unknown","justification":"1-3 short sentences"}
```

Context:
If Bruno holds a cobalt badge or Bruno has temporary clearance, then Bruno may enter the calibration room. If Bruno may enter the calibration room and Bruno is not under safety suspension, then Bruno may start the calibration console. Bruno holds a cobalt badge. Bruno is under safety suspension. Bruno is not under safety suspension.

Question:
May Bruno start the calibration console?
