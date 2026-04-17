from django.db import migrations, models

POSTGRES_FUNCTION_NAME = "mail_forwardedmail_previous_attempt_same_incoming_mail"
POSTGRES_TRIGGER_NAME = "mail_forwardedmail_previous_attempt_same_incoming_mail_trigger"
SQLITE_INSERT_TRIGGER_NAME = (
    "mail_forwardedmail_previous_attempt_same_incoming_mail_insert"
)
SQLITE_UPDATE_TRIGGER_NAME = (
    "mail_forwardedmail_previous_attempt_same_incoming_mail_update"
)


def create_previous_attempt_integrity_trigger(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            f"""
            CREATE FUNCTION {POSTGRES_FUNCTION_NAME}()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.previous_attempt_id IS NOT NULL AND EXISTS (
                    SELECT 1
                    FROM mail_forwardedmail
                    WHERE id = NEW.previous_attempt_id
                      AND incoming_mail_id <> NEW.incoming_mail_id
                ) THEN
                    RAISE EXCEPTION
                        'ForwardedMail previous_attempt must belong to the same IncomingMail';
                END IF;

                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        schema_editor.execute(
            f"""
            CREATE TRIGGER {POSTGRES_TRIGGER_NAME}
            BEFORE INSERT OR UPDATE ON mail_forwardedmail
            FOR EACH ROW
            EXECUTE FUNCTION {POSTGRES_FUNCTION_NAME}();
            """
        )
        return

    if schema_editor.connection.vendor == "sqlite":
        schema_editor.execute(
            f"""
            CREATE TRIGGER {SQLITE_INSERT_TRIGGER_NAME}
            BEFORE INSERT ON mail_forwardedmail
            FOR EACH ROW
            WHEN NEW.previous_attempt_id IS NOT NULL
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'ForwardedMail previous_attempt must belong to the same IncomingMail'
                )
                WHERE EXISTS (
                    SELECT 1
                    FROM mail_forwardedmail
                    WHERE id = NEW.previous_attempt_id
                      AND incoming_mail_id <> NEW.incoming_mail_id
                );
            END;
            """
        )
        schema_editor.execute(
            f"""
            CREATE TRIGGER {SQLITE_UPDATE_TRIGGER_NAME}
            BEFORE UPDATE ON mail_forwardedmail
            FOR EACH ROW
            WHEN NEW.previous_attempt_id IS NOT NULL
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'ForwardedMail previous_attempt must belong to the same IncomingMail'
                )
                WHERE EXISTS (
                    SELECT 1
                    FROM mail_forwardedmail
                    WHERE id = NEW.previous_attempt_id
                      AND incoming_mail_id <> NEW.incoming_mail_id
                );
            END;
            """
        )


def drop_previous_attempt_integrity_trigger(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            f"DROP TRIGGER IF EXISTS {POSTGRES_TRIGGER_NAME} ON mail_forwardedmail;"
        )
        schema_editor.execute(f"DROP FUNCTION IF EXISTS {POSTGRES_FUNCTION_NAME}();")
        return

    if schema_editor.connection.vendor == "sqlite":
        schema_editor.execute(f"DROP TRIGGER IF EXISTS {SQLITE_INSERT_TRIGGER_NAME};")
        schema_editor.execute(f"DROP TRIGGER IF EXISTS {SQLITE_UPDATE_TRIGGER_NAME};")


class Migration(migrations.Migration):
    dependencies = [
        ("mail", "0005_mailarchive_incomingmail_forwardedmail"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="forwardedmail",
            constraint=models.CheckConstraint(
                condition=~models.Q(pk=models.F("previous_attempt")),
                name="forwardedmail_previous_attempt_not_self",
            ),
        ),
        migrations.RunPython(
            create_previous_attempt_integrity_trigger,
            drop_previous_attempt_integrity_trigger,
        ),
    ]
