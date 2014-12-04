import os, fnmatch, re, threading, sublime, sublime_plugin, sys, codecs, subprocess

class _projectPHPClassUtils:
    def __init__(self, rootPath):
        self.rootPath = rootPath
        self.dbFilename = 'phpclass.sublime-classdb'

    def get_db_classnames(self):
        data = []

        compPath = os.path.join( self.rootPath , self.dbFilename )
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

        compPath = os.path.join( self.rootPath , self.dbFilename )
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

                data[cname.strip()]['methods'].append( {
                    'name': cmethod,
                    'args': cargs,
                    'definition': ' '.join([cvisibility.strip(),ccontext.strip()]).strip() +' '+cmethod.strip()+cargs.strip(),
                    'line': methodline
                } )
            except:
              # print "errors with line: %s" % (line,)
              pass
            line = cfp.readline()

        return data

    def dbPresent(self):
        compPath = os.path.join( self.rootPath , self.dbFilename )
        return os.path.isfile(compPath)

    def is_browser_view(self, view):
        if(view.is_scratch() == True and view.name() == 'PHP Class Browser'):
            return True
        return False

    def find_browser_view(self):
        window = sublime.active_window()
        for view in window.views():
            if(self.is_browser_view(view)):
                return view

        return None

    def is_updating_view(self, view):
        if(view.is_scratch() == True and view.name() == 'Please wait.'):
            return True
        return False

    def find_updating_view(self):
        window = sublime.active_window()
        for view in window.views():
            if(self.is_updating_view(view)):
                return view

        return None



class ProjectPHPClassCompletionsScan(threading.Thread):

    def __init__(self, rootPath, timeout):
        threading.Thread.__init__(self)
        self.rootPath = rootPath
        self.timeout = timeout
        self.result = None

    def get_php_executable(self):
        settings = sublime.load_settings('ProjectPHPClassBrowser.sublime-settings')
        return settings.get('php_executable') or 'php'

    def run(self):
        try:
            compPath = os.path.join( os.path.dirname(self.rootPath), 'phpclass.sublime-classdb' )
            with open(compPath, 'w') as cfp:
              cfp.close()

            with open(compPath, 'a') as cfp:
              patterns = ['.inc', '.php']
              for root, dirs, files in os.walk(os.path.dirname(self.rootPath)):
                  for p in patterns:
                      for f in files:
                          if f.endswith(p):
                              #parse the file and save class methods
                              filepath = os.path.join(root, f)
                              parser = os.path.join( sublime.packages_path() , 'Project PHP ClassBrowser', 'parse_file.php' )
                              pipe = subprocess.Popen([self.get_php_executable(), parser, filepath], stdout=cfp, stderr=cfp)
                              out, err = pipe.communicate()

            # try to update browser window
            window = sublime.active_window()
            utils = _projectPHPClassUtils(os.path.dirname(self.rootPath))
            browser_view = utils.find_browser_view()
            if(browser_view != None):
              browser_view.run_command("refresh_browser_view", {"rootPath": os.path.dirname(self.rootPath) } )

            return
        except:
            exc = sys.exc_info()[1]
            sublime.status_message(str(exc))
            raise

class OpenUpdatingCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    view = self.view
    view.set_read_only(False)
    view.set_scratch(True)
    view.set_name('Please wait.')
    view.insert(edit, view.size(),'Updating list... ')
    view.set_read_only(True)

class ProjectPhpclassOpenLayoutCommand(sublime_plugin.WindowCommand):
    def run(self):
        window = sublime.active_window();
        utils = _projectPHPClassUtils(window.folders()[0])
        if( utils.dbPresent() != True ):
            sublime.status_message('No DataBase Found!')
            return

        browser_view = utils.find_browser_view()
        if( browser_view != None ):
            browser_view.run_command("refresh_browser_view", {"rootPath": window.folders()[0] } )
            return

        oldlayout = window.get_layout();
        settings = sublime.load_settings('phpclass_browser.sublime-settings')
        settings.set('php_class_browser_revert_layout',oldlayout);
        sublime.save_settings('phpclass_browser.settings')

        window.set_layout({
            "cols": [0.0, 1.0],
            "rows": [0, 0.75, 1],
            "cells": [[0, 0, 1, 1], [0, 1, 1, 2]]
        })
        window.focus_group(1)
        view = window.new_file()
        view.run_command("refresh_browser_view", {"rootPath": window.folders()[0] } )

class ProjectPhpclassCloseLayoutCommand(sublime_plugin.WindowCommand):
    def run(self):
        window = sublime.active_window();

        settings = sublime.load_settings('phpclass_browser.sublime-settings')
        oldlayout = settings.get('php_class_browser_revert_layout');

        if( oldlayout != None ):
            window.set_layout(oldlayout)
        else:
            window.set_layout({
                "cols": [0.0, 1.0],
                "rows": [0, 1],
                "cells": [[0, 0, 1, 1]]
            })

        utils = _projectPHPClassUtils(window.folders()[0])

        updating_view = utils.find_updating_view()
        if( updating_view != None ):
            window.focus_view(updating_view)
            window.run_command('close')

        browser_view = utils.find_browser_view()
        if( browser_view != None ):
            window.focus_view(browser_view)
            window.run_command('close')

        window.focus_group(0)

class FillBrowserViewCommand(sublime_plugin.TextCommand):
  def run(self, edit, rootPath):

    view = self.view
    window = sublime.active_window()

    # remove view content if present
    viewcontent = sublime.Region(0,view.size())
    view.erase(edit,viewcontent)

    if rootPath:
      utils = _projectPHPClassUtils(rootPath)
    else:
      utils = _projectPHPClassUtils(window.folders()[0])

    regions = []
    foldregions = []
    numregions = 0;

    classnames = utils.get_db_classnames()

    if( self.get_classnames_order() == 'alpha' ):
        classnames = sorted(classnames)

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

    view.insert(edit, view.size(),'\n')
    view.add_regions('classbrowser' , regions, 'classbrowser', 'bookmark',sublime.DRAW_OUTLINED)
    view.add_regions('classbrowserfoldregions' , foldregions, 'classbrowserfoldregions', 'fold', sublime.HIDDEN)
    view.fold(foldregions)
    view.end_edit(edit)
    view.set_read_only(True)

    updatingview = utils.find_updating_view()
    if(updatingview != None):
      window.focus_view(updatingview)
      window.run_command('close')

  def get_classnames_order(self):
      settings = sublime.load_settings('ProjectPHPClassBrowser.sublime-settings')
      order = settings.get('class_order') or 'alpha'
      if( order != 'alpha' and order != 'definition'):
          order = 'alpha'
      return order

class RefreshBrowserViewCommand(sublime_plugin.TextCommand):
    def run(self, edit, rootPath):
        window = sublime.active_window()

        if rootPath:
          utils = _projectPHPClassUtils(rootPath)
        else:
          utils = _projectPHPClassUtils(window.folders()[0])
          rootPath = window.folders()[0]

        if( utils.dbPresent() != True ):
            sublime.status_message('No DataBase Found!')
            return

        view = self.view
        view.set_scratch(True)
        view.set_name('PHP Class Browser')
        view.set_read_only(False)

        # remove view content if present
        viewcontent = sublime.Region(0,view.size())
        view.erase(edit,viewcontent)

        updatingview = window.new_file()
        updatingview.run_command("open_updating")

        #sublime.set_timeout(lambda view=view, rootPath=rootPath: view.run_command("fill_browser_view", {"rootPath": rootPath } ), 1000)
        #view.run_command("fill_browser_view", {"rootPath": rootPath })

        thread = ProjectPHPClassBrowserFiller(view, rootPath)
        thread.start()

class ProjectPHPClassBrowserFiller(threading.Thread):
    def __init__(self, view, rootPath):
        threading.Thread.__init__(self)
        self.view = view
        self.rootPath = rootPath

    def run(self):
      self.view.run_command("fill_browser_view", { "rootPath" : self.rootPath })

class ClickPhpclassBrowser(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        window = sublime.active_window()
        utils = _projectPHPClassUtils(window.folders()[0])
        if( utils.is_browser_view(view) != True ):
            return;

        window.focus_view(view)

        point = view.sel()[0]
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
                if(line.startswith('\t') == False  and not re.match('\s+', line, re.IGNORECASE) ):
                    classname = line
        else:
            classname = word

        classname = classname.split('\n')[0].strip()
        if(len(classname)>0):
            try:
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
            except:
                sublime.status_message('Unknown Class Name: '+str(classname))

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
        window = sublime.active_window()
        utils = _projectPHPClassUtils(None)
        if( utils.is_browser_view(view) != True ):
            return

        path = view.file_name()
        rootPath = None

        if path:
            # Try to find the myproject.sublime-project file
            for filename in ['*.sublime-project']:
                rootPath = self.find_file(path, filename)

        view.run_command("refresh_browser_view", {"rootPath": rootPath } )

    def on_post_save(self, view):
        settings = sublime.active_window().active_view().settings()
        if( settings.get('scan_php_classes') != True ):
          return

        path = view.file_name()
        rootPath = None

        if path:
            # Try to find the myproject.sublime-project file
            for filename in ['*.sublime-project']:
                rootPath = self.find_file(path, filename)
        if rootPath:
            threads = []
            thread = ProjectPHPClassCompletionsScan(rootPath, 5)
            threads.append(thread)
            thread.start()

    def on_query_completions(self, view, prefix, locations):
        if not view.match_selector(locations[0], "source.php"):
            return []

        path = view.file_name()
        completions_location = None
        if path:
            # Try to find the phpclass.sublime-classdb file
            for filename in ['phpclass.sublime-classdb']:
                completions_location = self.find_file(path, filename)
        if completions_location:
            data = []
            utils = _projectPHPClassUtils(os.path.dirname(completions_location))
            for classname in utils.get_db_classnames():
              classes = utils.get_db_data(classname)

              t = ()
              for k in sorted(classes.keys()):
                classdef = classes[k]
                for methoddef in classdef.get('methods'):
                  if re.match(prefix, methoddef.get('name'), re.IGNORECASE):
                    trigger = methoddef.get('name')+'\t'+classdef.get('name')
                    contents = methoddef.get('name')+re.sub('\$', '\\\$', methoddef.get('args'))
                    t = trigger, contents
                    data.append(t)

            return data
            # return (data,sublime.INHIBIT_EXPLICIT_COMPLETIONS)
        else:
            return []

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
