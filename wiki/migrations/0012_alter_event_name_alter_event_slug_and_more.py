# Generated by Django 4.1.5 on 2023-03-10 12:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0011_alter_event_partners"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="name",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AlterField(
            model_name="event",
            name="slug",
            field=models.SlugField(default="event_name", max_length=150),
        ),
        migrations.AlterField(
            model_name="event",
            name="website",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name="rider",
            name="instagram",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name="rider",
            name="name",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AlterField(
            model_name="rider",
            name="photo",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name="rider",
            name="sex",
            field=models.CharField(blank=True, default="Unknown", max_length=20),
        ),
        migrations.AlterField(
            model_name="rider",
            name="slug",
            field=models.SlugField(default="event_name", max_length=150),
        ),
        migrations.AlterField(
            model_name="sponsor",
            name="name",
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
