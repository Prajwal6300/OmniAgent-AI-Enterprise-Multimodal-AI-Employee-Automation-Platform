# Backup & Restore Guide

## Neon (PostgreSQL) - Point-in-Time Restore

1. **Create a restore point (branch):**
   - Open the [Neon Console](https://console.neon.tech)
   - Select your project and database
   - Navigate to **Branches** → **Create branch**
   - Name the branch (e.g., `prelaunch-backup` or `restore-2026-10-15`)
   - Use the time slider to select the desired point in time, or enter a specific timestamp
   - Click **Create branch**

2. **Restore from the backup branch:**
   - In the Neon Console, go to **Branches**
   - Find the backup branch you created
   - Click **Promote** to make the branch the new main database, OR
   - Connect to the branch directly using the connection pooler endpoint to recover specific tables or data

3. **Important notes:**
   - Branches are independent copies; no impact on the production database
   - Branches expire after 48 hours by default (configurable)
   - Always test the restore on a non-production branch first

## Cloudflare R2 - Object Versioning

1. **Enable object versioning:**
   - Open the [Cloudflare Dashboard](https://dash.cloudflare.com)
   - Go to **R2** → Select your bucket
   - Click **Settings**
   - Toggle **Object Versioning** to **On**
   - Click **Save**

2. **Restore a previous version:**
   - In the R2 bucket, find the object you want to restore
   - Click the object to view its version history
   - Select the desired previous version
   - Use the "Restore" option or download the specific version

3. **Important notes:**
   - Versioning preserves all versions; deleted objects marked as "delete markers" can be undeleted
   - Storage cost increases with each version stored
   - Versioning applies to all objects in the bucket from the point it is enabled

## General Restore Procedures

### Database Restore (Neon)
- **Emergency procedure:** Promote the backup branch to production
- **Data recovery:** Connect to the backup branch and export specific tables using `pg_dump`
- **Rollback:** Promote the original branch back if the restore introduces issues

### Storage Restore (R2)
- **File recovery:** Restore previous version of a specific object
- **Bulk recovery:** Download multiple versions as needed
- **Deletion recovery:** Undo delete markers to restore deleted objects

### Verification
- Always verify restored data integrity before pointing production traffic to it
- Run full test suites against restored databases
- Validate file checksums for restored storage objects