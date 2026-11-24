# Workspace source setup

Choose sources explicitly. A Google Cloud runtime identity does not grant access to user
content. Reuse the authorized user's OAuth client and token when the required scopes exist;
additional scopes require actual user consent, not just an API enablement change.

For a local single-owner pilot, use a Desktop OAuth client with a loopback callback. A hosted
connector uses a Web client and registered HTTPS callback. Verify the consenting email and
granted scopes before saving refresh credentials privately. Domain-wide delegation is a
separate administrator-authorized design. Folder/date filters constrain ingestion, not token scope.

| Source | Useful content | Setup and ingestion checks |
| --- | --- | --- |
| Drive | Docs, supported files, project specifications, presentations | Enable Drive API; choose appropriate file-read scopes. Read/export content, preserve file ID, version, modified time and source URL. Check shared-drive support for the selected scope. Unsupported formats must be reported. |
| Gmail | Messages and threads | Enable Gmail API and authorize read access. Select labels/queries/date windows, read bodies, retain message/thread IDs and timestamps. Attachments need explicit handling. |
| Meet | Generated transcripts and meeting artifacts | Enable Meet API and authorize access to meeting spaces. Read actual transcript entries; retain resource IDs and timestamps. Do not assume every meeting has a transcript. Drive copies remain separately permissioned. |
| Calendar | Events, agendas, organizers, attendees, linked meeting/docs | Enable Calendar API. Use `calendar.readonly` (the scope Antfly's hosted Workspace design requests for event content and calendar selection); narrower scopes such as `calendar.events.readonly` suffice only for known calendar IDs without discovery. Read event content, not just free/busy. Preserve calendar ID + event ID, event status, time zone, start/end, recurrence identity, updated time and original URL. |

For Calendar, distinguish an invitation from attendance and an agenda from what was actually
said. Preserve cancellations, recurring-instance exceptions and all-day dates. A calendar link
to a document does not grant access to that document. Recheck each referenced source separately.
[Calendar scopes](https://developers.google.com/workspace/calendar/api/auth).

A connector must handle pagination and bounded initial scope. For ongoing ingestion, persist
Gmail history cursors, Drive change cursors and Calendar sync tokens, and reconcile deletions
and permission loss. Calendar invalid sync tokens return 410 and require a scoped full
resynchronization; retain request compatibility across incremental pages.
[Calendar synchronization](https://developers.google.com/workspace/calendar/api/guides/sync).

Meet API transcript entries have a limited availability window; accessible Drive transcript
documents can remain longer. Verify current retention and artifact availability before promising
historical coverage. [Meet artifacts](https://developers.google.com/workspace/meet/api/guides/artifacts).

## Hosted Workspace connection (Antfly Cloud, pre-release)

Antfly's design adds one Google Workspace connection in Antfly Cloud covering Drive, Gmail and
Calendar (read-only scopes `drive.readonly`, `gmail.readonly`, `calendar.readonly`), created
with `antfly-cloud connections connect google-workspace --services drive,gmail,calendar` and
then `antfly-cloud sources add --connection ID --resource gmail|calendar|drive --select ...`.
Gmail history IDs and per-calendar sync tokens drive incremental sync; expired cursors need a
full rebuild. Meet is not part of it. Status: local contract tests pass, but live hosted
qualification is blocked (the routes returned 400/404 on the deployed API), so treat it as
not generally available and verify on the target instance before relying on it.

The earlier separate Antfly pilot read selected Gmail, Drive and Meet content. Its token does
not establish Calendar consent; do not claim Calendar ingestion without actual reads.
