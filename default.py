import sys
import urlparse
import xbmcgui, xbmcaddon
from resources.lib.alarm import Alarm
import resources.lib.logger as logger

####################################################################
#    Aim:        To prompt the user for the duration of the timer
#    Returns:    The value from the input Dialog
#                 Empty string if cancelled
####################################################################
def promptTimeout():
    return xbmcgui.Dialog().input(language(32072), type=xbmcgui.INPUT_NUMERIC)

def getTimeInSeconds(time):
    ret = None
    time = time.split(":")
    if len(time) == 2:
        ret = int(time[0]) + 1
    elif len(time) == 3:
        ret = (int(time[0]) * 60) + int(time[1]) + 1
    return ret

def getCurrentItemTimeout():
    ret = None
    timeout = xbmc.getInfoLabel('Player.TimeRemaining')
    if timeout:
        logger.write("getCurrentTimeout: {}".format(timeout))
        ret = getTimeInSeconds(timeout)
        logger.write("getCurrentTimeout: {}".format(ret))
    return ret

def getNextProgrammeTimeout():
    ret = None
    logger.write("getNextProgrammeTimeout: Started")
    timeout = xbmc.getInfoLabel('VideoPlayer.NextDuration')
    if timeout:
        logger.write("getNextProgrammeTimeout: {}".format(timeout))
        ciTimeout = getCurrentItemTimeout()
        ret = getTimeInSeconds(timeout) + ciTimeout
    logger.write("getNextProgrammeTimeout: Finished - {}".format(ret))
    return ret

def getTimerTypeOptions():
    ret = [language(32081), language(32082)]
    if xbmc.Player().isPlayingVideo(): #check if playing video (we may need to put additional options in)
        videoType = xbmc.Player().getPlayingFile().lower()
        if videoType.startswith('pvr://'):
            ret.append(language(32085))
    return ret

####################################################################
#    Aim:        To determine if the timer can be set based on the
#                amount of time left for the currently playing item
#    Returns:    Boolean - True/False
#    Notes:      Displays a notification if the alarm cannot be set
####################################################################
def validateCurrentItemTimeout(timeout):
    # global settings, language
    ret = True
    if timeout <= int(settings('general.aftercurrentitem.value')):
        ret = False
        xbmcgui.Dialog().notification(language(32070), language(32083).format(language(32084).format(settings('general.aftercurrentitem.value'))), icon=xbmcgui.NOTIFICATION_WARNING)
    logger.write('validateCurrentItemTimeout: {}'.format(ret))
    return ret

####################################################################
#    Main processing
####################################################################
if __name__ == "__main__":
    logger.write('Arguments: {}'.format(sys.argv))
    action = ''
    if len(sys.argv) > 1: # split up the arguments
        args = urlparse.parse_qs(sys.argv[1])
        action = args.get('action', '')
        if action != '': action = action[0]

    if action == '': # open the settings as  the default action
        xbmcaddon.Addon().openSettings()
    else:
        language = xbmcaddon.Addon().getLocalizedString
        settings = xbmcaddon.Addon().getSetting
        alarm = Alarm(name='uvjim.rpiturnoff', friendly=language(32070))
        if xbmc.Player().isPlaying(): # only do something if the Player is playing something
            if action == 'queryset':
                if not alarm.isSet(): # no timer is set so let's create one
                    timertype = 0
                    if settings('general.timertype') == 'true': # let's workout the timer type
                        types = getTimerTypeOptions()
                        timertype = xbmcgui.Dialog().select(language(32080), types)
                    if timertype == 0:
                        timeout = promptTimeout()
                    elif timertype == 1:
                        timeout = getCurrentItemTimeout()
                    elif timertype == 2:
                        timeout = getNextProgrammeTimeout()
                    if timertype >= 0 and timeout:
                        proceed = True
                        if timertype == 1:
                            proceed = validateCurrentItemTimeout(timeout)
                        if settings('general.aftercurrentitem.buffer'):
                            timeout += int(settings('general.aftercurrentitem.buffer'))
                        if proceed: alarm.set(timeout=timeout)
                else: # there is a timer so let's get details for it
                    aRemaining = alarm.getTimeLeft()
                    aMins = aRemaining / 60
                    aSeconds = aRemaining % 60
                    msg = ""
                    if aMins:
                        aRemaining = int(aRemaining / 60)
                        msg += "{} {}".format(aMins, language(32073))
                    if aSeconds:
                        if msg: msg += " "
                        msg += "{} {}".format(aSeconds, language(32074))
                    # display time left and prompt for actions
                    ans = xbmcgui.Dialog().yesno(language(32070), language(32071).format(msg), nolabel=language(32998), yeslabel=language(32999).format(alarm.friendly))
                    if ans: # need to take an action
                        logger.write('Showing edit choices')
                        actions = getTimerTypeOptions()
                        actions.insert(0, language(32077))
                        sel = xbmcgui.Dialog().select(language(32999).format(alarm.friendly), actions)
                        logger.write('Edit action: {}'.format(sel))
                        if sel == 0: # cancel timer
                            alarm.cancel()
                        elif sel == 1: # extend timer
                            extendby = promptTimeout()
                            if extendby: alarm.extend(extendby=extendby)
                        elif sel == 2: # after current item
                            timeout = getCurrentItemTimeout()
                            if timeout:
                                alarm.cancel(notify=False)
                                proceed = validateCurrentItemTimeout(timeout)
                                if proceed:
                                    alarm.set(timeout=timeout)
            elif action == 'expired': # expire the timer
                alarm.expired()