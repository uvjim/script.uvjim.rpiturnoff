import xbmc, xbmcaddon

def write(msg, loglevel=xbmc.LOGDEBUG):
  xbmc.log('[{}] - {}'.format(xbmcaddon.Addon().getAddonInfo('id'), msg), level=loglevel)
