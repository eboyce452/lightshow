### This is lightshow.py V3, a script with the pyrfirmata library to control an arduino running the firmata library
### The code uses the Spotify API to call the ID of the track that is playing on the current user's Spotify account, then uses the same API to get the tempo (aka BPM)
### It then takes that information and uses it to drive a series of RBG lightstrips in combination with IRLB8721 MOSFET N-Channel Transistors arranged into AND gates. (I don't know if calling it charlieplexing is too generous or not) I'll add in a circuit diagram to the github so people can copy that.
### If you're reading these comments and thinking "holy moly, he needs to chill", just know that I wanted to over-comment rather than the opposite. Also, as a beginner who has tried to read other people's code, you guys need to acknowledge that I'm a dummy and have no idea what any of your stuff does.

import pyfirmata
import time
import pandas as pd
import numpy as np
import math
import statistics
import random
import spotipy
import sys
import spotipy.util as util

from threading import Thread
from pandas.io.json import json_normalize
from spotipy.oauth2 import SpotifyClientCredentials

## glob_counter is just there to be a check for the first while loop iteration so that it can move past any 'bugs' coming from no song playing

glob_counter = 0

## Copy and pasted code from the library examples for authorizing the Spotify API through OAuth2/util

client_id = 'd09b44e890e448e99b9572a7aca6d08b'
client_secret  = '258d2d8c6674405bbc58d1ad52ee85f7'
redirect_uri = 'http://localhost:50106'
scope = 'user-read-currently-playing'
token = util.prompt_for_user_token('12120950195', scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
spotify = spotipy.Spotify(auth=token)

## Setting up the board to send serial data for firmata. You only need PWM for different colors, not for the MOSFETs turning on the strips themselves.

board = pyfirmata.Arduino('COM3')

## Declare the pins controlling the strips themselves as digital outputs

pin2 = board.get_pin('d:2:o')
pin3 = board.get_pin('d:3:o')

## Declare the pins controlling the colors as PWM pins

pin9 = board.get_pin('d:9:p')
pin10 = board.get_pin('d:10:p')
pin11 = board.get_pin('d:11:p')

## Sorting the pin objects into arrays to call them easier

strips = [pin2, pin3]
palette = [pin9, pin10, pin11]

## Control the brightness limit of the strips

brightness = float(input('Please enter in a brightness value from 1-100: '))/100

## Code to turn all the pins off. Pretty self-explanatory.

def off():

    for strip in strips:
        strip.write(0)
    for color in palette:
        color.write(0)
    
    return

## The following is the code to control the lights themselves. It creates a series of random variables that are then used to control the light patterns.
## number_of_strips_to_light identifies how many light strips will go on during that cycle, I made it so that as you add or subtract strips, the only thing you need to adjust to the code is the strips array
## which_strips uses random.sample to build a non-repeating list filled with indexes for the strips array
## The list from which_strips is iterated through to light the appropriate strips

def pwm_strips():

    number_of_strips_to_light = random.randint(1,len(strips))
    which_strips = random.sample(range(0,len(strips)), number_of_strips_to_light)
    color = random.randint(0,6)
    subdivision = random.randint(0,2)
    for x in which_strips:
        strips[x].write(1)

        ## I don't know how I would shorten or clean up this code, even if I wanted to. I think that it works pretty well as is.
        ## Essentially, there are seven unique combinations with RGB. You can light any of the three colors by itself, then there is red and green, red and blue, or blue and green as possible color pairs. Lastly, you could light all three at once.
        ## So with the random variable 'color', you randomly pick one of the seven possibilities. For RGB, you just write the color as high as the brightness setting allows.
        ## If there is more than one color, you write a random value to each color to create a unique color each time.

        if color < 6:
            if color < 3:
                palette[color].write(brightness)
            if color == 3:
                pwm_setting = random.randint(1,brightness*100)/100
                palette[0].write(pwm_setting)
                pwm_setting = random.randint(1,brightness*100)/100
                palette[1].write(pwm_setting)
            if color == 4:
                pwm_setting = random.randint(1,brightness*100)/100
                palette[0].write(pwm_setting)
                pwm_setting = random.randint(1,brightness*100)/100
                palette[2].write(pwm_setting)
            if color == 5:
                pwm_setting = random.randint(1,brightness*100)/100
                palette[1].write(pwm_setting)
                pwm_setting = random.randint(1,brightness*100)/100
                palette[2].write(pwm_setting)
        if color == 6:
            pwm_setting = random.randint(1,brightness*100)/100
            palette[0].write(pwm_setting)
            pwm_setting = random.randint(1,brightness*100)/100
            palette[1].write(pwm_setting)
            pwm_setting = random.randint(1,brightness*100)/100
            palette[2].write(pwm_setting)
    
    ## I decided that just blinking on beat was a little too predictable and boring. Plus it can be really obvious when the code is lagging a bit behind the beat due to API calls
    ## So what I did here was I created a random variable called 'subdivision' and made it create a variable called 'divisor' that would equal 1, 2, or 4 so that it would divide the beat into halves or quarters randomly.
    ## This makes the pattern feel truly random and engaging. Especially with different sections lighting up. It's all personal preference though, so you can comment it out if you want.

    if subdivision == 0:
        divisor = 1
    if subdivision == 1:
        divisor = 2
    if subdivision == 2:
        divisor = 4

    ## The global variable seconds_per_beat is called here to set the delay equal to the bpm (along with any subdivision), which is what really makes the lights go with the music.

    time.sleep(seconds_per_beat/divisor)
    off()
    time.sleep(seconds_per_beat/divisor)

    return

#### 5/15/2020 the check_bpm() function was updated and the check_song() function was taken out.
#### Thanks to a ton of help from jsbueno on stackoverflow, the code now implements threading so that the API calls and lights don't have to wait on each other quite so much.
#### There is another version made that uses asyncio, but while running tests on the average speed across 25 iterations, I got the following data: normal code = 0.676 seconds, asyncio = 0.546 seconds, and threading = 0.420 seconds. So I just went with the fastest tested concurrency method
        
def check_bpm():

    ## Seconds_per_beat and current_track are declared as global variables so that they can be used between functions. I know that I could have just made a class and put the functions in there, but I am unfamiliar with classes and I don't think there's an unmatched benefit to it
    ## The default for if there is no current_track is BLEACH by BROCKHAMPTON as mentioned below. This is just to give the program something to do while it waits for you to play something.
    ## You could also easily adjust it so that it just keeps the lights off if nothing is playing, and that totally works, but these lights are for ambiance at a house party so I don't want them to ever be off or not running through the functions to make them light.

    global seconds_per_beat
    global current_track

    ## The spotify.current_user_playing_track() call gets a json object from the API with all the track info. I use json_normalize to arrange it all into a cleaner object
    ## The current track ID is assigned to the global variable 'current_track' and is then used to get the tempo through spotify.audio_features()
    ## There is another option besides using json_normalize for each API call. I also experimented with just parsing the json object to get the info I wanted, but it ran slower, so I scrapped it. If there's an even faster option let me know.

    while True:
        current_track = spotify.current_user_playing_track()
        if current_track is None:
            seconds_per_beat = 0.5
        else:
            current_track = json_normalize(current_track)
            current_track = str(current_track['item.id'].iloc[0])
            features = json_normalize(spotify.audio_features(current_track))
            tempo = float(features['tempo'].iloc[0])
            seconds_per_beat = 60/tempo
        time.sleep(1)

        ## Of note, the formula for seconds_per_beat comes from BPM. If there are x beats per minute, then 60 seconds divided by x beats per minute should give you the interval in seconds between beats.
        ## Also of note for people who haven't seen much music theory, some songs play drums and other beat-like sounds on subdivided intervals. So if the lights don't match the drums, it's because it's matching the tempo and not the actual sounds being played. It should still look good though.

def main():
    api_thread = Thread(target=check_bpm)
    api_thread.start()
    while True:
        pwm_strips()
## Setting defaut tempo value to 120 BPM. It doesn't matter too much because the tempo should update very quickly after the first API call.
seconds_per_beat = 0.5
main()
