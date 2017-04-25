local mp_utils = require 'mp.utils'
require 'os'

function trim(path)
    return string.match(path, '^%s*(.-)%s*$')
end

function run(t)
    return trim(mp_utils.subprocess(t).stdout)
end

function playback_finished(event)
    local reply = run({
        args={
            'python3',
            mp_utils.join_path(os.getenv('HOME'), '.config/mpv/scripts/playback_logger.py'),
            '--percent', mp.get_property_number('percent-pos') or 0.0,
            '--duration', mp.get_property_number('duration') or 0.0,
            '--path', mp.get_property('path'),
        },
        cancellable=false})
    mp.log('info', reply)
end

mp.add_hook('on_unload', 50, playback_finished)