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

def getCurrentItemTimeout():
    ret = None
    timeout = xbmc.getInfoLabel('Player.TimeRemaining')
    if timeout:
        logger.write("getCurrentTimeout: {}".format(timeout))
        timeout = timeout.split(":")
        if len(timeout) == 2:
            ret = int(timeout[0]) + 1
        elif len(timeout) == 3:
            ret = (int(timeout[0]) * 60) + int(timeout[1]) + 1
        logger.write("getCurrentTimeout: {}".format(ret))
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
                        types = [language(32081), language(32082)]
                        timertype = xbmcgui.Dialog().select(language(32080), types)
                    if timertype == 0:
                        timeout = promptTimeout()
                    elif timertype == 1:
                        timeout = getCurrentItemTimeout()
                    if timertype >= 0 and timeout: alarm.set(timeout=timeout)
                else: # there is a timer so let's get details for it
                    aRemaining = alarm.getTimeLeft()
                    if aRemaining > 60:
                        aRemaining = int(aRemaining / 60)
                        aUnits = language(32073)
                    else:
                        aUnits = language(32074)
                    # display time left and prompt for actions
                    ans = xbmcgui.Dialog().yesno(language(32070), language(32071).format('{} {}'.format(aRemaining, aUnits)), nolabel=language(32998), yeslabel=language(32999).format(alarm.friendly))
                    if ans: # need to take an action
                        logger.write('Showing edit choices')
                        actions = [language(32077), language(32078), language(32082)]
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
                                alarm.set(timeout=timeout)
            elif action == 'expired': # expire the timer
                alarm.expired()