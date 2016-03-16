from __future__ import unicode_literals
from .settings import money_rates_settings
from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


class CacheRateSourceManager(models.Manager):

    def _get_cache_key(self, source_name):
        return "dj_money_rate__ratesource__{}".format(source_name)

    def get_source_base_currency(self, source_name):
        cache_key = self._get_cache_key(source_name)
        base_currency = cache.get(cache_key)
        if base_currency is None:
            base_currency = RateSource.objects.get(
                name=source_name).base_currency
            cache.set(cache_key, base_currency)  # cache for 'ever'
        return base_currency

    def set_base_currency(self, source_rate):
        cache_key = self._get_cache_key(source_rate.name)
        cache.set(cache_key, source_rate.base_currency)  # cache for 'ever'

    def clear_base_currency(self, source_rate):
        cache_key = self._get_cache_key(source_rate.name)
        cache.delete(cache_key)


@python_2_unicode_compatible
class RateSource(models.Model):
    name = models.CharField(max_length=100, unique=True)
    last_update = models.DateTimeField(auto_now=True)
    base_currency = models.CharField(max_length=3)
    objects = CacheRateSourceManager()

    def __str__(self):
        return _("%s rates in %s update %s") % (
            self.name, self.base_currency, self.last_update)


@receiver(post_save, sender=RateSource)
def update_rate_source_cache(sender, instance, created, **kwargs):
    RateSource.objects.set_base_currency(instance)


@receiver(post_delete, sender=RateSource)
def delete_rate_source_cache(sender, instance, created, **kwargs):
    RateSource.objects.clear_base_currency(instance)


class CacheRateManager(models.Manager):

    def _get_cache_key(self, source_name, currency, date):
        return "dj_money_rate__rate__{}__{}_{}".format(source_name, currency, date)

    def get_rate_value(self, source_name, currency, date=None):
        if date is None:
            date = timezone.now().date()
        cache_key = self._get_cache_key(source_name, currency, date)
        rate_value = cache.get(cache_key)
        if rate_value is None:
            rate_value = Rate.objects.get(
                source__name=source_name,
                currency=currency).value
            cache.set(cache_key, rate_value, money_rates_settings.RATE_CACHE_TIME)
        return rate_value

    def set_rate_value(self, rate):
        cache_key = self._get_cache_key(rate.source.name, rate.currency, rate.date)
        cache.set(cache_key, rate.value, money_rates_settings.RATE_CACHE_TIME)

    def clear_rate_value(self, rate):
        cache_key = self._get_cache_key(rate.source.name, rate.currency, rate.date)
        cache.delete(cache_key)


def _get_default_date():
    return timezone.now().date()


@python_2_unicode_compatible
class Rate(models.Model):
    source = models.ForeignKey(RateSource)
    currency = models.CharField(max_length=3, db_index=True)
    value = models.DecimalField(max_digits=20, decimal_places=6)
    date = models.DateField(default=_get_default_date, null=True, blank=True, db_index=True)
    objects = CacheRateManager()

    class Meta:
        unique_together = ('source', 'currency', 'date')
        ordering = ('-date', 'currency')

    def __str__(self):
        return _("%s at %.6f") % (self.currency, self.value)


@receiver(post_delete, sender=Rate)
@receiver(post_save, sender=Rate)
def clear_rate_cache(sender, instance, **kwargs):
    if 'created' not in kwargs or not kwargs['created']:  # clear cache only on delete or update of rate
        Rate.objects.clear_rate_value(instance)
