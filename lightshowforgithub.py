### This is lightshow.py V3.2, a script with the pyrfirmata library to control an arduino running the firmata library
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
from spotipy import oauth2

                        ##### Functions ######

## Created new functions for getting a credential and refreshing it thanks to the work of gos on SOF.
## The util.prompt_for_user_token() function actually doesn't call the refresh token function without setting a cache path. It was easier to just use the other authorization that had a dedicated refresh function
## https://stackoverflow.com/questions/49239516/spotipy-refreshing-a-token-with-authorization-code-flow

def oauth_credential():
    client_id = 'enter client id in here'
    client_secret  = 'client secret goes here'
    redirect_uri = 'your favorite redirect uri'
    scope = 'user-read-currently-playing'
    ## Not sure why, but I didn't see gos pass 'username' as an argument in the SpotifyOAuth function. Without a username or cache path the .get_cached_token() function won't be able to find the cached token
    sp_oauth = oauth2.SpotifyOAuth(client_id=client_id,client_secret=client_secret,redirect_uri=redirect_uri,scope=scope,username='put in your username')
    token_info = sp_oauth.get_cached_token()
    if not token_info:
        auth_url = sp_oauth.get_authorize_url(show_dialog=True)
        print(auth_url)
        response = input('Paste the above link into your browser, then paste the redirect url here: ')

        code = sp_oauth.parse_response_code(response)
        token_info = sp_oauth.get_access_token(code)

        token = token_info['access_token']
    ## Not sure why this wasn't in gos' code, but if you've already authorized the app then you need to declare token still
    else:
        token = token_info['access_token']
    spotify = spotipy.Spotify(auth=token)
    return spotify

def refresh():
    global token_info, spotify
    ## I added == True to the code as well to be more explicit about what we're checking for
    if sp_oauth.is_token_expired(token_info) == True:
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        token = token_info['access_token']
        spotify = spotipy.Spotify(auth=token)

def get_credential():
    
    client_id = 'client_id goes here'
    client_secret  = 'client_secret goes here'
    redirect_uri = 'your favorite uri'
    scope = 'user-read-currently-playing'
    token = util.prompt_for_user_token('your username', scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
    spotify = spotipy.Spotify(auth=token)
    return spotify

def off():

    for strip in strips:
        strip.write(0)
    for color in palette:
        color.write(0)
    
    return
  
## Split the huge pwm function into random_light and the pwm_strips functions. This just makes the if statements much shorter in the pwm_strips side

def random_light():

    number_of_strips_to_light = random.randint(1,len(strips))
    which_strips = random.sample(range(0,len(strips)), number_of_strips_to_light)
    color = random.randint(0,6)
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
## The following is the code to control the lights themselves. It creates a series of random variables that are then used to control the light patterns.
## number_of_strips_to_light identifies how many light strips will go on during that cycle, I made it so that as you add or subtract strips, the only thing you need to adjust to the code is the strips array
## which_strips uses random.sample to build a non-repeating list filled with indexes for the strips array
## The list from which_strips is iterated through to light the appropriate strips

def pwm_strips(tempo): # tempo is always set to seconds_per_beat. It's possible you can just use seconds_per_beat because it's global, but the threading was so unpredictable I wanted to be sure that the code was flowing as intended.

    subdivision = random.randint(0,4)
    
    ## I decided that just blinking on beat was a little too predictable and boring. Plus it can be really obvious when the code is lagging a bit behind the beat due to API calls
    ## So what I did here was I created a random variable called 'subdivision' and made it create a variable called 'divisor' that would equal 1, 2, or 4 so that it would divide the beat into halves or quarters randomly.
    ## This makes the pattern feel truly random and engaging. Especially with different sections lighting up. It's all personal preference though, so you can comment it out if you want.

    ## Made things iterate so that they occupy a full beat. I'm playing around with different ways to make the pattern more appealing.
    ## At a certain point I'll incorporate different random lighting patterns based on a song's tempo threshold and/or on other features through Spotify such as danceability or energy
    if subdivision == 0:
        divisor = 1
        random_light()
        time.sleep(tempo/divisor)
        off()
        time.sleep(tempo/divisor)

    if subdivision >= 3:
        divisor = 4
        for loop in range(0,4):
            random_light()
            time.sleep(tempo/divisor)
            off()
            time.sleep(tempo/divisor)
    else:
        divisor = 2
        for loop in range(0,2):
            random_light()
            time.sleep(tempo/divisor)
            off()
            time.sleep(tempo/divisor)

    ## The global variable seconds_per_beat is called here to set the delay equal to the bpm (along with any subdivision), which is what really makes the lights go with the music.
    
    return
        
def check_bpm():

    ## The spotify.current_user_playing_track() call gets a json object from the API with all the track info. I use json_normalize to arrange it all into a cleaner object
    ## There is another option besides using json_normalize for each API call. I also experimented with just parsing the json object to get the info I wanted, but it ran slower, so I scrapped it. If there's an even faster option let me know.
    ## seconds_per_beat is globalized so that it's shared with both threads
    global seconds_per_beat
    while True:
        ## The token from the API expires after 1 hour, so the intention of the try here is to ensure that if the token expires it will just grab a new one from the API. Hard to test though because you have to wait so long.
        try:
            current_track = spotify.current_user_playing_track()
        except:
            print('error: generating new credential')
            refresh()
            current_track = spotify.current_user_playing_track()
        if current_track is None:
            seconds_per_beat = 10000 
            # I had experimented with defining a new variable to check if there was nothing playing, but I was running into so many issues with shared variables.
            # In order to make my life less hellish, I figured I could just set a variable I already knew worked to an arbitrarily high value. It works so I won't change it.
            refresh()
        else:
            current_track = json_normalize(current_track)
            play_check = current_track['is_playing'].iloc[0]
            if play_check == False:
                seconds_per_beat = 10000
                # Again, this just sets spb to an arbitrary value so that the code can stop the lights if nothing is playing.
                # It may be important to note that there are two conditions that may cause silence: the song being paused, or there being no song in the first place (either because you haven't selected one yet or because the spotify client is closed).
            else:
                current_track = str(current_track['item.id'].iloc[0])
                try:
                    features = json_normalize(spotify.audio_features(current_track))
                except:
                    refresh()
                    features = json_normalize(spotify.audio_features(current_track))
                tempo = float(features['tempo'].iloc[0])
                seconds_per_beat = 60/tempo
        ## Of note, the formula for seconds_per_beat comes from BPM. If there are x beats per minute, then 60 seconds divided by x beats per minute should give you the interval in seconds between beats.
        ## Also of note for people who haven't seen much music theory, some songs play drums and other beat-like sounds on subdivided intervals. So if the lights don't match the drums, it's because it's matching the tempo and not the actual sounds being played. It should still look good though.

def main():
    time.sleep(5) # main() starts on a one second sleep so that the check_bpm() function has time to define seconds_per_beat before it's called
    while True:
        if seconds_per_beat != 10000:
            print(seconds_per_beat)
            pwm_strips(seconds_per_beat)
## If you want to check the performance of the threading, just uncomment the following code and comment out the previous two lines.
    #         start = time.perf_counter()
    #         pin2.write(1)
    #         pin9.write(1)
    #         time.sleep(seconds_per_beat)
    #         pin2.write(0)
    #         pin9.write(0)
    #         time.sleep(seconds_per_beat)
    #         stop = time.perf_counter()
    #         print('Time performance: ', (stop - start) - (2*seconds_per_beat))
## That code will time how long it takes to light everything while checking the API. The typical value without threading is about 0.15-0.25 seconds for me. With threading it's about 0.003 seconds.
        else:
            print('off')
            time.sleep(0.1)
####################################################################################
                                        
                                        ### MAIN CODE ###


##### SETUP ######

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

## Control the brightness limit of the strips. Made an effort to make it dummy proof.

try:
    brightness = float(input('Please enter in brightness value from 0-100: '))
except:
    brightness = 100
if brightness > 100:
    brightness = 100
if brightness < 0:
    brightness = 0
brightness = brightness/100

## Create initial credential and define threads with their target functions

spotify = oauth_credential()
api_thread = Thread(target=check_bpm)
run_thread = Thread(target=main)

###### END SETUP #####

###### MAIN LOOP ######

## Run threads

api_thread.start()
run_thread.start()
api_thread.join()
run_thread.join()

######           ######
