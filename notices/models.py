from django.db import models
from django.utils import timezone


class Notice(models.Model):
    newspaper     = models.CharField(max_length=500, verbose_name='Газета',
                                     blank=True, default='')
    issue_date    = models.DateField(verbose_name='Дата выпуска',
                                     null=True, blank=True)
    approval_date = models.DateField(verbose_name='Дата согласования',
                                     null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Извещение'
        verbose_name_plural = 'Извещения'
        ordering            = ['-created_at']

    def __str__(self):
        return f'Извещение №{self.pk}'

    @property
    def approval_status(self):
        if not self.approval_date:
            return 'no-date'
        today = timezone.now().date()
        delta = (self.approval_date - today).days
        if delta < 0:    return 'overdue'
        if delta <= 3:   return 'critical'
        if delta <= 7:   return 'warning'
        if delta <= 14:  return 'attention'
        return 'ok'


class NoticeItem(models.Model):
    notice           = models.ForeignKey(Notice, on_delete=models.CASCADE,
                                         related_name='items')
    address          = models.TextField(verbose_name='Адрес', blank=True)
    fias_id          = models.CharField(max_length=36,  blank=True)
    region           = models.CharField(max_length=255, blank=True)
    city             = models.CharField(max_length=255, blank=True)
    street           = models.CharField(max_length=255, blank=True)
    house            = models.CharField(max_length=50,  blank=True)
    cadastral_number = models.CharField(max_length=255, blank=True,
                                        verbose_name='Кадастровый номер')
    customer         = models.CharField(max_length=500, blank=True,
                                        verbose_name='Заказчик')
    contract         = models.CharField(max_length=255, blank=True,
                                        verbose_name='Договор')
    order            = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name        = 'Объект извещения'
        verbose_name_plural = 'Объекты извещения'
        ordering            = ['order', 'pk']

    def __str__(self):
        return self.address or f'Объект #{self.pk}'