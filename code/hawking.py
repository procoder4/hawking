import importlib
import inspect
import sys
import os
import time
from collections import OrderedDict

import discord
from discord.ext import commands

import utilities
import speech
import admin
import message_parser
import help_formatter
import dynamo_helper

if not discord.opus.is_loaded():
    # the 'opus' library here is opus.dll on windows
    # or libopus.so on linux in the current directory
    # you should replace this with the location the
    # opus library is located in and with the proper filename.
    # note that on windows this DLL is automatically provided for you
    discord.opus.load_opus('opus')

## Config
CONFIG_OPTIONS = utilities.load_config()


class ModuleEntry:
    def __init__(self, cls, is_cog, *init_args, **init_kwargs):
        self.module = sys.modules[cls.__module__]
        self.cls = cls
        self.name = cls.__name__
        self.is_cog = is_cog
        self.args = init_args
        self.kwargs = init_kwargs

    ## Methods

    ## Returns an invokable object to instantiate the class defined in self.cls
    def get_class_callable(self):
        return getattr(self.module, self.name)


class ModuleManager:
    ## Keys
    MODULES_FOLDER_KEY = "modules_folder"

    def __init__(self, hawking, bot):
        self.modules_folder = CONFIG_OPTIONS.get(self.MODULES_FOLDER_KEY, "")

        self.hawking = hawking
        self.bot = bot
        self.modules = OrderedDict()

    ## Methods

    ## Registers a module, class, and args necessary to instantiate the class
    def register(self, cls, is_cog=True, *init_args, **init_kwargs):
        if(not inspect.isclass(cls)):
            raise RuntimeError("Provided class parameter '{}' isn't actually a class.".format(cls))

        if(not init_args):
            init_args = [self.hawking, self.bot]

        module_entry = ModuleEntry(cls, is_cog, *init_args, **init_kwargs)
        self.modules[module_entry.name] = module_entry

        ## Add the module to the bot (if it's a cog), provided it hasn't already been added.
        if(not self.bot.get_cog(module_entry.name) and module_entry.is_cog):
            cog_cls = module_entry.get_class_callable()
            self.bot.add_cog(cog_cls(*module_entry.args, **module_entry.kwargs))


    ## Finds and registers modules inside the modules folder
    def discover(self):
        ## Assumes that the modules folder is inside the root
        modules_folder_path = os.path.abspath(os.path.sep.join(["..", self.modules_folder]))
        ## Expose the modules folder to the interpreter, so modules can be loaded
        sys.path.append(modules_folder_path)

        ## Build a list of potential module paths and iterate through it...
        candidate_modules = os.listdir(modules_folder_path)
        for candidate in candidate_modules:
            ## If the file could be a python file...
            if(candidate[-3:] == ".py"):
                name = candidate[:-3]

                ## Attempt to import the module (akin to 'import [name]') and register it normally
                ## NOTE: Modules MUST have a 'main()' function that essentially returns a list containing all the args
                ##       needed by the 'register()' method of this ModuleManager class. At a minimum this list MUST
                ##       contain a reference to the class that serves as an entry point to the module. You should also
                ##       specify whether or not a given module is a cog (for discord.py) or not.
                try:
                    module = importlib.import_module(name)
                    declarations = module.main()

                    ## Validate the shape of the main() method's data, and attempt to tolerate poor formatting
                    if(not isinstance(declarations, list)):
                        declarations = [declarations]
                    elif(len(declarations) == 0):
                        raise RuntimeError("Module '{}' main() returned empty list. Needs a class object at minimum.".format(module.__name__))

                    self.register(*declarations)
                except Exception as e:
                    del module


    ## Reimport a single module
    def _reimport_module(self, module):
        try:
            importlib.reload(module)
        except Exception as e:
            print("Error: ({}) reloading module: {}".format(e, module))
            return False
        else:
            return True


    ## Reloads a module with the provided name
    def _reload_module(self, module_name):
        module_entry = self.modules.get(module_name)
        assert module_entry is not None

        self._reimport_module(module_entry.module)


    ## Reload a cog attached to the bot
    def _reload_cog(self, cog_name):
        module_entry = self.modules.get(cog_name)
        assert module_entry is not None

        self.bot.remove_cog(cog_name)
        self._reimport_module(module_entry.module)
        cog_cls = module_entry.get_class_callable()
        self.bot.add_cog(cog_cls(*module_entry.args, **module_entry.kwargs))


    ## Reload all of the registered modules
    def reload_all(self):
        counter = 0
        for module_name in self.modules:
            try:
                if(self.modules[module_name].is_cog):
                    self._reload_cog(module_name)
                else:
                    self._reload_module(module_name)
            except Exception as e:
                print("Error: {} when reloading cog: {}".format(e, module_name))
            else:
                counter += 1

        print("Loaded {}/{} cogs.".format(counter, len(self.modules)))
        return counter


class Hawking:
    ## Keys and Defaults
    ## Basically, any given class can be configured by changing the respective value for the
    ## desired key in config.json (see the Keys section at the top of each class for a list of
    ## keys). However, if you want to use Hawking as a part of something else, you may want to
    ## dynamically configure objects as necessary. Thus, you can also instantiate classes with
    ## keyworded arguments, which will then override any existing defaults, or config.json data.
    ## The existing defaults in each class are sort of like a fallback, in case the config.json is
    ## broken in some way.

    ## Keys
    VERSION_KEY = "version"
    ACTIVATION_STR_KEY = "activation_str"
    DESCRIPTION_KEY = "description"
    TOKEN_KEY = "token"
    TOKEN_FILE_KEY = "token_file"
    TOKEN_FILE_PATH_KEY = "token_file_path"

    ## Defaults
    VERSION = CONFIG_OPTIONS.get(VERSION_KEY, "Invalid version")
    ACTIVATION_STR = CONFIG_OPTIONS.get(ACTIVATION_STR_KEY, "\\")
    DESCRIPTION = CONFIG_OPTIONS.get(DESCRIPTION_KEY, "A retro TTS bot for Discord (Alpha)\n Visit https://github.com/naschorr/hawking")
    TOKEN_FILE = CONFIG_OPTIONS.get(TOKEN_FILE_KEY, "token.json")
    TOKEN_FILE_PATH = CONFIG_OPTIONS.get(TOKEN_FILE_PATH_KEY, os.sep.join([utilities.get_root_path(), TOKEN_FILE]))


    ## Initialize the bot, and add base cogs
    def __init__(self, **kwargs):
        self.activation_str = kwargs.get(self.ACTIVATION_STR_KEY, self.ACTIVATION_STR)
        self.description = kwargs.get(self.DESCRIPTION_KEY, self.DESCRIPTION)
        self.token_file_path = kwargs.get(self.TOKEN_FILE_PATH_KEY, self.TOKEN_FILE_PATH)
        self.dynamo_db = dynamo_helper.DynamoHelper()
        ## Todo: pass kwargs to the their modules

        ## Init the bot and module manager
        self.bot = commands.Bot(
            command_prefix=commands.when_mentioned_or(self.activation_str),
            formatter=help_formatter.HawkingHelpFormatter(),
            description=self.description
        )
        self.module_manager = ModuleManager(self, self.bot)

        ## Register the modules (Order of registration is important, make sure dependancies are loaded first)
        self.module_manager.register(message_parser.MessageParser, False)
        self.module_manager.register(speech.Speech, True, self.bot)
        self.module_manager.register(admin.Admin, True, self, self.bot)

        ## Load any dynamic modules inside the /modules folder
        self.module_manager.discover()

        ## Give some feedback for when the bot is ready to go, and provide some help text via the 'playing' status
        @self.bot.event
        async def on_ready():
            bot_status = discord.Game(type=0, name="Use {}help".format(self.activation_str))
            await self.bot.change_presence(game=bot_status)
            print("Logged in as '{}' (version: {}), (id: {})".format(self.bot.user.name, self.VERSION, self.bot.user.id))

        ## Give some feedback to users when their command doesn't execute.
        @self.bot.event
        async def on_command_error(exception, ctx):
            # discord.py uses reflection to set the destination chat channel for whatever reason (sans command ctx)
            _internal_channel = ctx.message.channel

            self.dynamo_db.put(dynamo_helper.DynamoItem(
                ctx, ctx.message.content, inspect.currentframe().f_code.co_name, False, str(exception)))

            ## Poorly handled (for now, until I can get more concrete examples in my database) error messages for users
            if ("code =" in str(exception)):
                await self.bot.say("Sorry <@{}>, Discord is having some issues that won't let me speak right now.")
                return
            ## Generic, command couldn't be completed alert for users
            else:
                await self.bot.say("Sorry <@{}>, **{}{}** isn't a valid command. Try the **{}help** page."
                    .format(ctx.message.author.id, ctx.prefix, ctx.invoked_with, self.activation_str))
                return

    ## Methods

    ## Add an arbitary cog to the bot
    def add_cog(self, cls):
        self.bot.add_cog(cls)


    ## Returns a cog with a given name
    def get_cog(self, cls_name):
        return self.bot.get_cog(cls_name)


    ## Returns the bot's speech cog
    def get_speech_cog(self):
        return self.bot.get_cog("Speech")


    ## Returns the bot's phrases cog
    def get_phrases_cog(self):
        return self.bot.get_cog("Phrases")


    ## Returns the bot's music cog
    def get_music_cog(self):
        return self.bot.get_cog("Music")


    ## Register an arbitrary module with hawking (easy wrapper for self.module_manager.register)
    def register_module(self, cls, is_cog, *init_args, **init_kwargs):
        self.module_manager.register(cls, is_cog, *init_args, **init_kwargs)


    ## Run the bot
    def run(self):
        ## Keep bot going despite any misc service errors
        try:
            self.bot.run(utilities.load_json(self.token_file_path)[self.TOKEN_KEY])
        except RuntimeError as e:
            utilities.debug_print("Critical Runtime Error when running bot:", e, debug_level=0)
        except Exception as e:
            utilities.debug_print("Critical exception when running bot:", e, debug_level=0)
            time.sleep(1)
            self.run()


if(__name__ == "__main__"):
    hawking = Hawking()
    # hawking.register_module(ArbitraryClass(*init_args, **init)kwargs))
    # or,
    # hawking.add_cog(ArbitaryClass(*args, **kwargs))
    hawking.run()
