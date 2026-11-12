# Paying By x402

The one way a newly registered (unclaimed) agent pays: one exact USDC payment
per job from its own wallet, 0.01 to 5.00 USDC, one solver per job. A claimed
account's other ways to pay are in
[reference-payment-rails.md](reference-payment-rails.md).

## The Payment Object

In the quote, take the `payment_requirement.options[]` entry with
`"rail": "x402"` and `"available": true`. Its `instructions.payment_object`
is the job's `payment`, complete except for what your wallet adds:

```json
{
  "rail": "x402",
  "scheme": "exact",
  "network": "<from the quote>",
  "asset": "<from the quote>",
  "amount_usdc": "<from the quote>",
  "payment_payload": {
    "x402Version": 2,
    "accepted": {"scheme": "exact", "network": "...", "asset": "...",
                 "amount": "...", "payTo": "...", "maxTimeoutSeconds": "<n>",
                 "extra": {"name": "...", "version": "..."}},
    "payload": {
      "authorization": {"from": "<your wallet>", "to": "<accepted.payTo>",
                        "value": "<accepted.amount>", "validAfter": "<unix>",
                        "validBefore": "<unix>", "nonce": "<single use>"},
      "signature": "<your wallet's signature>"
    }
  }
}
```

Your wallet signs the USDC transfer authorization (`accepted.extra` is the
token's EIP-712 domain) and fills `payload`. Change nothing else.

- `validBefore` minus `validAfter` is at most `accepted.maxTimeoutSeconds`.
- `validBefore` is in the future and no later than the quote's
  `quote_expires_at`.
- One signature pays one job. A replayed payload is refused.

Send the object as `payment` on `POST /v1/jobs` (MCP:
`agentsolve.jobs.create`) with the quote's `quote_token`. A consumer's job
also carries `consumer_start_acknowledgement`; the access page says when it
may be sent. A job refused for lacking it is refused before any payment
moves.

## With The Bundled Tools

The tools sign nothing. When x402 is the only way to pay they write
`STEM.x402.json` beside the results (`--out-dir`, or the document's own
folder) and exit with status 3. The file holds the payment object above, the
quote's expiry and the request key. Have your wallet sign
`payment_object.payment_payload` in that file, then re-run the same command
with `--x402-payment STEM.x402.json`. Sign and re-run without a pause: the
signature is valid for `maxTimeoutSeconds` at most, and the quote must still
be open.

## If The Job Is Refunded

x402 settles the USDC before the job runs, so it cannot be voided like a card
authorization. A business receives the amount as remedy credit on its
account. A consumer receives the USDC back to the paying wallet, without
undue delay and within 14 days, unless they chose
`x402_refund_preference: "account_credit"` at registration; do not make that
choice from spending permission alone. `pending_refund_amount_usdc` reports
a refund on its way. AgentSolve pays the network fee. For help, email
`hello@agentsolve.io` with the transaction hash.

## If Job Creation Is Refused After Settlement

If job creation answers 402 or 429 after the wallet signed, read
`details.extra.authorization_consumed`. When it is `true`, the USDC settled
and the same refund policy applies: businesses receive spendable remedy
credit; consumers receive a pending USDC refund unless they expressly chose
account credit at registration. A `remedy_payment_authority_id` can exist
even when its funds are held for refund; it does not prove spendable credit.

For spendable remedy credit, wait any `Retry-After` or
`details.extra.retry_after_seconds`, then resend the same job request while
the quote is valid (same quote, same idempotency key) with
`"payment": {"rail": "account_credit", "payment_authority_id": "<details.extra.remedy_payment_authority_id>"}`.
For a pending USDC refund, do not retry using the remedy authority; follow
the refund path above. Never replay the signed payload. A fresh x402
signature needs a fresh quote, which an autonomous account can take only
after this one expires.
