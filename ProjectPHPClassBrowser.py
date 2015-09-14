import os, fnmatch, re, threading, sublime, sublime_plugin, sys, codecs, subprocess

class _projectPHPClassUtils:
    def __init__(self, rootPath):
        self.rootPath = rootPath
        self.dbFilename = 'phpclass.sublime-classdb'

    def get_db_path(self):
        if(self.rootPath == None):
            return None
        return os.path.join( self.rootPath , self.dbFilename )

    def get_db_classnames(self):
        data = []
        compPath = self.get_db_path()
        if (compPath == None):
          return []
        if(['linux','osx'].count(sublime.platform())):
          # posix, use cut
          try:
            command = 'cut -d ";" -f 3 ' + compPath
            pipe = subprocess.Popen([command], shell=True ,stdout=subprocess.PIPE ,stderr=subprocess.PIPE)
            out, err = pipe.communicate()
            out = str(out.decode('utf-8'))
            data = list(set(out.split("\n")))
          except:
            exc = sys.exc_info()[1]
            sublime.status_message(str(exc))
        else:
          with codecs.open(compPath, 'r', encoding='utf-8', errors='ignore') as cfp:
              line = cfp.readline()
              while len(line) != 0:
                  try:
                      filepath,linedef,cname,cmethod,cargs,cvisibility,ccontext = line.split(";")
                      if( data.count(cname) == 0 ):
                          data.append(cname)
                  except:
                      # print "errors with line: %s" % (line,)
                      pass
                  line = cfp.readline()
        return data

    def get_db_data(self, classname):
        data = {}
        compPath = self.get_db_path()
        if (compPath == None):
          return {}
        if(['linux','osx'].count(sublime.platform())):
          # posix, use grep
          command = 'grep ";'+classname+';" ' + compPath
          pipe = subprocess.Popen([command], shell=True ,stdout=subprocess.PIPE ,stderr=subprocess.PIPE)
          out, err = pipe.communicate()
          out = str(out.decode('utf-8'))
          for line in out.split("\n"):
            try:
                filepath,linedef,cname,cmethod,cargs,cvisibility,ccontext = line.split(";")
                if( cname == classname ):
                    classline, methodspan = linedef[1:-1].split('-')
                    methodline = int(classline) + int(methodspan)

                    if( (cname in data) == False ):
                       data[cname.strip()] = { 'name': cname.strip(), 'methods': [] , 'filepath' : filepath.strip(), 'line' : int(classline) }

                    data[cname.strip()]['methods'].append({
                        'name': cmethod,
                        'args': cargs,
                        'definition': ' '.join([cvisibility.strip(),ccontext.strip()]).strip() +' '+cmethod.strip()+cargs.strip(),
                        'line': methodline
                    })
            except:
                # print "errors with line: %s" % (line,)
                pass
        else:
          with codecs.open(compPath, 'r', encoding='utf-8', errors='ignore') as cfp:
              line = cfp.readline()
              while len(line) != 0:
                  try:
                      filepath,linedef,cname,cmethod,cargs,cvisibility,ccontext = line.split(";")
                      if( cname == classname ):
                          classline, methodspan = linedef[1:-1].split('-')
                          methodline = int(classline) + int(methodspan)

                          if( (cname in data) == False ):
                             data[cname.strip()] = { 'name': cname.strip(), 'methods': [] , 'filepath' : filepath.strip(), 'line' : int(classline) }

                          data[cname.strip()]['methods'].append({
                              'name': cmethod,
                              'args': cargs,
                              'definition': ' '.join([cvisibility.strip(),ccontext.strip()]).strip() +' '+cmethod.strip()+cargs.strip(),
                              'line': methodline
                          })
                  except:
                      # print "errors with line: %s" % (line,)
                      pass
                  line = cfp.readline()
        return data

    def dbPresent(self):
        compPath = self.get_db_path()
        if (compPath == None):
          return False
        return os.path.isfile(compPath)

    def is_browser_view(self, view):
        if(view.is_scratch() == True and (view.name() == 'PHP Class Browser' or view.name() == 'PHP Class Methods')):
              return True
        return False

    def find_browser_view(self):
        window = sublime.active_window()
        for view in window.views():
            if(self.is_browser_view(view)):
                return view
        return None

    def find_methods_view(self):
        window = sublime.active_window()
        for view in window.views():
            if(self.is_browser_view(view) and view.name() == 'PHP Class Methods'):
                return view
        return None

    def is_updating_view(self, view):
        if(view.is_scratch() == True and view.name() == 'Please wait.'):
            return True
        return False

    def find_updating_views(self):
        window = sublime.active_window()
        views = []
        for view in window.views():
            if(self.is_updating_view(view)):
                views.append(view)
        return views

    def close_all_updating(self):
        window = sublime.active_window()
        updatingviews = self.find_updating_views()
        for updatingview in updatingviews:
            window.focus_view(updatingview)
            window.run_command('close')

    def get_num_panels(self):
        settings = sublime.load_settings('ProjectPHPClassBrowser.sublime-settings')
        use_two = settings.get('two_panels') or False
        if( isinstance(use_two, bool) ):
            if( use_two == True):
                return 2
        return 1

    def find_file(self, start_at, look_for):
        start_at = os.path.abspath(start_at)
        if not os.path.isdir(start_at):
            start_at = os.path.dirname(start_at)
        while True:
            for filename in os.listdir(start_at):
                if fnmatch.fnmatch(filename, look_for):
                    return os.path.join(start_at, filename)
            continue_at = os.path.abspath(os.path.join(start_at, '..'))
            if continue_at == start_at:
                return None
            start_at = continue_at

    def get_project_folders(self, view):
        window = sublime.active_window()
        if(int(sublime.version()) >= 3000):
            # ST3 - use project data
            project_data = window.project_data()
            out = []

            for folder in project_data.get('folders'):
              if (folder.startswith('/') != True):
                out.append( os.path.dirname(window.project_file_name())+'/'+ folder.get('path') )
              else:
                out.append(folder.get('path'))

            if (len(out) == 0):
                return window.folders()
            return out
        else:
            # ST2 - try to find data
            if(view != None):
                path = view.file_name()
                completions_location = None
                if path:
                    location = None
                    # Try to find the phpclass.sublime-classdb file
                    for filename in ['*.sublime-project', 'phpclass.sublime-classdb']:
                      compPath = self.find_file(path, filename)
                      if(compPath != None):
                        location = os.path.dirname(compPath)
                        break
                    if location:
                      return [location]
                    else:
                        sublime.status_message('Sublime project file not found. Are you sure it is saved in the root of your project?')
            # nothing found
            return window.folders()

class ProjectPHPClassCompletionsScan(threading.Thread):
    def __init__(self, folders, timeout):
        threading.Thread.__init__(self)
        self.folders = folders
        self.timeout = timeout
        self.result = None

    def get_php_executable(self):
        settings = sublime.load_settings('ProjectPHPClassBrowser.sublime-settings')
        return settings.get('php_executable') or 'php'

    def ensure_dir(self,f):
        d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d)
            return os.path.exists(d)
        else :
            return True

    def get_parser_file(self):
        if(int(sublime.version()) >= 3000):
            parsercontents = sublime.load_resource('Packages/Project PHP ClassBrowser/parse_file.php')
            parser_path = os.path.join( sublime.packages_path() , 'Project PHP ClassBrowser', 'parse_file.php' )
            direxists = self.ensure_dir(parser_path)
            with codecs.open(parser_path, 'w', encoding='utf-8', errors='ignore') as cfp:
                cfp.write(parsercontents)
            if(os.path.isfile(parser_path)):
                return parser_path
        else:
            return os.path.join( sublime.packages_path() , 'Project PHP ClassBrowser', 'parse_file.php' )
        return None

    def get_parsable_extensions(self):
        settings = sublime.load_settings('ProjectPHPClassBrowser.sublime-settings')
        extensions = settings.get('file_extensions') or None
        if(isinstance(extensions,list)):
            return extensions
        return ['.inc','.php']

    def run(self):
        try:
            utils = _projectPHPClassUtils(self.folders[0])
            compPath = utils.get_db_path()
            if ( compPath == None ):
                return
            with open(compPath, 'w') as cfp:
                cfp.close()
            php_executable = self.get_php_executable()
            parser = self.get_parser_file()
            patterns = self.get_parsable_extensions()
            for rootPath in self.folders:
                with open(compPath, 'a') as cfp:
                    for root, dirs, files in os.walk(rootPath):
                        for p in patterns:
                            for f in files:
                                if f.endswith(p):
                                    #parse the file and save class methods
                                    filepath = os.path.join(root, f)

                                    pipe = None
                                    if(sublime.platform() == 'windows'):
                                      CREATE_NO_WINDOW = 0x08000000
                                      pipe = subprocess.Popen([php_executable, parser, filepath], stdout=cfp, stderr=cfp, shell=False, creationflags=CREATE_NO_WINDOW)
                                    else:
                                      pipe = subprocess.Popen([php_executable, parser, filepath], stdout=cfp, stderr=cfp)

                                    out, err = pipe.communicate()
            # try to update browser window
            window = sublime.active_window()
            browser_view = utils.find_browser_view()
            if(browser_view != None):
                browser_view.run_command("refresh_browser_view", {"rootPath": self.folders[0] } )
            sublime.status_message('Project Class Scan Completed.')
        except:
            exc = sys.exc_info()[1]
            sublime.status_message(str(exc))
            pass

class OpenUpdatingCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        view.set_read_only(False)
        view.set_scratch(True)
        # remove view content if present
        viewcontent = sublime.Region(0,view.size())
        view.erase(edit,viewcontent)
        view.set_name('Please wait.')
        view.insert(edit, view.size(),'Updating list... ')
        view.set_read_only(True)

class ProjectPhpclassOpenLayoutCommand(sublime_plugin.WindowCommand):
    def run(self):
        window = sublime.active_window()
        rootPath = window.folders()[0]
        if(int(sublime.version()) >= 3000):
            # ST3 - use project data
            project_data = window.project_data()
            rootPath = project_data.get('folders')[0].get('path')
        utils = _projectPHPClassUtils(rootPath)
        if( utils.dbPresent() != True ):
            sublime.status_message('No DataBase Found!')
            return
        browser_view = utils.find_browser_view()
        if( browser_view != None ):
            browser_view.run_command("refresh_browser_view", {"rootPath": rootPath } )
            return
        oldlayout = window.get_layout()
        settings = sublime.load_settings('phpclass_browser.sublime-settings')
        settings.set('php_class_browser_revert_layout',oldlayout)
        sublime.save_settings('phpclass_browser.settings')

        layout = self.get_layout_config(utils.get_num_panels())
        window.set_layout(layout)
        window.run_command("refresh_browser_view", {"rootPath": rootPath } )

    def get_layout_config(self, num_panels):
        settings = sublime.load_settings('ProjectPHPClassBrowser.sublime-settings')
        if(num_panels == 2):
          two_panel_layout = settings.get('two_panel_layout') or None
          try:
            if( two_panel_layout != None and len( two_panel_layout.get('cells') ) == 3):
              return two_panel_layout
          except:
            pass
          #two panels default
          return {
              'cols': [0.0, 0.5, 1.0],
              'rows': [0.0, 0.75, 1.0],
              'cells': [[0, 0, 2, 1], [0, 1, 1, 2], [1, 1, 2, 2]]
          }
        else:
          one_panel_layout = settings.get('one_panel_layout') or None
          try:
            if( one_panel_layout != None and len( one_panel_layout.get('cells') ) == 2):
              return one_panel_layout
          except:
            pass
          #one panel default
          return {
              'cols': [0.0, 1.0],
              'rows': [0, 0.75, 1],
              'cells': [[0, 0, 1, 1], [0, 1, 1, 2]]
          }

class ProjectPhpclassCloseLayoutCommand(sublime_plugin.WindowCommand):
    def run(self):
        window = sublime.active_window()
        settings = sublime.load_settings('phpclass_browser.sublime-settings')
        oldlayout = settings.get('php_class_browser_revert_layout')
        if( oldlayout != None ):
            window.set_layout(oldlayout)
        else:
            window.set_layout({
                "cols": [0.0, 1.0],
                "rows": [0, 1],
                "cells": [[0, 0, 1, 1]]
            })
        # here rootPath could be also None
        utils = _projectPHPClassUtils(window.folders()[0])
        utils.close_all_updating()
        if(utils.get_num_panels() == 2):
            methodsview = utils.find_methods_view()
            if( methodsview != None ):
                window.focus_view(methodsview)
                window.run_command('close')
        browser_view = utils.find_browser_view()
        if( browser_view != None ):
            window.focus_view(browser_view)
            window.run_command('close')
        window.focus_group(0)

class ProjectPhpclassCreateDatabaseCommand(sublime_plugin.WindowCommand):
    def run(self):
        window = sublime.active_window()
        folders = []
        if(int(sublime.version()) >= 3000):
            # ST3 - use project data
            project_data = window.project_data()
            for folder in project_data.get('folders'):
              if (folder.startswith('/') != True):
                folders.append( os.path.dirname(window.project_file_name())+'/'+ folder.get('path') )
              else:
                folders.append(folder.get('path'))
        else:
            folders.append(window.folders()[0])

        if(len(folders) > 0):
            threads = []
            thread = ProjectPHPClassCompletionsScan(folders, 5)
            threads.append(thread)
            thread.start()

class FillBrowserViewCommand(sublime_plugin.TextCommand):
    def run(self, edit, args):
        rootPath = args.get('rootPath')
        group = args.get('group') or 1
        classname = args.get('classname') or None
        view = self.view
        window = sublime.active_window()
        # remove view content if present
        viewcontent = sublime.Region(0,view.size())
        view.erase(edit,viewcontent)
        if rootPath:
            utils = _projectPHPClassUtils(rootPath)
        else:
            if(int(sublime.version()) >= 3000):
                # ST3 - use project data
                project_data = window.project_data()
                utils = _projectPHPClassUtils( project_data.get('folders')[0].get('path') )
            else:
                utils = _projectPHPClassUtils( window.folders()[0] )
        if(utils.get_num_panels() == 2):
            window.focus_group(group)
            if(group == 1):
                self._fill_classes(view, edit, utils)
            else:
                classes = self._get_classes(utils)
                if(classname == None):
                    classname = classes[0]
                self._fill_methods(view, edit, utils, classname)
        else:
            self._allinone(view, edit, utils)
            utils.close_all_updating();

    def _get_classes(self, utils):
        classnames = utils.get_db_classnames()
        if( self.get_classnames_order() == 'alpha' ):
            classnames = sorted(classnames)
        return classnames

    def _fill_classes(self, view, edit, utils):
        view.set_read_only(False)
        viewcontent = sublime.Region(0,view.size())
        view.erase(edit,viewcontent)
        regions = []
        numregions = 0
        classnames = self._get_classes(utils)
        for classname in classnames:
            data = utils.get_db_data(classname)
            for k in sorted(data.keys()):
                item = data[k]
                if(numregions > 0):
                    view.insert(edit, view.size(),'\n')
                numregions += 1
                initregion = view.size()
                view.insert(edit, view.size(), item.get('name'))
                endregion = view.size()
                regions.append(sublime.Region(initregion,endregion))
                # view.insert(edit, view.size(),'\n')
        view.add_regions('classbrowser' , regions, 'classbrowser', 'bookmark',sublime.DRAW_OUTLINED)
        view.end_edit(edit)
        view.set_read_only(True)

    def _fill_methods(self, view, edit, utils, classname):
        # remove view content if present
        view.set_read_only(False)
        viewcontent = sublime.Region(0,view.size())
        view.erase(edit,viewcontent)
        data = utils.get_db_data(classname)
        for k in sorted(data.keys()):
            item = data[k]
            view.insert(edit, view.size(), item.get('name'))
            view.insert(edit, view.size(),'\n\t# '+item.get('filepath'))
            for method in item.get('methods'):
                view.insert(edit, view.size(),'\n\t' + method.get('definition'))
        view.end_edit(edit)
        view.set_read_only(True)

    def _allinone(self, view, edit, utils):
        regions = []
        foldregions = []
        numregions = 0
        classnames = self._get_classes(utils)
        for classname in classnames:
            data = utils.get_db_data(classname)
            for k in sorted(data.keys()):
                item = data[k]
                if(numregions > 0):
                    view.insert(edit, view.size(),'\n')
                numregions += 1
                initregion = view.size()
                view.insert(edit, view.size(), item.get('name'))
                initfold = view.size()
                view.insert(edit, view.size(),'\n\t# '+item.get('filepath'))
                for method in item.get('methods'):
                    view.insert(edit, view.size(),'\n\t' + method.get('definition'))
                endregion = view.size()
                regions.append(sublime.Region(initregion,initfold))
                foldregions.append(sublime.Region(initfold,endregion))
                # view.insert(edit, view.size(),'\n')
        view.add_regions('classbrowser' , regions, 'classbrowser', 'bookmark',sublime.DRAW_OUTLINED)
        view.add_regions('classbrowserfoldregions' , foldregions, 'classbrowserfoldregions', 'fold', sublime.HIDDEN)
        view.fold(foldregions)
        view.end_edit(edit)
        view.set_read_only(True)

    def get_classnames_order(self):
        settings = sublime.load_settings('ProjectPHPClassBrowser.sublime-settings')
        order = settings.get('class_order') or 'alpha'
        if( order != 'alpha' and order != 'definition'):
            order = 'alpha'
        return order

class RefreshBrowserViewCommand(sublime_plugin.WindowCommand):
    def run(self, rootPath):
        window = sublime.active_window()
        if rootPath:
            utils = _projectPHPClassUtils(rootPath)
        else:
            if(int(sublime.version()) >= 3000):
                # ST3 - use project data
                project_data = window.project_data()
                utils = _projectPHPClassUtils( project_data.get('folders')[0].get('path') )
                rootPath = project_data.get('folders')[0].get('path')
            else:
                utils = _projectPHPClassUtils( window.folders()[0] )
                rootPath = window.folders()[0]
        if( utils.dbPresent() != True ):
            sublime.status_message('No DataBase Found!')
            return

        views = []

        view = self.open_new_view(window, 1, 'PHP Class Browser')
        views.append(view)

        if( self.get_use_loading() == True):
            window.focus_view(view)
            updatingview = window.new_file()
            updatingview.run_command("open_updating")

        if(utils.get_num_panels() == 2):
            view = self.open_new_view(window, 2, 'PHP Class Methods')
            views.append(view)

            if( self.get_use_loading() == True):
                window.focus_view(view)
                updatingview = window.new_file()
                updatingview.run_command("open_updating")

        thread = ProjectPHPClassBrowserFiller(views, rootPath)
        thread.start()

    def open_new_view(self, window, group, name):
        window.focus_group(group)
        view = window.new_file()
        view.set_scratch(True)
        view.set_name(name)
        view.set_read_only(False)
        return view

    def get_use_loading(self):
        settings = sublime.load_settings('ProjectPHPClassBrowser.sublime-settings')
        use_loading = settings.get('use_loading') or False
        if( isinstance(use_loading, bool) ):
            return use_loading
        return False

class ProjectPHPClassBrowserFiller(threading.Thread):
    def __init__(self, views, rootPath):
        threading.Thread.__init__(self)
        self.views = views
        self.rootPath = rootPath

    def run(self):
        if(len(self.views) == 2):
            for index,view in enumerate(self.views):
                view.run_command("fill_browser_view", { "args": {"rootPath" : self.rootPath, "group": index+1, "classname":None} })
        elif(len(self.views) == 1):
            self.views[0].run_command("fill_browser_view", { "args": {"rootPath" : self.rootPath, "group": 1, "classname":None} })
        else:
            sublime.status_message('No views to fill!!')

class ClickPhpclassBrowser(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        window = sublime.active_window()
        if(int(sublime.version()) >= 3000):
            # ST3 - use project data
            project_data = window.project_data()
            utils = _projectPHPClassUtils( project_data.get('folders')[0].get('path') )
        else:
            utils = _projectPHPClassUtils( window.folders()[0] )
        if( utils.is_browser_view(view) != True ):
            return
        point = view.sel()[0]
        if(point.begin() == point.end()):
            return

        window.focus_view(view)
        word = view.substr(view.word(point))
        line = view.substr(view.line(point))
        methodname = None
        if( line.startswith('\t') or re.match('\s+', line, re.IGNORECASE) ):
            methodname = word
            regionbefore = sublime.Region(0,point.end())
            lineregions = view.split_by_newlines(regionbefore)
            clindex = len( lineregions ) - 1
            # for lineregion in lineregions:
            classname = None
            while( classname == None and clindex >= 0 ):
                line = view.substr(lineregions[clindex])
                clindex -= 1
                if(line.startswith('\t') == False and not re.match('\s+', line, re.IGNORECASE) ):
                    classname = line
        else:
            classname = word
        classname = classname.split('\n')[0].strip()
        if(len(classname)>0):
            try:
                if(utils.get_num_panels() == 2):
                    if(view.name() == 'PHP Class Methods'):
                        # in methods view. open file definition
                        self._open_file_definition(window, utils, classname, methodname)
                    else:
                        # in classes view. update methods view
                        methodview = utils.find_methods_view()
                        rootPath = window.folders()[0]
                        if(int(sublime.version()) >= 3000):
                            project_data = window.project_data()
                            rootPath = project_data.get('folders')[0].get('path')
                        args = {"rootPath" : rootPath, "group": 2, "classname": classname}
                        methodview.run_command("fill_browser_view", { "args": args })
                else:
                    # all in one... go, go, go!
                    self._open_file_definition(window, utils, classname, methodname)
            except:
                sublime.status_message('Unknown Class Name: '+str(classname))

    def _open_file_definition(self, window, utils, classname, methodname):
        data = utils.get_db_data(classname)
        window.focus_group(0)
        window.open_file(data.get(classname)['filepath'])
        new_view = window.active_view()
        if( methodname != None ):
            for methoddefinition in data.get(classname)['methods']:
                if( methoddefinition['name'] == methodname ):
                    new_view.run_command("goto_line", {"line": methoddefinition['line'] } )
                    return
            #if not found
            new_view.run_command("goto_line", {"line": data.get(classname)['line'] } )
        else:
            new_view.run_command("goto_line", {"line": data.get(classname)['line'] } )


class GotoLineCommand(sublime_plugin.TextCommand):
    def run(self, edit, line):
        # Convert from 1 based to a 0 based line number
        line = int(line) - 1
        # Negative line numbers count from the end of the buffer
        if line < 0:
            lines, _ = self.view.rowcol(self.view.size())
            line = lines + line + 1
        pt = self.view.text_point(line, 0)
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(pt))
        self.view.show(pt)

class ProjectPHPClassBrowser(sublime_plugin.EventListener):
    def on_selection_modified(self,view):
        window = sublime.active_window()
        if( window == None ):
            return
        utils = _projectPHPClassUtils(None)
        if( utils.is_browser_view(view) != True ):
            return
        point = view.sel()[0]
        if(point.begin() == point.end()):
            return
        word = view.substr(view.word(point))
        window.run_command("click_phpclass_browser", {})

    def on_load(self, view):
        sublime.status_message('Project PHP ClassBrowser starting.')
        window = sublime.active_window()
        utils = _projectPHPClassUtils(None)
        if( utils.is_browser_view(view) != True ):
            return
        folders = utils.get_project_folders(view)
        view.run_command("refresh_browser_view", {"rootPath": folders[0] } )
        for folder in folders:
            rootPath = utils.find_file(folder, '*.sublime-project')
            if( os.path.isfile( rootPath ) ):
                view.run_command("refresh_browser_view", {"rootPath": rootPath } )
                return
        # none found
        sublime.status_message('Project file not found.')

    def on_post_save(self, view):
        settings = sublime.active_window().active_view().settings()
        if( settings.get('scan_php_classes') != True ):
            return

        utils = _projectPHPClassUtils(None)
        folders = utils.get_project_folders(view)
        threads = []
        thread = ProjectPHPClassCompletionsScan(folders, 5)
        threads.append(thread)
        thread.start()

    def on_query_completions(self, view, prefix, locations):
        if not view.match_selector(locations[0], "source.php"):
            return []
        if (self.get_enable_completitions() != True):
            return []
        path = view.file_name()
        completions_location = None
        if path:
            utils = _projectPHPClassUtils( None )
            # Try to find the phpclass.sublime-classdb file
            for filename in ['phpclass.sublime-classdb']:
                completions_location = utils.find_file(path, filename)
        if completions_location:
            data = []
            utils = _projectPHPClassUtils( os.path.dirname(completions_location) )
            with codecs.open(utils.get_db_path(), 'r', encoding='utf-8', errors='ignore') as cfp:
                line = cfp.readline()
                while len(line) != 0:
                    try:
                        t = ()
                        filepath,linedef,cname,cmethod,cargs,cvisibility,ccontext = line.split(";")
                        if re.match(prefix, cmethod, re.IGNORECASE):
                            trigger = cmethod+'\t'+cname
                            contents = cmethod+re.sub('\$', '\\\$', cargs)
                            t = trigger, contents
                            data.append(t)
                    except:
                        # print "errors with line: %s" % (line,)
                        pass
                    line = cfp.readline()
            return data
            # return (data,sublime.INHIBIT_EXPLICIT_COMPLETIONS)
        else:
            return []

    def get_enable_completitions(self):
        settings = sublime.load_settings('ProjectPHPClassBrowser.sublime-settings')
        enable_completitions = settings.get('enable_completitions') or False
        if( isinstance(enable_completitions, bool) ):
            return enable_completitions
        return False
