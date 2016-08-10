import sys
import xbmc
import xbmcgui
import xbmcaddon

def logger(msg, loglevel = xbmc.LOGDEBUG):
  xbmc.log('[%s] - %s' % (settings.getAddonInfo('id'), msg), level=loglevel)
  # xbmc.log('[%s] - %s' % (settings.getAddonInfo('id'), msg), level=xbmc.LOGNOTICE)

if __name__ == "__main__":
  settings = xbmcaddon.Addon(id='script.uvjim.rpiturnoff')
  language = settings.getLocalizedString

  if xbmc.Player().isPlaying():
    alarmName = 'shutdowntimer'
    blnSet = False
    blnHasAlarm = xbmc.getCondVisibility('System.HasAlarm(%s)' % alarmName)
    logger('Timer already set = %s' % blnHasAlarm)
    if blnHasAlarm == 0:
      if len(sys.argv) - 1 > 0:
        if sys.argv[1] == 'true':
          logger('Stopping the current player')
          xbmc.executebuiltin('XBMC.PlayerControl(Stop)')
          logger('Returning to the home window')
          xbmc.executebuiltin('XBMC.ActivateWindow(Home)')
        else:
          blnSet = True
      else:
        blnSet = True      
      if blnSet:
        logger('Setting the timer')
        xbmc.executebuiltin('XBMC.AlarmClock(%s, XBMC.RunScript("%s", true))' % (alarmName, settings.getAddonInfo('id')))
    else:
      if xbmc.getCondVisibility('System.AlarmLessOrEqual(%s, 1)' % alarmName) == 0:
        dialog = xbmcgui.Dialog()
        if dialog.yesno(language(32070), language(32071) % xbmc.getInfoLabel('System.AlarmPos'), nolabel=language(32998), yeslabel=language(32999)):
          logger('Cancelling the timer')
          xbmc.executebuiltin('XBMC.CancelAlarm(%s, false)' % alarmName)
