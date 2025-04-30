#!/usr/bin/perl

# This script creates a temporary TextGrid file with the specified tiers.
# Do not run from the shell!  It was written to be called from Praat.

use strict;
use Cwd;

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# a few constants...

# Define which tiers are interval tiers.  All the others are point tiers.
my @interval_tiers = qw/tasks A.words A.turns A.phrases B.words B.turns B.phrases/;

# Directory with the desired Games Corpus files.
my $dir = cwd()."/../";

# script that creates a TextGrid file from a number of wavesurfer files.
my $script = "$dir/scripts/wavesurfer2praat.pl";

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Script arguments: 
my $stem = shift;	# input stem: 's01.cards.2', 's12.objects.1'
my @tiernames = @ARGV;	# ([AB].{words,breaks,tones,misc,dm,pos,turns,questions}, tasks)+

die "missing arguments" unless $stem and @tiernames;

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# parse the session number from the input stem.
$stem =~ m/^s([01][0-9])\./;
my $session = $1;

# Create a temporary directory
my $tmp_dir = "/tmp/praat-tmp-".time;
print STDERR `mkdir $tmp_dir`;

# create a synlink to each file in $tmp_dir
for my $tiername (@tiernames) {
    # $tiername has "A.words", "B.turns", etc.
	
	my $tier = '';
	my $subject = '';
	my $tier_dir = '';

    if ($tiername =~ /^([AB])\.(.+)$/) {
        $subject = $1;  # A or B
        $tier_dir = "b1-dialogue-$2";   # b1-dialogue-words, b1-dialogue-turns, etc.
    } elsif ($tiername eq "tasks") {
        $tier_dir = 'b1-dialogue-tasks';
    } else {
        die "Invalid tiername format: $tiername.\n";
    }	
    print STDERR `ln -s $dir/$tier_dir/$stem.$tiername $tmp_dir/`;
}
# Use $stem.A.wav as a placeholder for $stem.wav, 
# since there are no stereo files in this corpus.
print STDERR `ln -s $dir/b1-dialogue-wavs/$stem.A.wav $tmp_dir/$stem.wav`;

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Prepare the lists of names and types to pass to the script that creates
# the TextGrid file (e.g., `$script $stem "tones words breaks misc" PiPP`)

my ($names, $types);

for my $tiername (@tiernames) {
	$names .= ($names?' ':'') . $tiername;
	$types .= (in_array($tiername, \@interval_tiers) ? 'i' : 'P');
}


# filename of the resulting TextGrid file.
my $file_out = "/tmp/$stem.tmp.".time.".TextGrid";


# GO!!  cd into the temp dir, run the script, and rename the resulting file.
my $commands = "cd $tmp_dir; ".
               "$script $stem '$names' $types";
print STDERR `$commands`;

print STDERR `cp $tmp_dir/$stem.TextGrid $file_out`;

# Save in a file the path and name of the new TextGrid file, so that 
# the Praat script can find it.
open COMMFILE, ">/tmp/praat-tmp-communication.dat";
print COMMFILE $file_out;
close COMMFILE;

# delete the temporary directory
print STDERR `rm -r $tmp_dir`;

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Says if $elem is in @$list.
# Usage: in_array('x', \@xs)
sub in_array {
	my $elem = shift;
	my $list = shift;
	my $pos = index_of($elem, $list);
	return ($pos eq -1 ? 0 : 1);
}

# Returns the index of $elem in @$list.
# Usage: index_of('x', \@xs)
sub index_of {
	my $elem = shift;
	my $list = shift;

	for (my $i=0; $i<@$list; $i++) {
		if ($$list[$i] eq $elem) {
			return $i;
		}
	}

	return -1;
}
