#!/usr/bin/perl -w

use strict;
use Getopt::Std;

our($opt_l);
getopts('l:');       

## Read command line and output help if...
my $help = 'Usage: errorlist_comparison.pl [switches]
            -l List to compare with';

if (!$opt_l) {
    print STDERR "\nYou must specify an input list to compare to\n\n";
    print STDERR "$help\n\n";
    exit;
}

## Main

my @words = read_input();
my %list = read_list();
compare(\@words, \%list);

## Subs
sub read_input {
    my @words = ();
    while (my $line = <>) {
        @words = split(/\s+/, $line);
    }
    return @words;
}

sub read_list {
    my %list = (); #hash with key = error and value = correction
    open(LIST, $opt_l) || die "Cannot open file $opt_l: $!\n";
    while (my $line = <LIST>) {
        chomp($line);
        my($corrected, $error) = split(/~/,$line);
        if (exists $list{$error}) {
            print STDERR "This key already exists: $error\n";
            # exit;
        } else {
            $list{$error} = $corrected;
        }
    }
    return %list;
}

sub compare {
    my $words = shift;
    my $list = shift;
    foreach my $w (@$words) {
        if (exists $$list{$w}) {
            print "$w $$list{$w}\n";
            #print "Spelling error $w - should be $$list{$w}\n";
#        } elsif ($w =~ /<utt>/) {
#            print "$w\n"
        } else {
            print "$w\n";
        }
    }
}
