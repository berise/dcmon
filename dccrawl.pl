#!/usr/bin/perl
# Crawl images in dcinside.com(called ZzalBaang which prevents articles be moderated)
# This is perl version.
#
# usage
# perl dccrawl.pl [gallery name] [range]
# eg. perl dccrawl.pl [game_classic] [1, 1000]
# berise@gmail.com
# you need a 'wget' in you PATH

# Webpages from http://gall.dcinside.com/list.php?id=game_classic&no=403226&page=1&bbs=
# to http://gall.dcinside.com/list.php?id=game_classic&no=1&page=1&bbs=
# total pages : around 400,000 pages 
#

#use strict;
use warnings;
use utf8;
use Encode;


use LWP::Simple;

#  print "This is libwww-perl-$LWP::VERSION\n";


my $gallery_name;
my $page_from;
my $page_to;


&run_dccrawler;


sub run_dccrawler()
{
	&process_arguments; 
}

sub doit()
{ 
	foreach $page ($page_from .. $page_to)
	{
		$url = "http://gall.dcinside.com/list.php?id=" . $gallery_name . "&no=" . $page . "&page=1&bbs=";

		print "$url\n";
		&suck_it($url);
	} 
}

sub process_arguments()
{
	if ( $#ARGV == 2 )
	{
		$gallery_name = $ARGV[0];
		$page_from = $ARGV[1];
		$page_to = $ARGV[2];

#	print "$gallery_name, $page_from, $page_to";

		&doit($gallery_name, $page_from, $page_to);

	}
	else
	{
		print "Usage:\n";
		print "$0 galleryname from to\n"; 
	}
}


sub suck_it()
{
	my $url = shift;
#$html_contents = &get_html_contents("http://gall.dcinside.com/list.php?id=game_classic&no=409129&page=1&bbs=");
	$html_contents = &get_html_contents($url);

	@filenames =  &extract_filenames($html_contents);
	@links =  &extract_links($html_contents);

	print "# of files : ($#filenames+1), # of links : ($#links+1)\n";
	foreach $i  (0 .. $#filenames)
	{
		&serialize($filenames[$i], $links[$i]);
	}
}
	

sub get_html_contents()
{
	$url = shift;

	$h_contents = get($url);

	return $h_contents;
}

sub extract_filenames()
{
	$html_contents = shift;

	$pattern = "<a class='txt03'.*?>(.*?.jpg)<\/a>";
	@files = $html_contents =~ /$pattern/gi;

	foreach $file (@files) { print "extract_filenames : $file\n"; } 

	return @files;
}


sub extract_links()
{
	$html_contents = shift;

	$pattern = "src='(http://dcimg1.dcinside.com/viewimage.php?.*?)'";
	@links = $html_contents =~ /$pattern/gi;

	foreach $link (@links) { print "extract_links : $link\n"; }

	return @links;
}


#
# Windows XP에서는 cp949로 변환해야 콘솔창에서 한글이 보인다.
# Vista/7에서는 utf-8을 써도 무방할 듯...
sub serialize()
{
	my ($filename, $link) = @_;
	my $converted_filename = encode('cp949', $filename);

	print "Try to serialize $converted_filename in $link\n";

	$image = &get_html_contents($link);

	open(OUT, ">$converted_filename");
	binmode OUT;
	print OUT $image;
	close(OUT); 

	print "$converted_filename(" . (length($image)) . ")is saved\n\n";
}
