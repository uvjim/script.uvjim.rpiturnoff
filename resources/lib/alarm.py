import xbmc, xbmcgui, xbmcaddon
import logger
import json
import time

class AlarmStore:
    Location = xbmcgui.Window(10000)
    PropertyName = 'uvjim.timers'

    @staticmethod
    def _format(details):
        return json.dumps([details], separators=(',', ':'))

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
        logger.write(msg)
        if tostore:
            AlarmStore.Location.setProperty(AlarmStore.PropertyName, tostore)

    @staticmethod
    def get(name, log=True):
        ret = False
        if log: logger.write('Retrieving details for {}'.format(name))
        timers = AlarmStore.Location.getProperty(AlarmStore.PropertyName)
        if timers:
            timers = json.loads(timers)
            timer = [t for t in timers if t['name'] == name]
            ret = timer[0] if len(timer) else False
            if log: logger.write('{}: {}'.format(name, ret))
        return ret

    @staticmethod
    def unset(name):
        timers = AlarmStore.Location.getProperty(AlarmStore.PropertyName)
        timers = json.loads(timers)
        timers = [t for t in timers if t['name'] != name]
        if len(timers):
            tostore = AlarmStore._format(details)
        else:
            AlarmStore.Location.clearProperty(AlarmStore.PropertyName)

class Alarm:
    ReminderSuffix = '-reminder'

    def __init__(self, name, friendly):
        self.name = name
        self.friendly = friendly
        self.settings = xbmcaddon.Addon().getSetting
        self.language = xbmcaddon.Addon().getLocalizedString

    def _doAction(self):
        if self.settings('actions.waitforscreensaver') == 'false':
            logger.write('Executing CECStandby builtin')
            xbmc.executebuiltin('XBMC.CECStandby')
        if self.settings('actions.stopmedia') == 'true':
            logger.write('Stopping the current player')
            xbmc.executebuiltin('XBMC.PlayerControl(Stop)')
        if self.settings('actions.returnto') != '':
            logger.write('Returning to the {}'.format(self.settings('actions.returnto')))
            xbmc.executebuiltin('XBMC.ActivateWindow({})'.format(self.settings('actions.returnto')))
        AlarmStore.unset(self.name)

    def set(self):
        ret = None
        aTimeout = xbmcgui.Dialog().input(self.language(32072), type=xbmcgui.INPUT_NUMERIC)
        if aTimeout:
            aTimeout = int(aTimeout)
            remindername = '{}{}'.format(self.name, Alarm.ReminderSuffix)
            logger.write('Setting {} for {} minutes'.format(self.name, aTimeout))
            xbmc.executebuiltin('XBMC.AlarmClock({0}, XBMC.RunScript("{1}", "action=expired&name={0}"), "{2}:00", silent)'.format(self.name, xbmcaddon.Addon().getAddonInfo('id'), aTimeout))
            if self.settings('notifications.start') == 'true':
                xbmcgui.Dialog().notification(self.friendly, '{} {} {}'.format(self.language(32075), aTimeout, self.language(32073)))
            aDetails = {'name': self.name, 'reminder': remindername, 'friendly': self.friendly, 'start': int(time.time()), 'timeout': aTimeout * 60}
            ret = AlarmStore.set(aDetails)
            ret = True if not ret else ret[1]
            if ret:
                logger.write('{} created: {}'.format(self.name, ret))
                if self.settings('notifications.duration') == 'true':
                    if self.settings('notifications.duration.unit') == self.language(30040):
                        rTimeout = aTimeout - int(self.settings('notifications.duration.value'))
                    elif self.settings('notifications.duration.unit') == self.language(30041):
                        rTimeout = aTimeout - ((aTimeout * int(self.settings('notifications.duration.value'))) / 100)
                    xbmc.executebuiltin('XBMC.AlarmClock({0}, "Notification({0}, {1})", "{2}:00", silent)'.format(self.friendly, self.language(32071).format('{} {}'.format(aTimeout - rTimeout, self.language(32073))), rTimeout))
        else:
            logger.write('User cancelled setting alarm')
            ret = False
        return ret

    def cancel(self):
        logger.write('Cancelling {}'.format(self.name))
        timer = AlarmStore.get(self.name)
        xbmc.executebuiltin('XBMC.CancelAlarm({}, silent)'.format(self.name))
        xbmc.executebuiltin('XBMC.CancelAlarm({}, silent)'.format(timer['reminder']))
        if timer and self.settings('notifications.cancel') == 'true': xbmcgui.Dialog().notification(timer['friendly'], '{} {}'.format(timer['friendly'], self.language(32076)))
        AlarmStore.unset(self.name)

    def isSet(self, log=True):
        if log: logger.write('Checking for {}'.format(self.name))
        timer = AlarmStore.get(self.name)
        ret = True if timer else False
        if log: logger.write('{} exists: {}'.format(self.name, ret))
        return ret

    def getTimeLeft(self):
        ret = None
        logger.write('Checking time left on {}'.format(self.name))
        if self.isSet(log=False):
            timer = AlarmStore.get(self.name)
            if timer:
                ret = (timer['start'] + timer['timeout']) - int(time.time())
                logger.write('{} has {} seconds left'.format(self.name, ret))
        return ret

    def expired(self):
        logger.write('{} has expired'.format(self.name))
        self._doAction()