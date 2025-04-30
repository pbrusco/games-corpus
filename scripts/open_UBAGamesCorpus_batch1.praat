#############################################################
## Read from a form: session number+type, and tiers to
## include in the TextGrid file.

form Games Corpus
  comment Choose the session number, player and desired tiers.
  optionmenu session
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
  
  boolean words_A 1
  boolean phrases_A 0
  boolean turns_A 1

  boolean words_B 1
  boolean phrases_B 0
  boolean turns_B 1
  
  boolean tasks 0

  optionmenu wav_file 3
    option A
    option B
    option both (stereo)
	option none
endform 

#############################################################
## Session's stem -- eg: s01.objects.1
stem$ = "s'session$'.objects.1"

## Base corpus directory.
corpusdir$ = "../"

#############################################################
## Open the wav file as a Long File.

soundselected$ = "no"
dir$ = "'corpusdir$'/b1-dialogue-wavs/"

if wav_file$ = "A"
  Read from file... 'dir$'/'stem$'.A.wav
  soundselected$ = "yes"

elsif wav_file$ = "B"
  Read from file... 'dir$'/'stem$'.B.wav
  soundselected$ = "yes"

elsif wav_file$ = "both (stereo)"
  rnd = randomInteger(1, 10000)

  ## Open both mono files (A and B)
  Read from file... 'dir$'/'stem$'.A.wav
  Rename: "tmp_'rnd'_A"
  Read from file... 'dir$'/'stem$'.B.wav
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

if words_A = 1
  tiers$ = "'tiers$' A.words"
endif
if phrases_A = 1
  tiers$ = "'tiers$' A.phrases"
endif
if turns_A = 1
  tiers$ = "'tiers$' A.turns"
endif

if words_B = 1
  tiers$ = "'tiers$' B.words"
endif
if phrases_B = 1
  tiers$ = "'tiers$' B.phrases"
endif
if turns_B = 1
  tiers$ = "'tiers$' B.turns"
endif

if tasks = 1
  tiers$ = "'tiers$' tasks"
endif

#############################################################
## Run the script, read the name of the new TextGrid file
## from the 'communication' file, and open it.

system 'corpusdir$'/scripts/CreateTemporaryTextGrid_UBAGC1.pl 'stem$' 'tiers$'
filename$ < /tmp/praat-tmp-communication.dat
Read from file... 'filename$'

if soundselected$ = "yes"
  plus Sound 'sound$'
endif

Edit
