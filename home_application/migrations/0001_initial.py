# Generated by Django 2.2.6 on 2020-04-22 20:00

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Doinfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('businessname', models.CharField(max_length=50, verbose_name='业务')),
                ('username', models.CharField(max_length=50, verbose_name='用户')),
                ('createtime', models.DateTimeField(verbose_name='创建时间')),
                ('starttime', models.DateTimeField(verbose_name='开始执行时间')),
                ('endtime', models.DateTimeField(blank=True, null=True, verbose_name='执行结束时间')),
                ('iplist', models.CharField(max_length=200, verbose_name='执行列表')),
                ('details', models.CharField(blank=True, max_length=200, null=True, verbose_name='详细')),
                ('jobid', models.IntegerField(verbose_name='jobid')),
                ('status', models.IntegerField(choices=[(1, '未执行'), (2, '正在执行'), (3, '执行成功'), (4, '执行失败')], default=2, verbose_name='执行状态')),
                ('log', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
    ]
