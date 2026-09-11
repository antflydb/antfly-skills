# Optional private Cloud Run deployment

Use the user's selected service, project and region. A deployment needs application code,
a locked dependency set, a server entrypoint and container/build configuration. This procedure
does not assume that the Guide itself is a deployable application.

## Prepare the deployable app

Keep only code, dependencies and UI assets in the image. Inspect the source upload manifest
and Docker context; exclude `.env` files, OAuth credentials, private source bodies, reports
and local environments. Never put an ingestion/admin key into the runtime image.

Use a dedicated runtime service account with the required Vertex AI role and Secret Manager
access only to the needed secrets. Use an authorized build identity separately. Mount or
inject pinned versions of runtime secrets; use the attached identity for Google APIs rather
than generating a service-account key. Set a bounded timeout, concurrency and instance limit.

## Private browser access

For an internal Google-authenticated UI, enable Cloud Run IAP and disallow unauthenticated
access. Grant the IAP service agent Cloud Run invocation and grant only intended viewers the
IAP access role. Verify current [Cloud Run IAP configuration](https://docs.cloud.google.com/run/docs/securing/identity-aware-proxy-cloud-run).

The app should validate the signed IAP assertion's signature, issuer, expected audience and
allowed principal. For Cloud Run, the expected assertion audience is
`/projects/{project_number}/locations/{region}/services/{service_name}`. Do not trust an
unsigned email header. A local loopback bypass must not activate in the deployed runtime.
[Signed assertions](https://docs.cloud.google.com/iap/docs/signed-headers-howto).

IAP authenticates app access; the retrieval adapter still enforces source access. A shared
corporate domain does not authorize every user's mailbox. Avoid caching private responses
publicly and keep mutation/action endpoints separate from read-only retrieval.

## Deployment checks

Verify service health and readiness, anonymous denial or login redirect, authenticated page
loads, a complete agent turn, source links, and the deployed revision/identity/IAM policies.
Repeat through the deployed service even when local execution passed. Review UI behavior
when a UI is in scope, including errors, citations and smaller screens.

For programmatic IAP tests, use a supported identity flow and an explicitly allowed OAuth
client where required. A generic gcloud user ID token may have the wrong audience. The prior
private build used an existing Desktop OAuth client allowed for the specific IAP service,
with owner access still checked independently. Allow settings propagation before concluding
the token flow failed. Never log tokens or reuse a source token without its existing authorization.
[Programmatic IAP access](https://docs.cloud.google.com/iap/docs/authentication-howto).

Report automated API verification separately from a tested human browser sign-in flow.
Keep generated answers, logs and screenshots private when the dataset is private.
