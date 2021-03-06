from eventlet import Timeout
from oio.common.utils import float_value, RingBuffer


class BaseChecker(object):
    """Base class for all service checkers"""

    def __init__(self, conf, logger):
        self.logger = logger
        self.timeout = float_value(conf.get('timeout'), 1.0)
        self.rise = conf['rise']
        self.fall = conf['fall']
        self.results = RingBuffer(max([self.rise, self.fall]))
        self.name = conf.get('name')
        self.last_result = None

    def service_status(self):
        """Do the check and set `last_result` accordingly"""
        result = False
        try:
            with Timeout(self.timeout):
                result = self.check()
        except (Exception, Timeout):
            pass

        if self.last_result is None:
            self.last_result = result
            for _i in range(0, self.results.size):
                self.results.append(result)
            self.logger.info('%s first check returned %s', self.name, result)

        self.results.append(result)
        if not any(self.results[-self.fall:]):
            if self.last_result:
                self.logger.info(
                    '%s status is now down after %d failures', self.name,
                    self.fall)
                self.last_result = False
        if all(self.results[-self.rise:]):
            if not self.last_result:
                self.logger.info(
                    '%s status is now up after %d successes', self.name,
                    self.rise)
                self.last_result = True
        return self.last_result

    def check(self):
        """Actually do the service check"""
        return False
