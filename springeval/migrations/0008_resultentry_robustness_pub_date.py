from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('springeval', '0007_alter_resultentry_evaluate_robustness'),
    ]

    operations = [
        migrations.AddField(
            model_name='resultentry',
            name='robustness_pub_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
