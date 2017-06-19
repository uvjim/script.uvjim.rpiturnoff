import xbmc, xbmcgui, xbmcaddon
import logger
import json
import time

class AlarmStore:
    Location = xbmcgui.Window(10000)
    PropertyName = 'uvjim.timers'

    ######################################################################
    #    Aim:        To format the timer details ready for storing
    #    Params:     details - the details that need formatting
    #    Returns:    The formatted JSON string
    ######################################################################
    @staticmethod
    def _format(details):
        return json.dumps([details], separators=(',', ':'))

    ######################################################################
    #    Aim:        To store the timer details
    #    Params:     details - the details to store
    #                update - if True will attempt to update details of
    #                an existing timer
    #    Returns:    N/A
    ######################################################################
    @staticmethod
    def set(details, update=False):
        tostore = None
        name = details['name']
        timer = AlarmStore.get(name)
        if not update:
            if timer: return (-1, 'Timer already exists')
        else:
            if not timer: return (-2, 'Timer does not exist')
            AlarmStore.unset(name)
        tostore = AlarmStore._format(details)
        msg = 'Storing {}'.format(tostore) if not update else 'Updating {} to {}'.format(name, tostore)
        logger.write('AlarmStore.set: {}'.format(msg))
        if tostore:
            AlarmStore.Location.setProperty(AlarmStore.PropertyName, tostore)

    ######################################################################
    #    Aim:        To retrieve the details of the specified timer
    #    Params:     name - the name of the timer to retrieve details for
    #                log - False if you don't want the logging to happen
    #    Returns:    Details of the timer
    ######################################################################
    @staticmethod
    def get(name, log=True):
        ret = False
        if log: logger.write('AlarmStore.get: Retrieving details for {}'.format(name))
        timers = AlarmStore.Location.getProperty(AlarmStore.PropertyName)
        if timers:
            timers = json.loads(timers)
            timer = [t for t in timers if t['name'] == name]
            ret = timer[0] if len(timer) else False
            if log: logger.write('AlarmStore.get: {}: {}'.format(name, ret))
        return ret

    ######################################################################
    #    Aim:        To remove details of the specified timer
    #    Params:     name - the name of the timer to remove
    #    Returns:    N/A
    ######################################################################
    @staticmethod
    def unset(name):
        timers = AlarmStore.Location.getProperty(AlarmStore.PropertyName)
        timers = json.loads(timers)
        timers = [t for t in timers if t['name'] != name]
        if len(timers):
            tostore = AlarmStore._format(details)
        else:
            AlarmStore.Location.clearProperty(AlarmStore.PropertyName)

class Alarm(object):
    ReminderSuffix = '.reminder'

    ######################################################################
    #    Aim:        To intialise the basic details of the timer
    #    Params:     name - the name of the timer
    #                friendly - text used to display anything about the
    #                           timer
    #    Returns:    N/A
    ######################################################################
    def __init__(self, name, friendly):
        self.name = name
        self.friendly = friendly
        self.settings = xbmcaddon.Addon().getSetting
        self.language = xbmcaddon.Addon().getLocalizedString


    def _secondsToHHMMSS(self, seconds):
        hours = seconds // (60*60)
        seconds %= (60*60)
        minutes = seconds // 60
        seconds %= 60
        return '%02i:%02i:%02i' % (hours, minutes, seconds)

    ######################################################################
    #    Aim:        To carry out the actions configured for when the
    #                timer expires
    #    Returns:    N/A
    ######################################################################
    def _doAction(self):
        if self.settings('actions.waitforscreensaver') == 'false':
            logger.write('Alarm._doAction: Executing CECStandby builtin')
            xbmc.executebuiltin('XBMC.CECStandby')
        if self.settings('actions.stopmedia') == 'true':
            logger.write('Alarm._doAction: Stopping the current player')
            xbmc.executebuiltin('XBMC.PlayerControl(Stop)')
        if self.settings('actions.returnto') != '':
            logger.write('Alarm._doAction: Returning to the {}'.format(self.settings('actions.returnto')))
            xbmc.executebuiltin('XBMC.ActivateWindow({})'.format(self.settings('actions.returnto')))
        AlarmStore.unset(self.name)

    ######################################################################
    #    Aim:        To create or extend the timer
    #    Params:     timeout - the duration of the timer in seconds
    #                extend - True if extending the timer
    #    Returns:    True/False
    ######################################################################
    def set(self, timeout=0, extend=False):
        ret = None
        if timeout:
            remindername = '{}{}'.format(self.name, Alarm.ReminderSuffix)
            logger.write('Alarm.set: Setting {} for {} minutes - extend: {}'.format(self.name, timeout, extend))
            xbmc.executebuiltin('XBMC.AlarmClock({0}, XBMC.RunScript("{1}", "action=expired&name={0}"), "{2}", silent)'.format(self.name, xbmcaddon.Addon().getAddonInfo('id'), self._secondsToHHMMSS(timeout)))
            if self.settings('notifications.start') == 'true' and not extend:
                xbmcgui.Dialog().notification(self.friendly, '{} {} {}'.format(self.language(32075), divmod(timeout, 60)[0], self.language(32073)))
            aDetails = {'name': self.name, 'reminder': remindername, 'friendly': self.friendly, 'start': int(time.time()), 'timeout': timeout}
            ret = AlarmStore.set(aDetails)
            ret = True if not ret else ret[1]
            if ret:
                logger.write('Alarm.set: {} created: {}'.format(self.name, ret))
                if self.settings('notifications.duration') == 'true':
                    if self.settings('notifications.duration.unit') == self.language(30040) or self.settings('notifications.duration.unit') == '':
                        rTimeout = timeout - (int(self.settings('notifications.duration.value')) * 60)
                    elif self.settings('notifications.duration.unit') == self.language(30041):
                        rTimeout = timeout - ((timeout * int(self.settings('notifications.duration.value'))) / 100)
                    xbmc.executebuiltin('XBMC.AlarmClock({}, "Notification({}, {})", "{}", silent)'.format(remindername, self.friendly, self.language(32071).format('{} {}'.format(divmod(timeout - rTimeout, 60)[0], self.language(32073))), self._secondsToHHMMSS(rTimeout)))
        else:
            ret = False
        return ret

    ######################################################################
    #    Aim:        To stop the timer from running
    #    Params:     notify - stop notifications showing
    #    Returns:    N/A
    ######################################################################
    def cancel(self, notify=True):
        logger.write('Alarm.cancel: Cancelling {}'.format(self.name))
        timer = AlarmStore.get(self.name)
        xbmc.executebuiltin('XBMC.CancelAlarm({}, silent)'.format(self.name))
        xbmc.executebuiltin('XBMC.CancelAlarm({}, silent)'.format(timer['reminder']))
        if notify:
            if timer and self.settings('notifications.cancel') == 'true': xbmcgui.Dialog().notification(timer['friendly'], '{} {}'.format(timer['friendly'], self.language(32076)))
        AlarmStore.unset(self.name)

    ######################################################################
    #    Aim:        To extend the timer by the given amount
    #    Params:     extendby - the number of seconds to extend the timer
    #    Returns:    N/A
    ######################################################################
    def extend(self, extendby):
        if extendby:
            logger.write('Alarm.extend: Extending {}'.format(self.friendly))
            timeLeft = self.getTimeLeft()
            if timeLeft:
                self.cancel(notify=False)
                if self.set(timeout=timeLeft + extendby, extend=True):
                    if self.settings('notifications.extend') == 'true':
                        xbmcgui.Dialog().notification(self.friendly, '{} {} {}'.format(self.language(32079), divmod(extendby, 60)[0], self.language(32073)))
                    logger.write('Alarm.extend: Extended {} by {}'.format(self.friendly, extendby))

    ######################################################################
    #    Aim:        To determine if the timer is already set
    #    Params:     log - False if you don't want the logging to happen
    #    Returns:    True/False
    ######################################################################
    def isSet(self, log=True):
        if log: logger.write('Alarm.isSet: Checking for {}'.format(self.name))
        timer = AlarmStore.get(self.name)
        ret = True if timer else False
        if log: logger.write('Alarm.isSet: {} exists: {}'.format(self.name, ret))
        return ret

    ######################################################################
    #    Aim:        To retrieve how long the timer has left to run
    #    Returns:    The number of seconds that the timer has left
    ######################################################################
    def getTimeLeft(self):
        ret = None
        logger.write('Alarm.getTimeLeft: Checking time left on {}'.format(self.name))
        if self.isSet(log=False):
            timer = AlarmStore.get(self.name)
            if timer:
                ret = (timer['start'] + timer['timeout']) - int(time.time())
                logger.write('Alarm.getTimeLeft: {} has {} seconds left'.format(self.name, ret))
        return ret

    ######################################################################
    #    Aim:        To carry out the actions when the timer has expired
    #    Returns:    N/A
    ######################################################################
    def expired(self):
        logger.write('Alarm.expired: {} has expired'.format(self.name))
        self._doAction()
