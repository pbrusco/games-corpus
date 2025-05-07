#############################################################
## Read from a form: session number+type, and tiers to
## include in the TextGrid file.

form Games Corpus
  comment Choose the session number, player and desired tiers.
  optionmenu session
    option 21
    option 22
    option 23
    option 24
    option 25
    option 26
    option 27
    option 28
    option 29
    option 30

  optionmenu task
    option 01
    option 02
    option 03
    option 04
    option 05
    option 06
    option 07
    option 08
    option 09
    option 10
    option 11
    option 12
    option 13
    option 14
    option 15
    option 16
    option 17
    option 18
    option 19
    option 20
    option 21
    option 22
    option 23
    option 24
    option 25
    option 26
    option 27
    option 28
    option 29
    option 30
  
  boolean phrases_A 1
  boolean turns_A 1

  boolean phrases_B 1
  boolean turns_B 1
  
  optionmenu wav_file 3
    option A
    option B
    option both (stereo)
	option none
endform 

#############################################################
## Session's stem -- eg: s01.objects.1
stem$ = "s'session$'.objects.'task$'"

## Base corpus directory.
corpusdir$ = "../"

#############################################################
## Open the wav file as a Long File.

soundselected$ = "no"
dir$ = "'corpusdir$'/b2-dialogue-wavs/"

if wav_file$ = "A"
  Read from file... 'dir$'/'stem$'.channel1.wav
  soundselected$ = "yes"

elsif wav_file$ = "B"
  Read from file... 'dir$'/'stem$'.channel2.wav
  soundselected$ = "yes"

elsif wav_file$ = "both (stereo)"
  rnd = randomInteger(1, 10000)

  ## Open both mono files (A and B)
  Read from file... 'dir$'/'stem$'.channel1.wav
  Rename: "tmp_'rnd'_A"
  Read from file... 'dir$'/'stem$'.channel2.wav
  Rename: "tmp_'rnd'_B"

  ## Combine into stereo sound.
  selectObject: "Sound tmp_'rnd'_A"
  plusObject: "Sound tmp_'rnd'_B"
  Combine to stereo

  ## Remove temporary objects.
  Rename: "tmp_'rnd'_stereo"
  selectObject: "Sound tmp_'rnd'_A"
  Remove
  selectObject: "Sound tmp_'rnd'_B"
  Remove

  ## Select new stereo sound.
  selectObject: "Sound tmp_'rnd'_stereo"
  soundselected$ = "yes"
endif

if soundselected$ = "yes"
  sound$ = selected$("Sound")
endif

#############################################################
## Prepare the script tier names.

tiers$ = ""

if phrases_A = 1
  tiers$ = "'tiers$' channel1.phrases"
endif
if turns_A = 1
  tiers$ = "'tiers$' channel1.turns"
endif

if phrases_B = 1
  tiers$ = "'tiers$' channel2.phrases"
endif
if turns_B = 1
  tiers$ = "'tiers$' channel2.turns"
endif

#############################################################
## Run the script, read the name of the new TextGrid file
## from the 'communication' file, and open it.

system 'corpusdir$'/scripts/CreateTemporaryTextGrid_UBAGC2.pl 'stem$' 'tiers$'
filename$ < /tmp/praat-tmp-communication.dat
Read from file... 'filename$'

if soundselected$ = "yes"
  plus Sound 'sound$'
endif

Edit
