# Mail monitoring design

## Problem

The dashboard needs an admin-first view of inbound mailing-list traffic handled by `datmail`, including:

- one row per inbound mail
- current deliverability visibility for that mail
- downloadable archived `.eml`
- retry support for failed recipient deliveries

`datmail` already stores the raw inbound message in S3 as `archive/<request_uuid>.eml`. The missing piece is a durable event flow from `datmail` into Django plus Django-side models/admin views for monitoring and retry operations.

## Goals

- Make Django the source of truth for monitoring inbound mail state
- Keep `datmail` as the authority for mail-forwarding behavior and header construction
- Preserve enough audit history to show original sends, failures, bounces, and resends
- Support downloading the archived raw inbound `.eml` through Django admin
- Make resend behavior explicit and traceable without mutating history

## Non-goals

- Replacing the current `datmail` forwarding pipeline
- Designing the full AWS SNS / SES webhook implementation in detail
- Making resend byte-for-byte identical without using `datmail`'s own resend path

## Recommended architecture

Use Django as the persistence and admin/UI layer, and `datmail` as the event producer and resend executor.

### Responsibilities

#### Django

- persists inbound mail, archive references, and forwarding attempts
- exposes authenticated ingest endpoints for `datmail`
- provides admin views, stats, presigned archive download, and resend buttons

#### datmail

- accepts inbound SMTP traffic
- archives raw inbound `.eml` to S3
- resolves mailing-list recipients
- forwards mail using its existing header/body logic
- reports mail events to Django
- performs resend requests from Django so the same forwarding logic is reused

## Data model

These models belong in the existing Django `mail` app.

### `MailArchive`

- `id` primary key
- `request_uuid` UUID, unique
- `created_at` datetime
- `s3_object_key` string, for example `archive/<request_uuid>.eml`

Notes:
- The S3 objects for MailArchive will live in the mail-archive bucket. 
- Store the S3 object key, not a presigned URL
- Django generates presigned URLs on demand in admin

### `IncomingMail`

- `id` primary key
- `received_at` datetime
- `sender` string
- `target` string containing the original inbound mailing-list address as received
- `mailing_list` nullable foreign key to the existing `MailingList` model
- `mail_archive` one-to-one to `MailArchive`
- `status` enum: `PROCESSED`, `DROPPED`
- `reason` text/string for rejection/drop explanation

Notes:

- An `IncomingMail` row is created for both processed and dropped mail
- Only one original inbound mailing-list target is expected per `IncomingMail`

### `ForwardedMail`

- `id` primary key
- `incoming_mail` foreign key to `IncomingMail`
- `target` string containing the expanded final recipient email
- `status` enum: `FORWARDED`, `FAILED`, `BOUNCED`
- `forwarded_at` datetime
- `reason` nullable text/string for synchronous send failures or bounce details
- `previous_attempt` nullable self foreign key pointing to the earlier failed/bounced attempt when this row is a resend

Notes:

- A resend creates a new `ForwardedMail` row; it does not rewrite the old row
- `previous_attempt` provides an explicit retry chain for audit and UI display
- The `ForwardedMail` retry entity should stay close to the original forward entity in the UI display (for correlation).

## Event flow

### 1. Inbound mail recorded after processing outcome is known

When `datmail` finishes the relevant relay decision flow for an inbound message and knows whether the mail was processed or dropped, it calls a Django API endpoint keyed by `request_uuid`.

Payload should include:

- `request_uuid`
- `received_at`
- `sender`
- original inbound `target`
- optional resolved `mailing_list` identifier when known
- `status`
- `reason` when dropped
- `s3_object_key`
- `expanded_recipients` list when the mail was processed and recipient expansion happened

Django behavior:

- upsert `MailArchive` by `request_uuid`
- create or update `IncomingMail`
- bulk-create one initial `ForwardedMail` row per expanded recipient only when `IncomingMail.status = PROCESSED`

For dropped mail:

- create `IncomingMail` with `status = DROPPED`
- store the drop reason for UI display
- do not create any `ForwardedMail` rows

### 2. Synchronous forwarding failure updates

If `datmail` learns that a forwarded recipient failed during relay handoff, it calls Django to update the corresponding `ForwardedMail` row from `FORWARDED` to `FAILED` and stores the failure reason.

This status is intentionally separate from `BOUNCED`:

- `FAILED` means `datmail` or its relay path could not hand the message off successfully
- `BOUNCED` means the downstream provider accepted the send and later reported a bounce

### 3. Bounce updates

Later, AWS SNS / SES webhook handling in Django updates the matching `ForwardedMail` row to `BOUNCED` and stores the bounce details in `reason` or a future dedicated field.

## API shape

Keep the API small and idempotent.

### Endpoint set

1. `upsert incoming mail`
   - creates or updates `MailArchive` and `IncomingMail`
   - creates initial `ForwardedMail` rows from the expanded recipient list
2. `patch forwarded attempt`
   - marks existing `ForwardedMail` rows as `FAILED` when relay handoff fails
3. `resend forwarded attempt`
   - called by Django admin toward `datmail`, not the other way around

### Authentication

- Use the existing granular API-key mechanism in Django for `datmail` -> Django calls
- Use a separate authenticated mechanism for Django -> `datmail` resend requests
- Scope credentials narrowly to mail-monitoring endpoints

### Idempotency

The `upsert incoming mail` endpoint must be idempotent on `request_uuid`.

Repeated calls must not:

- duplicate `MailArchive`
- duplicate `IncomingMail`
- recreate the initial `ForwardedMail` set

The simplest implementation is to treat the initial `(incoming_mail, target, previous_attempt IS NULL)` rows as unique for the first delivery wave.

## Admin UX

### Incoming mails changelist

Create a Django admin page named `Incoming mails`.

Each row should show:

- received time
- sender
- original target
- processing status
- recipient counts derived from the latest attempt per recipient chain
- counts for current forwarded / failed / bounced outcomes
- whether resend attempts exist

Default admin behavior:

- show only `IncomingMail` rows with `status = PROCESSED`
- provide an easy filter to include or switch to `DROPPED` rows

### Incoming mail detail

Show:

- core metadata from `IncomingMail`
- a download action or button that generates a presigned URL for the archived `.eml`
- inline `ForwardedMail` attempts with:
  - target
  - status
  - forwarded time
  - reason
  - previous attempt

### Deliverability stats

Stats must be computed from the latest attempt in each retry chain, not by counting every `ForwardedMail` row equally.

Example:

- first attempt to `a@example.com` failed
- resend succeeded

The current state for that recipient is `FORWARDED`, even though the history still contains a failed row.

## Resend design

Resend must reuse `datmail`'s forwarding logic so the same headers and transformations are applied as in the original forward.

### Why Django should not send the resend directly

Django's SMTP backend sends directly to Postfix -> SES and bypasses `datmail`. If Django sent the resend itself, it would need to duplicate `datmail`'s forwarding logic, including:

- list headers
- `From` / `Reply-To` rewriting
- any optional body rewriting
- any other future forwarding rules

That duplication would drift over time.

### Resend flow

1. An admin clicks resend on a `FAILED` or `BOUNCED` `ForwardedMail`
2. Django calls an authenticated resend endpoint in `datmail` with:
   - `request_uuid`
   - `incoming_mail_id`
   - `forwarded_mail_id`
   - retry `target`
3. `datmail` loads the archived inbound `.eml` from S3 using `request_uuid`
4. `datmail` rebuilds and forwards the message using its existing logic, but only to the requested target
5. Django records a new `ForwardedMail` row with `previous_attempt` pointing to the retried attempt

Important:

- resend does not create a new `IncomingMail`
- the old `ForwardedMail` row remains unchanged
- the new row represents the retry attempt

## Implementation notes

### Django

- add the new models and migrations in `mail`
- add admin registrations, inlines, list annotations, and resend action UI
- add a service for generating presigned S3 URLs
- add authenticated ingest endpoints for `datmail`

### datmail

- after archive + recipient resolution, post the initial event to Django
- when relay handoff fails for a known recipient, patch the matching `ForwardedMail`
- add an authenticated resend entry point that performs a single-target resend using existing forwarding logic

## Error handling

- Failed Django ingest calls from `datmail` should be logged clearly and retried intentionally, not silently ignored
- Resend failures should create a new `ForwardedMail` attempt only when a resend was actually attempted
- Presigned URL generation failures should surface as explicit admin errors
- Unknown or late SNS events should be logged and rejected rather than attached to the wrong row

## Testing strategy

### Django tests

- model constraints and relationships
- idempotent incoming-mail upsert behavior
- initial `ForwardedMail` bulk creation from expanded recipients
- no `ForwardedMail` creation for dropped mail
- admin changelist stats based on latest attempt per recipient chain
- admin default filtering to processed mail with optional dropped-mail visibility
- presigned download action behavior
- resend action triggering the outbound request to `datmail`

### datmail tests

- event payload generation after archiving and recipient expansion
- failure patch reporting
- single-target resend behavior reusing existing forwarding/header logic

## Open decisions resolved during brainstorming

- Django is the source of truth for monitoring data
- An `IncomingMail` row exists for both processed and dropped mail
- Dropped mail creates no `ForwardedMail` rows and must carry a visible drop reason
- `IncomingMail` stores both the raw original target string and a nullable `MailingList` relation
- `datmail` reports mail to Django after the processing outcome is known, so Django only creates initial `ForwardedMail` rows for processed mail
- `ForwardedMail` uses `FORWARDED`, `FAILED`, and `BOUNCED`
- Resends create new `ForwardedMail` rows linked by `previous_attempt`
- Resends are triggered from Django admin but executed by `datmail`
