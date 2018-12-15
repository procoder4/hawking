# hawking
A retro text-to-speech interface bot for Discord, designed to work with all of the stuff you might've seen in Moonbase Alpha, using the existing commands.

## Activation
- Go to [this page](https://discordapp.com/oauth2/authorize?client_id=334894709292007424&scope=bot&permissions=53803072) on Discord's site.
- Select the server that you want Hawking to be added to.
- Hit the "Authorize" button.
- Start speaking! (you should check out the [**Commands**](https://github.com/naschorr/hawking#commands) section of this readme, too!)

## To Do
- [ ] Clean up config.json, and remove some ultimately unnecessary code
- [x] Improve the help interface by visually isolating phrase sections, and giving the music interface help text that's actually convenient to review
- [x] Give the bot some sort of sign-off message when he leaves a channel due to inactivity? Right now it just sounds like a regular person left
- [ ] Better, more up to date analytics (Who's using the bot right now? Is a specific server/channel abusing my poor EC2 instance?)
- [ ] Live, per server configuration done by server owners
- [ ] (Potentially) Have the bot delete it's own (less useful) messages after a period of time?
- [ ] Clean up class level configuration, theres too much redundancy
- [x] Dynamic module loading? Just drop (properly formatted) modules into a folder and the bot will handle loading?
- [ ] Proper testing suite
- [x] Run it as a system service (systemd for now)
- [ ] Installation script (pip instead?)

## Installation
- Make sure you've got [Python 3.6](https://www.python.org/downloads/) or greater installed, and support for virtual environments (This assumes that you're on Python 3.6 with `venv` support, but older versions with `virtualenv` and `pyvenv` should also work.)
- `cd` into the directory that you'd like the project to go (If you're on Linux, I'd recommend '/usr/local/bin')
- `git clone https://github.com/naschorr/hawking`
- `python3 -m venv hawing/`
    + You may need to run: `apt install python3-venv` to enable virtual environments for Python 3 on Linux
- Activate your newly created venv
- `pip install -r requirements.txt`
    + If you run into issues during PyNaCl's installation, you may need to run: `apt install build-essential libffi-dev python3.5-dev` to install some supplemental features for the setup process.
- Make sure the [FFmpeg executable](https://www.ffmpeg.org/download.html) is in your system's `PATH` variable
- Create a [Discord app](https://discordapp.com/developers/applications/me), flag it as a bot, and put the bot token inside `hawking/token.json`
- Register the Bot with your server. Go to: `https://discordapp.com/oauth2/authorize?client_id=CLIENT_ID&scope=bot&permissions=53803072`, but make sure to replace CLIENT_ID with your bot's client id.
- Select your server, and hit "Authorize"
- Check out `config.json` for any configuration you might want to do. It's set up to work well out of the box, but you may want to add admins, change pathing, or modify the number of votes required for a skip.

#### Windows Installation
- Nothing else to do! Everything should work just fine.

#### Linux Installation
Running Hawking on Linux requires a bit more work. At a minimum you'll need some sort of way to get Windows applications running on Linux. However, if you plan to run Hawking in a server environment (and you probably do), you should also check out the [Server Installation](https://github.com/naschorr/hawking#server-installation) section below.

##### Basic Installation
- Install [Wine](https://www.winehq.org/) to get the text-to-speech executable working.
    + `dpkg --add-architecture i386`
    + `apt-get update`
    + `apt-get install wine`

##### Server Installation
- Get Hawking set up with Xvfb
    + Install Xvfb with with your preferred package manager (`apt install xvfb` on Ubuntu, for example)
    + Invoke Xvfb automatically on reboot with a cron job (`sudo crontab -e`), by adding `@reboot Xvfb :0 -screen 0 1024x768x16 &` to your list of jobs.
    + Set `headless` to be `true` in `config.json`
    + If you're using different virtual server or screen identifiers, then make sure they work with `xvfb_prepend` in `config.json`. Otherwise everything should work fine out of the box.

- Hawking as a Service (HaaS)
    > *Note:* This assumes that your system uses systemd. You can check that by running `pidof systemd && echo "systemd" || echo "other"` in the terminal. If your system is using sysvinit, then you can just as easily build a cron job to handle running `hawking.py` on reboot. Just make sure to use your virtual environment's Python executable, and not the system's one.

    - Assuming that your installation is in '/usr/local/bin/hawking', you'll want to move the `hawking.service` file into the systemd services folder with `mv hawking.service /etc/systemd/system/`
        + If your hawking installation is located elsewhere, just update the paths (`ExecStart` and `WorkingDirectory`) inside the `hawking.service` to point to your installation.
    - Get the service working with `sudo systemctl daemon-reload && systemctl enable hawking && systemctl start hawking --no-block`
    - Now you can control the Hawking service just like any other. For example, to restart: `sudo service hawking restart`

## Usage
- `cd` into the project's root
- Activate the venv
- `cd` into `hawking/code/` (Note, you need `hawking.py` to be in your current working directory, as theres some weird pathing issues with the required files for `say.exe`
- `python hawking.py`

## Commands
These commands allow for the basic operation of the bot, by anyone.
- `\say [text]` - Tells the bot to speak [text] in the voice channel that you're currently in.
- `\skip` - Skip a phrase that you've requested, or start a vote to skip on someone else's phrase.
- `\music [options] [notes]` - Sings the [notes] aloud. See music.py's music() command docstring for more info about music structure. Currently rewriting to be even more flexible.
- `\summon` - Summons the bot to join your voice channel.
- `\help` - Show the help screen.

## Admin Commands
Admin commands allow for some users to have a little more control over the bot. For these to work, the `admin` array in `config.json` needs to have the desired usernames added to it. Usernames should be in the `Username#1234` format that Discord uses.
- `\admin skip` - Skip whatever's being spoken at the moment, regardless of who requested it.
- `\admin reload_phrases` - Unloads, and then reloads the preset phrases (found in `phrases.json`). This is handy for quickly adding new presets on the fly.
- `\admin reload_cogs` - Unloads, and then reloads the cogs registered to the bot (see admin.py's register_module() method). Useful for debugging.
- `\admin disconnect` - Forces the bot to stop speaking, and disconnect from its current channel in the invoker's server.
- `\help admin` - Show the help screen for the admin commands.


## Configuration `config.json`

#### Discord Configuration
- **version** - String - The bot's current semantic version.
- **admins** - Array - Array of Discord usernames who have access to `\admin` commands. Uses `Username#1234` format.
- **activation_str** - String - The string that'll activate the Discord bot from chat messages.
- **description** - String - The bot's description. This is seen in the help interface.
- **announce_updates** - Boolean - Choose whether or not the bot will announce status updates to the invoker's voice channel. Things like 'Loaded N phrases.' after invoking `\admin reload_phrases`.
- **delete_commands** - Boolean - Choose to delete the command that invoked the bot. This lets users operate the bot 'silently'. Requires that the bot role's `Manage Messages` permission is enabled, and that the bot can also 'Manage Messages' in the text chat channel.
- **channel_timeout** - Int - The time in seconds before the bot will leave its current voice channel due to inactivity.
- **channel_timeout_phrases** - Array - Array of strings that the bot can speak right before it leaves. One phrase is chosen randomly from the array.
- **skip_votes** - Int - The minimum number of votes needed by a channel to skip the currently playing speech.
- **skip_percentage** - Int - The minimum percentage of other users who need to request a skip before the currently playing speech will be skipped.

#### Bot Configuration
- **debug_level** - Int - The maximum threshold for printing debug statements to the terminal. Debug statements with a level of `0` are the most important, while statements with a level of `4` are the least important. See `debug_print()` in `utilities.py`.
- **token_file** - String - The name of the file containing the bot's Discord token.
- **\_token_file_path** - String - Force the bot to use a specific token, rather than the normal `token.json` file. Remove the leading underscore to activate it.
- **phrases_file_extension** - String - The file extension to look for when searching for phrase files.
- **phrases_folder** - String - The name of the folder that contains phrase files.
- **\_phrases_folder_path** - String - Force the bot to use a specific phrases folder, rather than the normal `phrases/` folder. Remove the leading underscore to activate it.
- **tts_file** - String - The name of the text-to-speech executable.
- **\_tts_file_path** - String - Force the bot to use a specific text-to-speech executable, rather than the normal `say.exe` file. Remove the leading underscore to activate it.
- **tts_output_dir** - String - The name of the file where the temporary speech files are stored.
- **\_tts_output_dir_path** - String - Force the bot to use a specific text-to-speech output folder, rather than the normal `temp/` folder. Remove the leading underscore to activate it.
- **ffmpeg_before_options** - String - Options to send to the FFmpeg executable before the `-i` flag.
- **ffmpeg_options** - String - Options to send to the FFmpeg executable after the `-i` flag.
- **output_extension** - String - The file extension of the text-to-speech engine's output.
- **wine** - String - The command to invoke Wine on your system. Linux only.
- **xvfb_prepend** - String - The string that'll select your `xvfb` display. Headless only.
- **headless** - Boolean - Indicate that the bot is running on a machine without a display. Uses `xvfb` to simulate a display required for the text-to-speech engine.

#### Speech Configuration
- **prepend** - String - A string that'll always be prepended onto the text sent to the text-to-speech engine.
- **append** - String - A string that'll always be appended onto the text sent to the text-to-speech engine.
- **char_limit** - Int - A hard character limit for messages to be sent to the text-to-speech engine.
- **newline_replacement** - String - A string that'll replace all newline characters in the text sent to the text-to-speech engine.
- **replace_emoji** - Boolean - If `true`, indicates that the bot should convert emoji into their textual form (ex. :thinking: -> "thinking face"). This isn't a perfect conversion, as Discord encodes emoji into their unicode representation before the bot is able to parse it. If this is set to `false`, then the bot will just strip out emoji completely, as if they weren't there.

#### Music Configuration
- **bpm** - Int - The default bpm for `\music` commands.
- **octave** - Int - The default octave for `\music` commands.
- **tone** - Boolean - Choose to use pure tones for musical notes instead of a simulated voice singing the notes.
- **bad** - Boolean - Choose to make all `\music` commands comically worse. Think Cher's 'My Heart Will Go On' on the recorder.
- **bad_percent** - Int - The percentage that the `bad` command makes music worse by.

#### Analytics Configuration
- **boto_enable** - Boolean - Indicate that you want the bot to upload analytics to an Amazon AWS resource.
- **boto_resource** - String - The AWS boto-friendly resource to upload to. (I've only tried DynamoDB, but I'm fairly sure AWS' other storage resources would work if you wanted to tweak the code).
- **boto_region_name** - String - The AWS region of your chosen boto_resource.
- **boto_table_name** - String - The name of the table to insert into.
- **boto_primary_key** - String - The primary key of your chosen table.

## Lastly...
Also included are some built-in phrases from [this masterpiece](https://www.youtube.com/watch?v=1B488z1MmaA). Check out the `Phrases` section in the `\help` screen. You should also take a look at my dedicated [hawking-phrases repository](https://github.com/naschorr/hawking-phrases). It's got a bunch of phrase files that can easily be put into your phrases folder for even more customization.

Lastly, be sure to check out the [Moonbase Alpha](https://steamcommunity.com/sharedfiles/filedetails/?id=482628855) moon tunes guide on Steam.

Tested on Windows 10, and Ubuntu 16.04.
