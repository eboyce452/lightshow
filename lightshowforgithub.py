### This is lightshow.py V2.1, a script with the pyrfirmata library to control an arduino running the firmata library
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

from pandas.io.json import json_normalize
from spotipy.oauth2 import SpotifyClientCredentials

## glob_counter is just there to be a check for the first while loop iteration so that it can move past any 'bugs' coming from no song playing

glob_counter = 0

## Copy and pasted code from the library examples for authorizing the Spotify API through OAuth2/util

client_id = 'Your Client ID'
client_secret  = 'Your Client Secret'
redirect_uri = 'Whatever URI Feels Good'
scope = 'user-read-currently-playing'
token = util.prompt_for_user_token('Username', scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
spotify = spotipy.Spotify(auth=token)

## Setting up the board to send serial data for firmata. You only need PWM for different colors, not for the MOSFETs turning on the strips themselves.

board = pyfirmata.Arduino('Get the COM port from the Arduino IDE')

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

## As you will see below, there are two similar looking functions below: check_bpm() and check_song().
## The reason to create two functions instead of running the check_bpm every time is because check_bpm() has two API calls, which takes an average of ~0.10 seconds longer depending on connection.
## By creating another function that just checks the song, you can run the check more frequently so that the delay in BPM change between songs is shorter, but without sacrificing performance.
## If there is a way to frequently, or even constantly, check for a song change through the API without interrupting the light pattern loop please let me know. I have looked into threading, but it's a bit beyond me at the moment.

def check_bpm():
    
    ## Seconds_per_beat and current_track are declared as global variables so that they can be used between functions. I know that I could have just made a class and put the functions in there, but I am unfamiliar with classes and I don't think there's an unmatched benefit to it
    ## The default for if there is no current_track is BLEACH by BROCKHAMPTON as mentioned below. This is just to give the program something to do while it waits for you to play something.
    ## You could also easily adjust it so that it just keeps the lights off if nothing is playing, and that totally works, but these lights are for ambiance at a house party so I don't want them to ever be off or not running through the functions to make them light.

    global seconds_per_beat
    global current_track

    ## The spotify.current_user_playing_track() call gets a json object from the API with all the track info. I use json_normalize to arrange it all into a cleaner object
    ## The current track ID is assigned to the global variable 'current_track' and is then used to get the tempo through spotify.audio_features()
    ## There is another option besides using json_normalize for each API call. I also experimented with just parsing the json object to get the info I wanted, but it ran slower, so I scrapped it. If there's an even faster option let me know.

    current_track = spotify.current_user_playing_track()
    if current_track is None:
        current_track = '0dWOFwdXrbBUYqD9DLsoyK'
        features = json_normalize(spotify.audio_features(current_track))
        tempo = float(features['tempo'].iloc[0])
        seconds_per_beat = 60/tempo
    else:
        current_track = json_normalize(current_track)
        current_track = str(current_track['item.id'].iloc[0])
        features = json_normalize(spotify.audio_features(current_track))
        tempo = float(features['tempo'].iloc[0])
        seconds_per_beat = 60/tempo

        ## Of note, the formula for seconds_per_beat comes from BPM. If there are x beats per minute, then 60 seconds divided by x beats per minute should give you the interval in seconds between beats.
        ## Also of note for people who haven't seen much music theory, some songs play drums and other beat-like sounds on subdivided intervals. So if the lights don't match the drums, it's because it's matching the tempo and not the actual sounds being played. It should still look good though.

def check_song():
    
    global current_track
    current_track = spotify.current_user_playing_track()
    if current_track is None:
        current_track = '0dWOFwdXrbBUYqD9DLsoyK'
    else:
        current_track = json_normalize(current_track)
        current_track = str(current_track['item.id'].iloc[0])

while True:

## The following code block automatically sets the song to "BLEACH" by BROCKHAMPTON (aka: 0dWOFwdXrbBUYqD9DLsoyK) on the first iteration so that there is something to check against.
## If there is no song playing, the default for the check_bpm() function is also "BLEACH" so the code will be able to loop without any data from the API.
## When a song does start playing, it will trigger the check_bpm() function and beceome the new current track.

    if glob_counter == 0:
        checked_song = '0dWOFwdXrbBUYqD9DLsoyK'
        check_bpm()
        glob_counter += 1
    check_song()
    if checked_song != current_track:
        check_bpm()
        checked_song = current_track
## Enter in code block for light patterns below:

### iterations variable is used to ensure the code loops every 5 seconds despite tempo (any faster and the lag from the API check starts to add up)
    iterations = int(round(5/seconds_per_beat/2,0))
    for x in range(0,iterations+1):
        pwm_strips()
## ----------------------------------------- ##
## Lastly, the checked_song becomes the current_track so that the next time it checks, it can figure out if it's a different song.
    checked_song = current_track