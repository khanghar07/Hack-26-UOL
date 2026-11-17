# Final acceptance record · 17 November 2026

| Challenge item | Verification |
|---|---|
| Ten accounts and repeatable seeding | Two seeds, ten successful emulator logins, wrong password and unseeded identity denials passed. |
| Server-side roles | Checked all ten identities, role-filtered lists, task counts and direct project access. All nine non-admin import attempts denied. Disabled and revoked sessions denied. |
| Required fields and final decisions | Earlier live OpenRouter acceptance run matched the three clients, managers and final deadlines and all twelve task owners, deadlines and estimates. Original totals 40, 46 and 38 hours. Modified run changed QuickServe to 48 hours and Usman's deadline to 23 October. |
| Import integrity | Repeated/concurrent imports, source-supported estimates, invalid dates/owners, empty input, provider failure and mid-transaction rollback passed. No partial records on failure. |
| Desktop and mobile | Final browser run exercises Firebase emulator login, read-only directory, admin import, project detail, refresh, manager filtering, logout and a 390px developer view against local PostgreSQL. |
| AI availability | Final live generation attempt was network-blocked. For the final browser regression only, the test harness supplied a deterministic provider response. The normal application calls the configured provider and raises an error if unavailable. No fixture fallback exists in production. |
| Hosted services | Aiven address supplied; DNS lookup failed in this workspace before TLS/authentication. configure_aiven.py tests the private URI on your computer. The admin previously signed into hosted Firebase. Hosted backend seeding still requires a private Firebase Admin credential. No Vercel deployment. |

The video is a recording of the final browser regression with a fixture provider response, real emulator login and real PostgreSQL persistence. Provide a fresh live-provider recording for judging if an end-to-end live AI demonstration is required. The PDF's hosted-deployment bonus remains outstanding.
