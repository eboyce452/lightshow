# lightshow
This is a Python script used to control multiplexed RGB strips through an Arduino running Firmata and the Pyfirmata library

I will try to make this README as robust as possible, but please let me know if there are changes I can make to ensure it is as professional and as helpful as possible.

---------------HARDWARE-------------------------------------------------

I am using an Arduino Uno knockoff from China, but the layout on the board is the same. In theory, this should run with just about any chip or board configuration on the Arduino platform as the Firmata code is pretty streamlined. That being said, it's 12454 bytes so just make sure there is enough memory. Also, the hardware I have set up uses three PWM pins base, plus a digital pin for each LED strip you're using. So pretty essential that it has at least four pins.

With the transistors in the circuit, the pin requirements for one strip is actually less efficient as you need four pins for one strip (whereas if you just connected each color from the strip to a pin you would only need three). After the first strip, it becomes incredibly efficient. Namely because the Arduino only has six PWM pins: pins 3, 5, 6, 9, 10, and 11. If you use two strips, you use all of them. With the AND gates, you only need three PWM pins and two digital pins. At three strips, the control becomes impossible with PWM, and at four strips you max out all the pins on the Arduino. At four strips with this configuration, you are only using seven pins. So in theory with this setup, your upper limit with the arduino is nine strips with full RGB control off the digital pins. Could you squeeze more out of it? Sure. But since I'm not Lebron James, my house is not big enough to justify more than 270 feet of LED's. Plus soldering wires to them can be a pain, so whatever.

I am using IRLB8721 MOSFET N-Channel Transistors which are more than good enough for the 12V 3A power supply I am using. Use whatever you want though that has a gate that can be triggered by the 5v Arduino pin and can handle the amps your strips need is good enough.

I'll include a rough mockup of the circuit somewhere in the files to this if I can.

The last note I have is that you can actually skip the Arduino altogether and run the Python script in micropython on an ESP8266 or similar chip. With the right board, you don't need to keep a computer connected at all, as you can connect an ESP8266 (with a wifi card) to your network through the boot file, then upload the full python script with the Spotipy library to the ESP8266, and have it run completely independently. This is a change I'm looking at making shortly, as Python is a language I'm much more confident in than Processing.

-------------SOFTWARE------------------------------------------------------

The software actually uses two scripts. One is in Python and the other is written in Processing for the Arduino.

The latter is actually an example script that comes with the Arduino IDE. In the IDE, if you go to file --> examples --> examples for any board --> firmata and load that, you'll have all the Processing code you need. Just upload that to your board and your Arduino is prepped.

The former is script I wrote in Python. It uses the Spotify API through the Spotipy library to get the tempo of a song currently playing and then stores that in a variable that's used to adjust the timing of the lights so they go with the music. It uses the Pyfirmata library to then send serial data to the Arduino through the Python script. The Firmata script running on the Arduino board reads the serial data and activates the appropriate pins. How the lights are turned on or controlled from there is largely up to you and your preferences, but I have included a function that uses PWM to create random, varied colors and that turns on different strips/segments of LED's randomly.

The Python script is structured to only call the API once every 5 seconds. This is for two reasons: I don't want the API to rate limit me, and every time the API is called there's a 0.15 second delay with my network speed. Since the script has to finish the API call before it can resume the lights, more API calls creates more and more sync issues. In an ideal world, I would be able to check the API constantly in the background (or as constantly as rate limits allow), without slowing down the cycle the lights run through. Basically just checking to see if a song has changed all the time, and only interrupting the while loop the lights are in when the song changes. I have been reading a lot about threading (asyncio even more so since I can pinpoint exactly where the thread would switch) with Python, but I'm not actually sure that will accomplish what I want it to. (I have read that GIL limits one Python thread to run at a time.) So I might, in the future, look into multiprocessing and/or writing some parts in another language. As I gain more experience there, or if people weigh in and help teach, then that is an area that can definitely be improved.


