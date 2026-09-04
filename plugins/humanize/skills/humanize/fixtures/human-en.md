# Put a queue between checkout and the notification service

Twice in the last month (Aug 12, Aug 27) SendGrid returned 503s for about 20 minutes, and both times checkout latency went from 300ms to 4s because `POST /orders` calls the notification service synchronously and the notification service calls SendGrid synchronously. We lost an estimated 1,100 orders on the 27th. Nobody wants email delivery to be able to break checkout.

I want to put an SQS queue between the two. Checkout writes an `OrderPlaced` event and returns; a worker pool drains the queue and talks to SendGrid. That's the whole change. I'm not proposing a general event bus, and I'm not touching SMS or push, which have their own problems but didn't cause an outage.

## Why a queue and not just a timeout

We did add a 500ms timeout in July. It stopped the latency bleed but we still drop the email when SendGrid is down, and support gets tickets. A queue keeps the email and sends it when the provider comes back. Kafka would also work, but we already run SQS for the export jobs and nobody on the team has operated Kafka. I'll take the boring option.

## What changes

- `orders-api`: replace the HTTP call with `sqs.send_message` (about 40 lines, plus a feature flag so we can flip back).
- `notify-worker`: new service, roughly 300 lines, polls with long polling, batch size 10, visibility timeout 2 minutes. On a SendGrid 5xx it doesn't ack, so the message comes back. After 5 attempts it goes to a dead-letter queue and pages on-call.
- Idempotency: the worker keys on `order_id` and checks a 24-hour Redis set before sending, because SQS standard queues can deliver twice. I measured duplicates at 0.02% on the export queue, so it's rare but real.

## What I'm unsure about

Ordering. Standard SQS doesn't preserve order, so a "shipped" email could in theory arrive before "confirmed" if both are queued within seconds. I think this is fine because the templates stand alone, but if product disagrees we'd need a FIFO queue, which caps at 300 msg/s per group. Our peak is 40/s, so even that would work.

## Rollout

Flag on for internal accounts Monday, 5% of traffic Tuesday, 100% by Thursday if the DLQ stays empty. Rollback is the flag; the old code path stays for two weeks.
