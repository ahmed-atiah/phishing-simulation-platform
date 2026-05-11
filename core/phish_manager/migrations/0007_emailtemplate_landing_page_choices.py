from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phish_manager', '0006_campaign_target_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailtemplate',
            name='landing_page',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('linkedin',  'LinkedIn'),
                    ('instagram', 'Instagram'),
                    ('microsoft', 'Microsoft 365'),
                    ('google',    'Google Workspace'),
                ],
                default='linkedin',
            ),
        ),
    ]
