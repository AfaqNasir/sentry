# Generated by Django 2.2.28 on 2023-03-14 23:45

from django.db import connection, migrations
from psycopg2.extras import execute_values

from sentry.new_migrations.migrations import CheckedMigration
from sentry.utils.query import RangeQuerySetWrapperWithProgressBar

BATCH_SIZE = 100

UPDATE_QUERY = """
    UPDATE sentry_monitorcheckin
    SET monitor_environment_id = data.monitor_environment_id
    FROM (VALUES %s) AS data (id, monitor_environment_id)
    WHERE sentry_monitorcheckin.id = data.id"""


def backfill_monitor_checkins(apps, schema_editor):
    MonitorCheckIn = apps.get_model("sentry", "MonitorCheckIn")
    MonitorEnvironment = apps.get_model("sentry", "MonitorEnvironment")

    monitor_mappings = {
        monitor_id: monitor_env_id
        for monitor_id, monitor_env_id in MonitorEnvironment.objects.filter(
            environment__name="production"
        )
        .order_by("date_added")
        .values_list("monitor_id", "id")
    }

    queryset = RangeQuerySetWrapperWithProgressBar(
        MonitorCheckIn.objects.all().values_list(
            "id",
            "monitor_id",
            "monitor_environment_id",
        ),
        result_value_getter=lambda item: item[0],
    )

    cursor = connection.cursor()
    batch = []
    for monitor_checkin_id, monitor_id, monitor_environment_id in queryset:
        if monitor_environment_id:
            continue

        monitor_environment_id = monitor_mappings[monitor_id]

        batch.append((monitor_checkin_id, monitor_environment_id))
        if len(batch) >= BATCH_SIZE:
            execute_values(cursor, UPDATE_QUERY, batch, page_size=BATCH_SIZE)
            batch = []

    if batch:
        execute_values(cursor, UPDATE_QUERY, batch, page_size=BATCH_SIZE)


class Migration(CheckedMigration):
    # This flag is used to mark that a migration shouldn't be automatically run in production. For
    # the most part, this should only be used for operations where it's safe to run the migration
    # after your code has deployed. So this should not be used for most operations that alter the
    # schema of a table.
    # Here are some things that make sense to mark as dangerous:
    # - Large data migrations. Typically we want these to be run manually by ops so that they can
    #   be monitored and not block the deploy for a long period of time while they run.
    # - Adding indexes to large tables. Since this can take a long time, we'd generally prefer to
    #   have ops run this and not block the deploy. Note that while adding an index is a schema
    #   change, it's completely safe to run the operation after the code has deployed.
    is_dangerous = True

    dependencies = [
        ("sentry", "0385_service_hook_hc_fk"),
    ]

    operations = [
        migrations.RunPython(
            backfill_monitor_checkins,
            migrations.RunPython.noop,
            hints={
                "tables": [
                    "sentry_monitor",
                    "sentry_monitorcheckin",
                    "sentry_monitorenvironment",
                ]
            },
        ),
    ]