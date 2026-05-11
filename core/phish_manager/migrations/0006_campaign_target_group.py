from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phish_manager', '0005_emailtemplate_landing_page'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='targets',
            field=models.ManyToManyField(blank=True, to='phish_manager.target'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='target_group',
            field=models.CharField(
                blank=True,
                max_length=100,
                help_text="Grup adı girilirse (örn: 'öğrenci', 'akademisyen') o gruptaki tüm hedeflere gönderilir. Boş bırakılırsa yukarıdaki 'targets' listesi kullanılır."
            ),
        ),
    ]
