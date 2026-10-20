"""
SafeHome AI - Controlled Demo Data Cleanup Script
Safely removes verified demo/seeded records while strictly preserving
genuine user uploads, real analysis results, and configuration.
Idempotent and safe to run multiple times.
"""

import os
import sys
import shutil
import sqlite3

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "safehome.db"))

def cleanup_database():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    print("=" * 60)
    print("SAFEHOME AI - CONTROLLED DATABASE CLEANUP")
    print(f"Target Database: {DB_PATH}")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Inspect existing records
    print("\n--- Current Record Counts Before Cleanup ---")
    tables = ["videos", "analysis_jobs", "events", "ai_summaries", "ring_devices", "notifications", "review_records", "privacy_settings"]
    counts_before = {}
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            cnt = cursor.fetchone()[0]
            counts_before[table] = cnt
            print(f"  {table:18}: {cnt}")
        except sqlite3.OperationalError:
            counts_before[table] = 0

    # 2. Identify confirmed demo records to delete
    # Demo videos: is_demo = 1
    cursor.execute("SELECT id, filename, file_path FROM videos WHERE is_demo = 1")
    demo_videos = cursor.fetchall()

    # Demo events: is_demo = 1 OR source = 'simulator' OR source_type = 'test_fixture'
    cursor.execute("SELECT id FROM events WHERE is_demo = 1 OR source = 'simulator' OR source_type = 'test_fixture'")
    demo_events = cursor.fetchall()
    demo_event_ids = [e[0] for e in demo_events]

    # Simulator devices: is_simulator = 1
    cursor.execute("SELECT id FROM ring_devices WHERE is_simulator = 1")
    demo_devices = cursor.fetchall()

    # Demo summaries: is_demo = 1
    cursor.execute("SELECT id FROM ai_summaries WHERE is_demo = 1")
    demo_summaries = cursor.fetchall()

    # Fake/simulator notifications
    cursor.execute("""
        SELECT id FROM notifications 
        WHERE event_id IN (SELECT id FROM events WHERE is_demo = 1 OR source = 'simulator' OR source_type = 'test_fixture')
           OR title LIKE '%Simulator%'
           OR message LIKE '%Simulator%'
           OR notification_type = 'test_fixture'
    """)
    demo_notifications = cursor.fetchall()
    demo_notification_ids = [n[0] for n in demo_notifications]

    print("\n--- Identified Confirmed Demo / Seed Records ---")
    print(f"  Demo Videos        : {len(demo_videos)}")
    print(f"  Demo Events        : {len(demo_events)}")
    print(f"  Simulator Devices  : {len(demo_devices)}")
    print(f"  Demo AI Summaries  : {len(demo_summaries)}")
    print(f"  Demo Notifications : {len(demo_notifications)}")

    # 3. Perform atomic cleanup
    deleted_counts = {}
    try:
        # Reviews attached to demo events
        if demo_event_ids:
            placeholders = ",".join("?" * len(demo_event_ids))
            cursor.execute(f"DELETE FROM review_records WHERE event_id IN ({placeholders})", demo_event_ids)
            deleted_counts["review_records"] = cursor.rowcount
        else:
            deleted_counts["review_records"] = 0

        # Notifications
        if demo_notification_ids:
            placeholders = ",".join("?" * len(demo_notification_ids))
            cursor.execute(f"DELETE FROM notifications WHERE id IN ({placeholders})", demo_notification_ids)
            deleted_counts["notifications"] = cursor.rowcount
        else:
            deleted_counts["notifications"] = 0

        # AI Summaries (demo)
        cursor.execute("DELETE FROM ai_summaries WHERE is_demo = 1")
        deleted_counts["ai_summaries"] = cursor.rowcount

        # Events (demo/simulator)
        cursor.execute("DELETE FROM events WHERE is_demo = 1 OR source = 'simulator' OR source_type = 'test_fixture'")
        deleted_counts["events"] = cursor.rowcount

        # Ring Devices (simulator)
        cursor.execute("DELETE FROM ring_devices WHERE is_simulator = 1")
        deleted_counts["ring_devices"] = cursor.rowcount

        # Analysis jobs for demo videos
        if demo_videos:
            demo_video_ids = [v[0] for v in demo_videos]
            placeholders = ",".join("?" * len(demo_video_ids))
            cursor.execute(f"DELETE FROM analysis_jobs WHERE video_id IN ({placeholders})", demo_video_ids)
            deleted_counts["analysis_jobs"] = cursor.rowcount
            
            cursor.execute("DELETE FROM videos WHERE is_demo = 1")
            deleted_counts["videos"] = cursor.rowcount
        else:
            deleted_counts["analysis_jobs"] = 0
            deleted_counts["videos"] = 0

        # Keep privacy settings intact!
        deleted_counts["privacy_settings"] = 0

        conn.commit()
        print("\n[SUCCESS] Transaction committed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Cleanup failed, rolled back: {e}")
        conn.close()
        return

    # 4. Report results
    print("\n--- Summary of Deleted Records by Table ---")
    for tbl, cnt in deleted_counts.items():
        print(f"  {tbl:18}: {cnt} deleted")

    print("\n--- Remaining Records After Cleanup ---")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            cnt = cursor.fetchone()[0]
            print(f"  {table:18}: {cnt}")
        except sqlite3.OperationalError:
            pass

    conn.close()
    print("\nCleanup completed safely. Real user videos, legitimate settings, and real data preserved.")

if __name__ == "__main__":
    cleanup_database()
