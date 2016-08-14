import sys
import urlparse
import xbmcgui, xbmcaddon
from resources.lib.alarm import Alarm
import resources.lib.logger as logger

if __name__ == "__main__":
    logger.write('Arguments: {}'.format(sys.argv))
    action = ''
    if len(sys.argv) > 1:
        args = urlparse.parse_qs(sys.argv[1])
        action = args.get('action', '')
        if action != '': action = action[0]

    if action == '':
        xbmcaddon.Addon().openSettings()
    else:
        language = xbmcaddon.Addon().getLocalizedString
        alarm = Alarm(name='uvjim.rpiturnoff', friendly=language(32070))
        if xbmc.Player().isPlaying():
            if action == 'queryset':
                if not alarm.isSet():
                    alarm.set()
                else:
                    aRemaining = alarm.getTimeLeft()
                    if aRemaining > 60:
                        aRemaining = int(aRemaining / 60)
                        aUnits = language(32073)
                    else:
                        aUnits = language(32074)
                    ans = xbmcgui.Dialog().yesno(language(32070), language(32071).format('{} {}'.format(aRemaining, aUnits)), nolabel=language(32998), yeslabel=language(32999))
                    if ans: alarm.cancel()
            elif action == 'expired':
                alarm.expired()