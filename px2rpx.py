import sublime
import sublime_plugin
import re
import time
import os

SETTINGS = {
    "_devices": [
        {
            "name" :"iphone4/4s",
            "info":{
                "dpr": 1,
                "width": 320
                }
            },
        {
            "name" :"iphone5/5s",
            "info":{
                "dpr": 2,
                "width": 320
                }
        },
        {
            "name" :"iphone6",
            "info": {
                "dpr": 2,
                "width": 375
            }
        },
        {
            "name" :"iphone6plus",
            "info": {
                "dpr": 3,
                "width": 414
            }
        },
        {
            "name" :"galaxyS5",
            "info": {
                "dpr": 3,
                "width": 384
            }
        },
        {
            "name" :"galaxyNote2",
            "info": {
                "dpr": 2,
                "width": 360
            }
        }
    ]
}
lastCompletion = {"needFix": False, "value": None, "region": None}

def plugin_loaded():
    init_settings()

def init_settings():
    print(SETTINGS);
    get_settings();
    sublime.load_settings('px2rpx.sublime-settings').add_on_change('get_settings', get_settings)

def get_settings():
    settings = sublime.load_settings('px2rpx.sublime-settings')
    SETTINGS['max_rpx_fraction_length'] = settings.get('max_rpx_fraction_length', 6)
    SETTINGS['available_file_types'] = settings.get('available_file_types', ['.wxss'])
    SETTINGS['devices'] = SETTINGS['_devices'] + settings.get('devices')
    SETTINGS['rpx_standard_length'] = settings.get('rpx_standard_length', 750)

def get_setting(view, key):
    return view.settings().get(key, SETTINGS[key]);

class Px2RpxCommand(sublime_plugin.EventListener):
    def on_text_command(self, view, name, args):
        if name == 'commit_completion':
            view.run_command('replace_rpx')
        return None

    def on_query_completions(self, view, prefix, locations):
        # print('px2rpx start {0}, {1}'.format(prefix, locations))

        # only works on specific file types
        fileName, fileExtension = os.path.splitext(view.file_name())
        if not fileExtension.lower() in get_setting(view, 'available_file_types'):
            return []

        # reset completion match
        lastCompletion["needFix"] = False
        location = locations[0]
        snippets = []

        # get rem match
        match = re.compile("([\d.]+)p(x)?").match(prefix)
        if match:
            lineLocation = view.line(location)
            line = view.substr(sublime.Region(lineLocation.a, location))
            value = match.group(1)
            standardLength = get_setting(view, 'rpx_standard_length')
            # fix: values like `0.5px`
            segmentStart = line.rfind(" ", 0, location)
            if segmentStart == -1:
                segmentStart = 0
            segmentStr = line[segmentStart:location]

            segment = re.compile("([\d.])+" + value).search(segmentStr)
            if segment:
                value = segment.group(0)
                start = lineLocation.a + segmentStart + 0 + segment.start(0)
                lastCompletion["needFix"] = True
            else:
                start = location
            devices = get_setting(view, 'devices');
            for device in devices:
                obj = device['info']
                name = device['name']
                dpr = 1
                for index, obj_item in obj.items():
                    # dpr = device_info['dpr']
                    if index == 'dpr':
                        dpr = obj_item
                rpxValue = round( standardLength * float(value)  / obj['width'] / dpr, get_setting(view, 'max_rpx_fraction_length'))
                # save them for replace fix
                lastCompletion["value"] = str(rpxValue) + 'rpx'
                lastCompletion["region"] = sublime.Region(start, location)
                # set completion snippet
                # snippets += [(value + 'px ->rem(' + str(get_setting(view, 'px_to_rem')) + ')', str(remValue) + 'rem')]
                snippets += [(value+'px->rpx: ' + name, str(rpxValue) + 'rpx')]
        # print(format(snippets))
        return snippets

class ReplaceRpxCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        needFix = lastCompletion["needFix"]
        if needFix == True:
            value = lastCompletion["value"]
            region = lastCompletion["region"]
            # print('replace: {0}, {1}'.format(value, region))
            self.view.replace(edit, region, value)
            self.view.end_edit(edit)