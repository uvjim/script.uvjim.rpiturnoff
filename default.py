import sys
import urlparse
import json
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

####################################################################
#    Aim:        To convert a time string into seconds
#    Returns:    The number of seconds
####################################################################
def getTimeInSeconds(time):
    ret = None
    ret = sum(int(x) * 60 ** i for i, x in enumerate(reversed(time.split(":"))))
    return ret

####################################################################
#    Aim:        To retrieve the amount of remaining time of the
#                currently playing item (in seconds)
#    Returns:    The reminaing time of the current item in seconds
####################################################################
def getCurrentItemTimeout():
    ret = None
    timeout = xbmc.getInfoLabel('Player.TimeRemaining')
    if timeout:
        logger.write("getCurrentTimeout: Raw: {}".format(timeout))
        ret = getTimeInSeconds(timeout)
        logger.write("getCurrentTimeout: Seconds: {}".format(ret))
    return ret

####################################################################
#    Aim:        To retrieve the amount of remaining time of the
#                next programmed (PVR) item (in seconds)
#    Returns:    The reminaing time of the next programme in seconds
####################################################################
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

####################################################################
#    Aim:        To retrieve the amount of remaining time for the
#                playlist (or time until the given playlist item)
#    Returns:    The reminaing time in seconds
####################################################################
def getPlaylistTimeout(afterPos=0):
    ret = None
    playlist = None
    logger.write("getPlaylistTimeout: Started")
    if xbmc.Player().isPlayingVideo():
        logger.write("getPlaylistTimeout: Checking video playlist")
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    elif xbmc.Player().isPlayingAudio():
        logger.write("getPlaylistTimeout: Checking music playlist")
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    if playlist:
        curPos = playlist.getposition()
        logger.write("getPlaylistTimeout: Current position: {}".format(curPos))
        if curPos != '':
            afterPos = afterPos if afterPos else playlist.size()
            logger.write("getPlaylistTimeout: Start idx: {}, End idx: {}".format(curPos, afterPos))
            ret = 0
            logger.write("getPlaylistTimeout: Executing JSON-RPC for playlist details")
            jsonDetails = {
                "id": "{}-getPlaylistTimeout".format(xbmcaddon.Addon().getAddonInfo('id')),
                "jsonrpc": "2.0",
                "method": "Playlist.GetItems",
                "params": {
                    "playlistid": playlist.getPlayListId(),
                    "properties": [
                        "duration"
                    ],
                    "limits": {
                        "start": curPos
                    }
                }
            }
            playlist = xbmc.executeJSONRPC(json.dumps(jsonDetails))
            logger.write("getPlaylistTimeout: Playlist details: {}".format(playlist))
            playlist = json.loads(playlist)['result']['items']
            for idx, itm in enumerate(playlist):
                duration = int(itm['duration'])
                if idx == 0: duration = duration - getTimeInSeconds(xbmc.getInfoLabel('Player.Time'))
                logger.write("getPlaylistTimeout: idx {} duration: {} ({})".format(idx + curPos, duration, itm['duration']))
                ret += duration
        else:
            logger.write("getPlaylistTimeout: Playlist not playing")
    logger.write("getPlaylistTimeout: Finished - {}".format(ret))
    return ret

####################################################################
#    Aim:        To build the items to be shown to the user for
#                timer types
#    Returns:    A list containing the available timer types
####################################################################
def getTimerTypeOptions():
    ret = []
    playlist = None
    logger.write("getTimerTypeOptions: Started")
    if alarm.isSet():
        ret.extend([language(32077), language(32078)])
    else:
        ret.append(language(32081))
    ret.append(language(32082))
    if xbmc.Player().isPlayingVideo(): # check if playing video (we may need to put additional options in)
        videoType = xbmc.Player().getPlayingFile().lower()
        if videoType.startswith('pvr://'):
            logger.write("getTimerTypeOptions: PVR playing")
            ret.append(language(32085))
        else:
            logger.write("getTimerTypeOptions: Checking video playlist")
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    elif xbmc.Player().isPlayingAudio():
        logger.write("getTimerTypeOptions: Checking music playlist")
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    if playlist:
        plPos = playlist.getposition()
        logger.write("getTimerTypeOptions: Playlist position: {}".format(plPos))
        if plPos != '': # we've got a playlist and it is being played (idx starts 1)
            ret.extend([language(32086)])
    logger.write("getTimerTypeOptions: Finished - {}".format(ret))
    return ret

####################################################################
#    Aim:        To determine if the timer can be set based on the
#                amount of time left for the currently playing item
#    Returns:    Boolean - True/False
#    Notes:      Displays a notification if the alarm cannot be set
####################################################################
def validateCurrentItemTimeout(timeout):
    ret = True
    if timeout <= int(settings('general.aftercurrentitem.value')) * 60:
        ret = False
        xbmcgui.Dialog().notification(language(32070), language(32083).format(language(32084).format(settings('general.aftercurrentitem.value'))), icon=xbmcgui.NOTIFICATION_WARNING)
    logger.write('validateCurrentItemTimeout: {}'.format(ret))
    return ret

####################################################################
#    Aim:        To process the timer type options
#    Returns:    N/A
####################################################################
def doTimerType(timertype):
    ret = None
    timeout = None
    if alarm.isSet() and (timertype != language(32077) and timertype != language(32078)):
        alarm.cancel(notify=False)
    if timertype == language(32081): # custom
        timeout = promptTimeout()
        if timeout: timeout = int(timeout) * 60
    elif timertype == language(32082): # after current item
        timeout = getCurrentItemTimeout()
        timeout = timeout if validateCurrentItemTimeout(timeout) else None
    elif timertype == language(32085): # after next programme
        timeout = getNextProgrammeTimeout()
    elif timertype == language(32086): # after playlist
        timeout = getPlaylistTimeout()
    elif timertype == language(32077): # turn off
        alarm.cancel()
    elif timertype == language(32078): # extend
        extendby = promptTimeout()
        if extendby:
            extendby = int(extendby) * 60
            alarm.extend(extendby)

    if timeout:
        if timertype == language(32082) or timertype == language(32085):
            if settings('general.aftercurrentitem.buffer'):
                timeout += int(settings('general.aftercurrentitem.buffer')) * 60
        alarm.set(timeout=timeout)

    return ret

####################################################################
#    Main processing
####################################################################
if __name__ == "__main__":
    logger.write('Main: Arguments: {}'.format(sys.argv))
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
        if action == 'expired': # expire the timer
            alarm.expired()
        else:
            if xbmc.Player().isPlaying(): # only do something if the Player is playing something
                if action == 'queryset':
                    if not alarm.isSet(): # no timer is set so let's create one
                        timertype = 0
                        if settings('general.timertype') == 'true': # let's workout the timer type
                            types = getTimerTypeOptions()
                            timertype = xbmcgui.Dialog().select(language(32080), types)
                        if timertype >= 0:
                            logger.write("Main: Timer type selected: {} - {}".format(timertype, types[timertype]))
                            doTimerType(types[timertype])
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
                            actions = getTimerTypeOptions()
                            logger.write('Main: Showing edit choices')
                            sel = xbmcgui.Dialog().select(language(32999).format(alarm.friendly), actions)
                            if sel != -1:
                                logger.write('Main: Edit action selected: {} - {}'.format(sel, actions[sel]))
                                doTimerType(actions[sel])
