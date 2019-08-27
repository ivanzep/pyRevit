# pylint: skip-file
from pyrevit import EXEC_PARAMS
from pyrevit.runtime.types import ScriptOutputManager, EngineManager


__context__ = 'zerodoc'


print(':fire_engine: Active Engines:')
for engine_info in EngineManager.EngineDict:
    print('Engine Type Id: %s' % engine_info.Key)
    print('Engine: %s' % engine_info.Value)
    print('Engine Unique Id: %s' % engine_info.Value.Id)
    print('Engine Assembly: %s' % engine_info.Value.GetType().Assembly.Location)
    print('\n\n')

print(':rocket: Cached engine? {}'.format('YES' if __cachedengine__ else 'NO'))
print('\n\n')

print(':page_facing_up: Active Output Windows:')
for so in ScriptOutputManager.ActiveOutputWindows:
    print('Output Id: %s' % so.OutputId)
    print('Output Unique Id: %s' % so.OutputUniqueId)
    print('\n\n')
