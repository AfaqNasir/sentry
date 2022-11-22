# Generated by Django 2.2.28 on 2022-11-08 05:02

import django.utils.timezone
from django.db import migrations, models

import sentry.db.models.fields.bounded
from sentry.new_migrations.migrations import CheckedMigration


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
    is_dangerous = False

    dependencies = [
        ("sentry", "0341_reconstrain_savedsearch_pinning_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrganizationMapping",
            fields=[
                (
                    "id",
                    sentry.db.models.fields.bounded.BoundedBigAutoField(
                        primary_key=True, serialize=False
                    ),
                ),
                (
                    "organization_id",
                    sentry.db.models.fields.bounded.BoundedBigIntegerField(db_index=True),
                ),
                ("slug", models.SlugField(unique=True)),
                ("name", models.CharField(max_length=64)),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
                ("stripe_id", models.CharField(max_length=255, db_index=True, null=True)),
                ("verified", models.BooleanField(default=False)),
                ("idempotency_key", models.CharField(max_length=48)),
                ("region_name", models.CharField(max_length=48, null=True)),
            ],
            options={
                "db_table": "sentry_organizationmapping",
            },
        ),
    ]
