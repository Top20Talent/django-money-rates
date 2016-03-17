from __future__ import unicode_literals

import json
import logging

from django.core.exceptions import ImproperlyConfigured
from django.utils import six
from django.utils import timezone

from .compat import urlopen
from .compat import urlencode
from .exceptions import RateBackendError
from .models import Rate
from .models import RateSource
from .settings import money_rates_settings


logger = logging.getLogger(__name__)


class BaseRateBackend(object):
    source_name = None
    base_currency = None

    def get_source_name(self):
        """
        Return the name that identifies the ratings source
        """
        if not self.source_name:
            raise RateBackendError("'source_name' can't be empty or"
                                   "you should override 'get_source_name'")

        return self.source_name

    def get_base_currency(self):
        """
        Return the base currency to which the rates are referred
        """
        if not self.base_currency:
            raise RateBackendError("'base_currency' can't be empty or"
                                   "you should override 'get_base_currency'")

        return self.base_currency

    def get_rates(self, date=None):
        """
        Return a dictionary that maps currency code with its rate value
        """
        raise NotImplementedError

    def update_rates(self, date=None):
        """
        Creates or updates rates for a source
        """
        if date is None:
            date = timezone.now().date()

        source, created = RateSource.objects.get_or_create(name=self.get_source_name())
        source.base_currency = self.get_base_currency()
        source.save()

        for currency, value in six.iteritems(self.get_rates(date)):
            try:
                rate = Rate.objects.get(source=source, currency=currency, date=date)
            except Rate.DoesNotExist:
                rate = Rate(source=source, currency=currency, date=date)

            rate.value = value
            rate.save()


class OpenExchangeBackend(BaseRateBackend):
    source_name = "openexchange.org"

    def __init__(self):
        if not money_rates_settings.OPENEXCHANGE_URL:
            raise ImproperlyConfigured(
                "OPENEXCHANGE_URL setting should not be empty when using OpenExchangeBackend")

        if not money_rates_settings.OPENEXCHANGE_APP_ID:
            raise ImproperlyConfigured(
                "OPENEXCHANGE_APP_ID setting should not be empty when using OpenExchangeBackend")

        # Build the base api url
        base_url = "%s?app_id=%s" % (money_rates_settings.OPENEXCHANGE_URL,
                                     money_rates_settings.OPENEXCHANGE_APP_ID)

        # Change the base currency whether it is specified in settings
        base_url += "&base=%s" % self.get_base_currency()

        self.url = base_url

    def get_rates(self, date=None):
        # TODO: date not used
        try:
            logger.debug("Connecting to url %s", self.url)
            data = urlopen(self.url).read().decode("utf-8")
            return json.loads(data)['rates']

        except Exception as e:
            logger.exception("Error retrieving data from %s", self.url)
            raise RateBackendError("Error retrieving rates: %s" % e)

    def get_base_currency(self):
        return money_rates_settings.OPENEXCHANGE_BASE_CURRENCY


class CurrencyLayerBackend(BaseRateBackend):
    source_name = "currencylayer.com"

    def __init__(self):
        if not money_rates_settings.CURRENCYLAYER_URL:
            raise ImproperlyConfigured(
                "CURRENCYLAYER_URL setting should not be empty when using OpenExchangeBackend")

        if not money_rates_settings.CURRENCYLAYER_KEY:
            raise ImproperlyConfigured(
                "CURRENCYLAYER_KEY setting should not be empty when using OpenExchangeBackend")

    def get_rates(self, date=None):
        params = {'access_key': money_rates_settings.CURRENCYLAYER_KEY}
        if date is None or date == timezone.now().date():
            url = money_rates_settings.CURRENCYLAYER_URL + 'live'
        else:
            url = money_rates_settings.CURRENCYLAYER_URL + 'historical'
            params['date'] = str(date)

        url += '?%s' % urlencode(params)
        try:
            logger.debug("Connecting to url %s", url)
            data = urlopen(url).read().decode("utf-8")
            rates = json.loads(data)['quotes']
            return dict((r[0][3:], r[1]) for r in six.iteritems(rates))
        except Exception as e:
            logger.exception("Error retrieving data from %s", url)
            raise RateBackendError("Error retrieving rates: %s" % e)

    def get_base_currency(self):
        return money_rates_settings.CURRENCYLAYER_BASE_CURRENCY
