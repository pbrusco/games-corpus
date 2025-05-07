Scripts for opening UBA Games Corpus files on Praat, selecting the 
desired tiers (words, turns, etc.).

Requirements: Linux, Praat, bash, Perl, some patience.

Important: the 'scripts' directory should be placed along the directories
containing the corpus files. For example:
/path/to/uba-games-corpus/scripts/
/path/to/uba-games-corpus/b1-dialogue-wavs/
/path/to/uba-games-corpus/b1-dialogue-words/
/path/to/uba-games-corpus/b1-dialogue-tasks/
etc.

These scripts should work on *Linux*. I have no idea if they work on 
Windows or Mac, sorry.

-----

Description of files:

open_UBAGamesCorpus_batch1.praat
open_UBAGamesCorpus_batch2.praat
	Praat scripts that create and open a temporary TextGrid file with a
	number of selected tiers for a session of the UBA Games Corpus, 
	batch 1 or 2. Run from Praat.
	Optionally, append these lines to ~/.praat-dir/buttons5: 
    Add menu command... "Objects" "Read" "-- games --" "" 0 
    Add menu command... "Objects" "Read" "Open UBA Games TextGrid (batch 1)" "" 0 /full/path/to/open_UBAGamesCorpus_batch1.praat
    Add menu command... "Objects" "Read" "Open UBA Games TextGrid (batch 2)" "" 0 /full/path/to/open_UBAGamesCorpus_batch2.praat

CreateTemporaryTextGrid_UBAGC1.pl
CreateTemporaryTextGrid_UBAGC2.pl
    Required Perl scripts that create a TextGrid file for UBA Games Corpus, batch 1 or 2.

wavesurfer2praat.pl
    Required Perl script that takes several wavesurfer files and creates a Praat TextGrid.
    
-----
Agustin Gravano
April 2025

