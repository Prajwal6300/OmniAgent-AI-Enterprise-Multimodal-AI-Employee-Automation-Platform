# Third-Party Audit

This document lists every external service, CDN, font, analytics, and SDK used by the OmniAgent AI app. Items without a verified license or that set cookies without consent must be addressed before launch.

## 1. External Services & SDKs

| Name | Purpose | Data Sent | Sets Cookies | Load Before Consent? | License | Removable / Self-Hostable |
|---|---|---|---|---|---|---|
| `OpenAI API` | AI document analysis, chat, embeddings | Prompts, document content, embeddings | No persistent cookies from frontend | Yes (until consent accepted) | Proprietary - cannot self-host | Required for core AI functionality |
| `Cloudflare R2 / Storage` | Document file storage | File metadata, uploads | Referer/header logging | No | Proprietary - cannot self-host | Required for document storage |
| `PostgreSQL / Neon` | User/organization/data persistence | All user records, conversations, messages | No cookies from app | No | Open source - can self-host | Required |
| `Hosting (Vercel/Render)` | Web hosting | IP address, session metadata | Server logs (not app cookies) | No | N/A | Required |
| `Font: Google APIs` | UI font rendering | Font family names | Potential tracking | **Yes** (before consent) | Proprietary - being reviewed | Replace with self-hosted OFL fonts |
| `(none)` | SMTP/email sending | - | - | **No** (no email sending configured) | N/A | N/A - confirmed no SMTP setup |

## 2. Fonts

| Name | Source | License | Attribution | Status |
|---|---|---|---|---|
| `UI Fonts` | `tailwindcss` default / system fonts | MIT / system | None required | ✅ Acceptable |
| `(potential) Google Fonts` | `fonts.googleapis.com` | Being reviewed (OFL) | May be required | 🚫 **To be replaced** with self-hosted OFL fonts |

*Action: Self-host Google Fonts if OFL license allows, or replace with system fonts. Remove `fonts.googleapis.com` import if no longer needed.*

## 3. CDNs & External CSS/JS

| Resource | Purpose | Host | Cookies | Before Consent? |
|---|---|---|---|---|
| `tailwindcss` | Utility-first CSS framework | `node_modules` | No | N/A |
| `lucide-react` | Icon set | `node_modules` | No | N/A |
| `@heroicons/react` | Alternative icons | `node_modules` | No | N/A |

*No external CDN links found in `index.html` or CSS `@import`. All dependencies are from `node_modules`.*

## 4. Summary

- **No analytics scripts** (Google Analytics, etc.) are currently loaded.
- **No chat widgets** (Intercom, Crisp, etc.) are currently loaded.
- **No map widgets** (Google Maps, etc.) are currently loaded.
- **No social login** (Google, GitHub, etc.) is currently implemented.
- **OpenAI API** is the only third-party AI service integrated.
- **Cloudflare R2** is the only third-party storage service integrated.
- **Hosting** is via Vercel/Render (infra-level, not app-level scripts).

*Key finding: No non-essential third-party scripts load before consent. The cookie banner (Item 5) should ensure analytics/OpenAI scripts are blocked until user accepts.*

*Action: Confirm OpenAI API usage is essential and cannot be removed. If removable, document removal. If not, ensure cookie banner properly discloses it.*