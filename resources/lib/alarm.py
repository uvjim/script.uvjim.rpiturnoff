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
    def __init__(self, name, friendly):
        self.name = name
        self.friendly = friendly
        self.settings = xbmcaddon.Addon().getSetting

    def _doAction(self):
        logger.write('Stopping the current player')
        xbmc.executebuiltin('XBMC.PlayerControl(Stop)')
        logger.write('Returning to the home window')
        xbmc.executebuiltin('XBMC.ActivateWindow(Home)')
        AlarmStore.unset(self.name)

    def set(self):
        ret = None
        timeout = xbmcgui.Dialog().input(xbmcaddon.Addon().getLocalizedString(32072), type=xbmcgui.INPUT_NUMERIC)
        if timeout:
            timeout = int(timeout)
            logger.write('Setting {} for {} minutes'.format(self.name, timeout))
            aDetails = {'name': self.name, 'friendly': self.friendly, 'start': int(time.time()), 'timeout': timeout * 60}
            ret = AlarmStore.set(aDetails)
            ret = True if not ret else ret[1]
            logger.write('{} created: {}'.format(self.name, ret))
            if ret:
                xbmc.executebuiltin('XBMC.AlarmClock({0}, XBMC.RunScript("{1}", "action=expired&name={0}"), "{2}:00", silent)'.format(self.name, xbmcaddon.Addon().getAddonInfo('id'), timeout))
                if self.settings('notifications.start') == 'true':
                    xbmcgui.Dialog().notification('{} has been set for {} minutes'.format(self.friendly, timeout), xbmcaddon.Addon().getAddonInfo('id'))
        else:
            logger.write('User cancelled setting alarm')
            ret = False
        return ret

    def cancel(self):
        logger.write('Cancelling {}'.format(self.name))
        xbmc.executebuiltin('XBMC.CancelAlarm({}, silent)'.format(self.name))
        timer = AlarmStore.get(self.name)
        if timer and self.settings('notifications.cancel') == 'true': xbmcgui.Dialog().notification('{} has been cancelled'.format(timer['friendly']), xbmcaddon.Addon().getAddonInfo('id'))
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