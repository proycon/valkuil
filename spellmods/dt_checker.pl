#!/usr/bin/perl -w

use strict;
use Getopt::Std;
use IO::Socket::INET;

our($opt_l);
getopts('l:');       

## Read command line and output help if...
my $help = 'Usage: dt_checker.pl [switches]
            -l list with dt-triggers';

if (!$opt_l) {
    print STDERR "\nYou must specify dt-triggers\n\n";
    print STDERR "$help\n\n";
    exit;
}

## Main

#Reads list of dt-triggers
#This is to make sure the timbl classifier only gets activated when necessary
my %list = read_list();

#Reads input in particular format (specified in the processchain)
#Returns @ngrams (array) and %focus_words (hash: key = ngram, value = focus_word)
my ($ngrams, $focus_words) = read_input();

#Activates timbl classifier for focus_words in triggerlist
#prints focus_word plus correction if applicable
dt_checker($ngrams, $focus_words, \%list);

## Subs
sub read_list {
    my %list = ();
    open(LIST, $opt_l) || die "Cannot open file $opt_l: $!\n";
    while (my $line = <LIST>) {
        chop($line);
        #Add trigger to %list
        $list{$line}++;
        #Add trigger plus -t to %list
        $line =~ s/(.*)/$1t/;
        $list{$line}++;
    }
    return %list;
}

sub read_input {
    my @words = ();
    my @ngrams = ();
    my %focus_words = ();
    while (my $line = <>) {
        chomp($line);
        @words = split(/\s+/, $line);
        #get focus_word from input
        my $focus_word = pop(@words);
        #change focus_word in ngram to version ending with -d
        if ($focus_word =~ /.*t$/) {
            $words[2] =~ s/(.*)t$/$1/;
        }
        my $ngram = join(' ', @words);
        push(@ngrams, $ngram);
        $focus_words{$ngram} = $focus_word;
    }
    return(\@ngrams, \%focus_words);
}

sub dt_checker {
    my $ngrams = shift;
    my $focus_words = shift;
    my $list = shift;
    #connect to machine with timbl classifier
    my $socket = new IO::Socket::INET (
        PeerAddr => 'chronos.uvt.nl',
        PeerPort => '2000',
        Proto => 'tcp',
        Timeout => '2')
    || die "Could not create socket: $@\n";

    print STDERR "\t\tConnected to server\n";

    #catch "Welcome to the Timbl server."
    my $result=<$socket>;
    if ($result !~ /^Welcome/) {
        die "Could not connect to Timbl classifier: $!\n";
    }

    print STDERR "\t\tProcessing input\n";

    foreach my $n (@$ngrams) {

    #if focus_word = trigger
        if (exists $$list{$$focus_words{$n}}) {
            print STDERR "\t\tClassifying\n"; 
            print $socket "classify $n ?\n";
            my $result=<$socket>;
            chomp($result);
            $result =~ s/CATEGORY \{([dt]*)\}/$1/;
            #if focus_word and timbl suggestion are the same, only print focus_word
            if ($$focus_words{$n} =~ /d$/ && $result =~ /^d$/ || $$focus_words{$n} =~ /dt$/ && $result =~ /^dt$/) {
                print "$$focus_words{$n}\n";
            #if genuine correction, print focus_word plus correction
            } elsif ($$focus_words{$n} =~ /d$/ && $result =~ /^dt$/) {
                print "$$focus_words{$n} ";
                $$focus_words{$n} =~ s/^(.*)d$/$1dt/;
                print "$$focus_words{$n}\n";
            } else {
                print "$$focus_words{$n}\n";
            }
        } elsif ($$focus_words{$n} =~ /<begin>/ || $$focus_words{$n} =~ /<end>/ ) {
            next;
        } else {
            print "$$focus_words{$n}\n";
        }
    }
    close($socket);
}

