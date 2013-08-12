#!/usr/bin/env perl

use strict;
use warnings;
use utf8;
use charnames ':full';
use Encode;

while(<>) {
    chomp;
    $_ = ord Encode::decode("UTF-8", $_);
    print charnames::viacode($_);
    print "\n";
}
