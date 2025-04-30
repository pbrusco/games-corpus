#!/usr/bin/perl
use strict;

# Agustin Gravano - Columbia University - November 2005

# This script merges several wavesurfer annotation files 
# into one Praat TextGrid file.

# full path to the program 'duration'
my $DURATION = "soxi -D";

my $stem = shift;
my $tiernames = shift;
my $tiertypes = shift;
my $tiername_for_xmin_xmax = shift;

my @tiers = split " ", $tiernames;
my @types = split "",  $tiertypes;

if (!$stem || !@tiers) {
    die "\nUsage: wavesurfer2praat.pl STEM TIERNAMES TIERTYPES [TIERNAME_FOR_XMIN_XMAX]\n".
		"Where: STEM       is the stem of the filename without extension,\n".
		"                  common to all files.\n".
		"       TIERNAMES  is a ordered list of tier names: \n".
		"                  \"TIERNAME1 TIERNAME2 TIERNAME3...\"\n".
		"       TIERTYPES  is a string of {p,P,i,I}, indicating the type of \n".
		"                  each tier: \n".
		"                  p = point, with time specified by the first column,\n".
		"                  P = point, with time specified by the second column,\n".
		"                  i = interval with both boundaries specified,\n".
		"                  I = interval with only the first boundary specified\n".
		"                      (the second column is ignored).\n\n".
		"Example: wavesurfer2praat.pl test \"tones words breaks misc\" pipp\n".
		"       will read test.tones, test.breaks, and test.misc as point tiers,\n".
		"       and test.words as an interval tier, and generate test.TextGrid.\n".
		"Important: The file test.wav needs to be present in the same dir, unless\n".
		"       the TIERNAME_FOR_XMIN_XMAX is specified. In that case, the first and\n".
		"       last points in that tier will be used as the end point of the TextGrid.\n\n";
} 

map {
	my $filename = "$stem.$_";
	die "File not found: '$filename'\n" unless -e $filename;
} @tiers;

# if the numbers of tiernames and tiertypes don't match, or
# if the tiertypes are not 'i' or 'p', terminate.
if ( (@tiers+0 ne @types+0) || ! ($tiertypes =~ m/^[iIpP]+$/)) {
	die "Wrong tier types.\n";
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

my $xmin = 0;
my $xmax;

if ($tiername_for_xmin_xmax) {
	$xmin = `cat $stem.$tiername_for_xmin_xmax | head -n1 | awk '{if (\$1>\$2) print \$2; else print \$1}'`+0;
	$xmax = `cat $stem.$tiername_for_xmin_xmax | tail -n1 | awk '{if (\$1>\$2) print \$1; else print \$2}'`+0;
}
else {
	# find out the lenghth of the wav file.
	my $wav_file = "$stem.wav";
	die "File not found: '$wav_file'" unless -e $wav_file;
	$xmax = wav_length($wav_file);
}
#print $xmax; exit;

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

my $result;

# header
$result .= "File type = \"ooTextFile\"\n";
$result .= "Object class = \"TextGrid\"\n\n";
$result .= "xmin = $xmin \n";
$result .= "xmax = $xmax \n";
$result .= "tiers? <exists> \n";
$result .= "size = ".(@tiers+0)." \n";
$result .= "item []: \n";

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

for my $i (1..@tiers) {
	my $tier = $tiers[$i-1];
	my $type = $types[$i-1];
	my $filename = "$stem.$tier";
	
	open FILE_HANDLER, $filename;
	my @lines = <FILE_HANDLER>;
	close FILE_HANDLER;
	chomp @lines;
	
	$result .= tabs(1)."item [$i]:\n";
	$result .= tabs(2)."class = \"".($type eq "p" || $type eq "P" ? 'TextTier' : 'IntervalTier')."\" \n";
	$result .= tabs(2)."name = \"$tier\" \n";
	$result .= tabs(2)."xmin = $xmin \n";
	$result .= tabs(2)."xmax = $xmax \n";


	my $buffer; # we'll save all contents of this tier here.
	
	my $previous_time = 0;
	my $j = 0;
		
	for my $line (@lines) {
		if ($line =~ m/^\s*(-?[0-9.]+)\s+(-?[0-9.]+)\s+(.*)$/) {
			$j++;

			my $col1 = $1;
			my $col2 = $2;
			my $col3 = escape_chars($3);

			if ($type eq "p") { 
				# point, with time specified by the first column
				$buffer .= tabs(2)."points [$j]:\n";
				$buffer .= tabs(3)."time = $col1 \n";
				$buffer .= tabs(3)."mark = \"$col3\" \n";
			}
			elsif ($type eq "P") { 
				# point, with time specified by the second column
				$buffer .= tabs(2)."points [$j]:\n";
				$buffer .= tabs(3)."time = $col2 \n";
				$buffer .= tabs(3)."mark = \"$col3\" \n";
			}
			elsif ($type eq "i") { 
				# interval with both boundaries specified
				$buffer .= tabs(2)."intervals [$j]:\n";
				$buffer .= tabs(3)."xmin = $col1 \n";
				$buffer .= tabs(3)."xmax = $col2 \n";
				$buffer .= tabs(3)."text = \"$col3\" \n";
			}
			elsif ($type eq "I") { 
				# I = interval with only the first boundary specified
				#     (the second column is ignored).
				$buffer .= tabs(2)."intervals [$j]:\n";
				$buffer .= tabs(3)."xmin = $previous_time \n";
				$buffer .= tabs(3)."xmax = $col1 \n";
				$buffer .= tabs(3)."text = \"$col3\" \n";

				$previous_time = $col1;
			}
		}
	}

	# now that we know how many points/intervals there are,
	# we finish printing the header
	if ($type eq "p" || $type eq "P") {    # - - - - point tier - - -
		$result .= tabs(2)."points: size = ".$j." \n";
	}
	elsif ($type eq "i" || $type eq "I") { # - - - - interval tier - - - 
	
		# special case: in praat, interval tiers must have at least
		# one interval. ie, 'empty' interval tiers have one interval
		# that starts at 0 and ends at the end of the file.
		if ($j eq 0) {
			$j = 1;
			$buffer .= tabs(2)."intervals [1]:\n";
			$buffer .= tabs(3)."xmin = $xmin \n";
			$buffer .= tabs(3)."xmax = $xmax \n";
			$buffer .= tabs(3)."text = \"\" \n";
		}

		$result .= tabs(2)."intervals: size = ".$j." \n";
	}
	
	# and we print the rest of the tier
	$result .= $buffer;	
};

open FILE_HANDLER, ">$stem.TextGrid";
print FILE_HANDLER $result;
close FILE_HANDLER;

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

sub tabs {
	my $n = shift;
	my $TABS = "    ";
	my $res;
	
	for (1..$n) { $res .= $TABS; }

	return $res;
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# returns the length in seconds of a wav file
sub wav_length {
	my $filename = shift;

	my $length = `$DURATION $filename`;
	chomp $length;

	return ($length+0);
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# escapes the characters that might cause trouble: "
sub escape_chars {
	my $str = shift;
	
	$str =~ s/"/""/g;
	return $str;
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
