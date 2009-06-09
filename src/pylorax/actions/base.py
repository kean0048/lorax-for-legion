# pylorax/actions/base.py

import os
import re

from pylorax.utils.fileutils import cp, mv, touch, edit, replace


# command:action mapping
# maps a template command to an action class
# if you want your new action to be supported, you have to include it in this mapping
COMMANDS = { 'copy': 'Copy',
             'move': 'Move',
             'link': 'Link',
             'touch': 'Touch',
             'edit': 'Edit',
             'replace': 'Replace',
             'makedir': 'MakeDir' }


class LoraxAction(object):
    """Actions base class.

    To create your own custom action, subclass this class and override the methods you need.

    A valid action has to have a REGEX class variable, which specifies the format of the action
    command line, so the needed parameters can be properly extracted from it.
    All the work should be done in the execute method, which will be called from Lorax.
    At the end, set the success to False, or True depending on the success or failure of your action.

    If you need to install some package prior to executing the action, return an install pattern
    with the "install" property. Lorax will get this first, and will try to install the needed
    package.

    Don't forget to include a command:action map for your new action in the COMMANDS dictionary.
    Action classes which are not in the COMMANDS dictionary will not be loaded.
    
    You can take a look at some of the builtin actions to get an idea of how to create your
    own actions."""


    REGEX = r'' # regular expression for extracting the parameters from the command line

    def __init__(self):
        if self.__class__ is LoraxAction:
            raise TypeError, 'LoraxAction is an abstract class, cannot be used this way'

        self._attrs = {}
        self._attrs['success'] = None   # success is None, if the action wasn't executed yet

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self._attrs)

    def execute(self, verbose=False):
        """This method is the main body of the action. Put all the "work" stuff in here."""
        raise NotImplementedError, 'execute method not implemented for LoraxAction class'

    @property
    def success(self):
        """Returns if the action's execution was successful or not."""
        return self._attrs['success']

    @property
    def install(self):
        """Returns a pattern that needs to be installed, prior to calling the execute method."""
        return None

    @property
    def getDeps(self):
        # FIXME hmmm, how can i do this more generic?
        return None


##### builtin actions

class Copy(LoraxAction):

    REGEX = r'^(?P<src>.*?)\sto\s(?P<dst>.*?)(\smode\s(?P<mode>.*?))?$'

    def __init__(self, **kwargs):
        LoraxAction.__init__(self)
        self._attrs['src'] = kwargs.get('src')
        self._attrs['dst'] = kwargs.get('dst')
        self._attrs['mode'] = kwargs.get('mode')

    def execute(self, verbose=False):
        cp(src=self.src, dst=self.dst, mode=self.mode, verbose=verbose)
        self._attrs['success'] = True

    @property
    def src(self):
        return self._attrs['src']

    @property
    def dst(self):
        return self._attrs['dst']

    @property
    def mode(self):
        return self._attrs['mode']

    @property
    def install(self):
        return self._attrs['src']

    @property
    def getDeps(self):
        return self._attrs['src']


class Move(Copy):
    def execute(self, verbose=False):
        mv(src=self.src, dst=self.dst, mode=self.mode, verbose=verbose)
        self._attrs['success'] = True


class Link(LoraxAction):

    REGEX = r'^(?P<name>.*?)\sto\s(?P<target>.*?)$'

    def __init__(self, **kwargs):
        LoraxAction.__init__(self)
        self._attrs['name'] = kwargs.get('name')
        self._attrs['target'] = kwargs.get('target')

    def execute(self, verbose=False):
        os.symlink(self.target, self.name)
        self._attrs['success'] = True

    @property
    def name(self):
        return self._attrs['name']

    @property
    def target(self):
        return self._attrs['target']

    @property
    def install(self):
        return self._attrs['target']


class Touch(LoraxAction):

    REGEX = r'^(?P<filename>.*?)$'

    def __init__(self, **kwargs):
        LoraxAction.__init__(self)
        self._attrs['filename'] = kwargs.get('filename')

    def execute(self, verbose=False):
        touch(filename=self.filename, verbose=verbose)
        self._attrs['success'] = True

    @property
    def filename(self):
        return self._attrs['filename']


class Edit(Touch):

    REGEX = r'^(?P<filename>.*?)\stext\s"(?P<text>.*?)"((?P<append>\sappend?))?$'

    def __init__(self, **kwargs):
        Touch.__init__(self, **kwargs)
        self._attrs['text'] = kwargs.get('text')
        
        append = kwargs.get('append', False)
        if append:
            self._attrs['append'] = True
        else:
            self._attrs['append'] = False

    def execute(self, verbose=False):
        edit(filename=self.filename, text=self.text, append=self.append, verbose=verbose)
        self._attrs['success'] = True

    @property
    def text(self):
        return self._attrs['text']

    @property
    def append(self):
        return self._attrs['append']

    @property
    def install(self):
        return self._attrs['filename']


class Replace(Touch):

    REGEX = r'^(?P<filename>.*?)\sfind\s"(?P<find>.*?)"\sreplace\s"(?P<replace>.*?)"$'

    def __init__(self, **kwargs):
        Touch.__init__(self, **kwargs)
        self._attrs['find'] = kwargs.get('find')
        self._attrs['replace'] = kwargs.get('replace')

    def execute(self, verbose=False):
        replace(filename=self.filename, find=self.find, replace=self.replace, verbose=verbose)
        self._attrs['success'] = True

    @property
    def find(self):
        return self._attrs['find']

    @property
    def replace(self):
        return self._attrs['replace']

    @property
    def install(self):
        return self._attrs['filename']


class MakeDir(LoraxAction):

    REGEX = r'^(?P<dir>.*?)(\smode\s(?P<mode>.*?))?$'

    def __init__(self, **kwargs):
        LoraxAction.__init__(self)
        self._attrs['dir'] = kwargs.get('dir')
        self._attrs['mode'] = kwargs.get('mode')

    def execute(self, verbose=False):
        if not os.path.isdir(self.dir):
            if self.mode:
                os.makedirs(self.dir, mode=int(self.mode))
            else:
                os.makedirs(self.dir)
        self._attrs['success'] = True

    @property
    def dir(self):
        return self._attrs['dir']

    @property
    def mode(self):
        return self._attrs['mode']
