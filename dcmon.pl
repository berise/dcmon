#!/usr/bin/perl
# Crawl images in dcinside.com(called ZzalBaang which prevents articles be moderated)
# This is perl version.
#
# usage
# perl dcmon.pl [gallery name]
# eg. perl dcmon.pl game_classic
# berise@gmail.com
# you need a 'wget' in you PATH

# Webpages from http://gall.dcinside.com/list.php?id=game_classic&no=403226&page=1&bbs=
# to http://gall.dcinside.com/list.php?id=game_classic&no=1&page=1&bbs=
# total pages : around 400,000 pages 
#

use strict;
use warnings;
use utf8;

use LWP::Simple;
use Encode;
use WWW::Mechanize;
use Web::Scraper;
use Data::Dumper;


#  print "This is libwww-perl-$LWP::VERSION\n";

my $CFG_DCMON = "dcmon.cfg"; # fixed
my $directory_name = "call_setup_directory";
my %opt = ( "debug"=>1 );
my %statistic = ();

# to make STDOUT flush immediately
$| = 1;


my $TEST = 0;
# tests
if ($TEST == 1)
{
    test_1114();
    exit;
}
else
{
    show_usage();
    load_cfg();
}


#http://gall.dcinside.com/board/view/?id=pad&no=227106&page=1
# page 228546
sub test_1114
{
	my $no = -2;
	my $prev_index = -1;
    my $curr_index = -1;
	my @prev_list = ();
    my $gallery_name = "pad";

	# to print in status subroutine
	$statistic{$gallery_name} = 0;
	my $image_count = 0;

	setup_directory($gallery_name);

    my $url = get_dcinside_address($gallery_name);
    $url =  $url . "&no=228546&page=1";
    print $url;

    # save images and add to count
    $image_count = find_and_get_images($gallery_name, $url);
}


# get filenames
sub scrape_href_links
{
    my $html_content = shift;

    my $html_element = scraper {
        process ".icon_pic > a", "html[]" => 'HTML', "text[]" => 'TEXT';
    };

    # get html text based on div class="con_substance"
    my $res = $html_element->scrape( $html_content );

    #print Dumper $res;

    # return a reference to image links
    return $res->{text};
}

# parse html with WWW:Scraper and extract image links
sub scrape_links
{
    my $html_content = shift;

    my $html_element = scraper {
        process ".con_substance", html => 'HTML';
    };

    # [] for plural
    my $img_element = scraper {
        process "img", "src[]" => '@src';
    };

    # get html text based on div class="con_substance"
    my $res = $html_element->scrape( $html_content );

    # get img src link which shows real image (in javascript pop window)
    my $res2 = $img_element->scrape( $res->{html});

#    print Dumper $res;
#    print Dumper $res2;
    return $res2->{src};
}


###
sub load_cfg
{
	open(my $CFG_IN, "<$CFG_DCMON");
	my @lines = <$CFG_IN>;
	close($CFG_IN); 

	foreach my $gallery (@lines)
	{
        next if $gallery =~ /^#/;
		chomp $gallery;
		#print $gallery;
		do_fork($gallery);
	}
}

sub do_fork
{
	my $gallery_name = shift;
	{
		print "Monitoring $gallery_name\n"; 

		# run this script
		my $pid = fork(); 
		if ($pid == 0)
		{
			run_dcmon_with_given_name($gallery_name);
			exit;
		} 
	}
}


# run dcmon with given name
sub run_dcmon_with_given_name
{
	my $gallery_name = shift;

	#print $gallery_name;
	setup_directory($gallery_name);

	# monitor and get
	monitor_and_get($gallery_name);
}


sub show_usage
{
	print "dcmon: A small utility to monitor your favorite galleries.\n";
	print "       Edit dcmon.cfg and run\n";
	print "       by berise\n\n";
#	exit;
}


# crawl given page
# TI : size of array
sub find_and_get_images
{
	my ($gallery_name, $url) = @_;
	my $html_contents = get($url);
    #print $html_contents;

	my $h_filenames =  scrape_href_links($html_contents);
	my $h_links =  scrape_links($html_contents);

    if (!defined($h_filenames))  # http://zzbang.dcinside.com/pad_temp.jpg is basic image for an article without any image attached
    {
        print "[$gallery_name] No image was found\n" if $opt{debug};
        return ;
    }

	my $file_count = @{$h_filenames};
	my $link_count = @{$h_links};
	my $image_count = 0;

    #print "# of files : ($file_count), # of links : ($link_count)\n" if $opt{debug};
	for(my $i = 0; $i < $file_count; $i++)
	{
    	my $filename_p;
        $filename_p = encode('cp949', $h_filenames->[$i]);
        #print " - download $filename_p\n";
        #print "$h_filenames->[$i], $h_links->[$i]\n" if $opt{debug};
		download_and_save_as($h_filenames->[$i], $h_links->[$i]);
	}

	return $file_count;
}
	

#
# Web::Scraper sometimes died with a malicious formed html.
# So here left old regex based parsing code.
# WARNING : following code is not work anymore
sub extract_filenames
{
	my $html_contents = shift;

	my $pattern = "<li class=\"icon_pic\"><a href=.*>(.*?.*?)<\/a>";
	my @files = $html_contents =~ /$pattern/gi;

	foreach my $file (@files) { print "extract_filenames : $file\n" if $opt{debug}; } 
    #print "Attached Image filename : @files\n" if $opt{debug};
	return @files;
}

#
# Web::Scraper sometimes died with a malicious formed html.
# So here left old regex based parsing code.
# WARNING : following code is not work anymore
sub extract_links
{
	my $html_contents = shift;

    #my $pattern = "src='(http://dcimg1.dcinside.com/viewimage.php?.*?)'";
	my $pattern = "<li class=\"icon_pic\"><a href=\"(.*)\">.*?.*?<\/a>";
	my @links = $html_contents =~ /$pattern/gi;

	foreach my $link (@links) {
        print "extract_links : @links\n" if $opt{debug};
    }

	return @links;
}


#
# Windows XP에서는 cp949로 변환해야 콘솔창에서 한글이 보인다.
# Vista/7에서는 utf-8을 써도 무방할 듯...
sub download_and_save_as
{
	my ($filename, $link) = @_;
	my $filename_p = encode('cp949', $filename);

    my $USE_WGET = 0;
    my $USE_MECHANIZE = 0;
    my $USE_LWP = 1;

	# 저장할 위치 지정
    $filename_p = $directory_name . "/" . $filename_p; 

    # 위치를 고정하여 저장한다. .. 파일 보기가 편해서...
	#$filename_p = "dcmon/temp/" . $filename_p; 

    if ($USE_WGET eq 1)
    {
        my $cmd_wget = "wget \"$link\"";
        print "Execute $cmd_wget\n";

        # download with wget
        system($cmd_wget);
    }
    elsif ($USE_MECHANIZE eq 1)
    {
        # mechanize
        my $image = get($link);

        if (defined $image)
        {
            open(my $fh_out, ">$filename_p");
            binmode $fh_out;
            print $fh_out $image;
            close($fh_out); 
        }
    } elsif ($USE_LWP eq 1) { # download with a LWP, ref : http://lotus.perl.kr/2012/01.html
        my $ua = LWP::UserAgent->new( agent =>
            'Mozilla/5.0'
            .' (Windows; U; Windows NT 6.1; en-US; rv:1.9.2b1)'
            .' Gecko/20091014 Firefox/3.6b1 GTB5'
        );
        my $res;
        eval { $res = $ua->get($link); };
        if ($@) {
            warn $@;
            # next;
        }

        open my $fh, ">", $filename_p;

        binmode $fh;
        print $fh $res->content;
        close $fh;
    }

    my $filesize = -s $filename_p if -e $filename_p;
    print " + $filename_p($filesize Bytes)\n" if $opt{debug};
}


sub setup_directory
{
	my ($gallery_name, $end) = @_;
	my $dcmon_dir = "dcmon";
	$directory_name =  $dcmon_dir . "/" . $gallery_name;

	if (-d $dcmon_dir) {
		print "$gallery_name already exists.\n" if $opt{debug};
	}
	else {
		print "Make a directory $dcmon_dir.\n" if $opt{debug};
		mkdir($dcmon_dir);
	}

	unless (-d $directory_name) {
		print "Make directory $directory_name.\n" if $opt{debug};
		mkdir($directory_name);
	}
	else {
		print "$directory_name Directory already exists\n" if $opt{debug};
	}
#	print "set up directory for $directory_name is finished.\n" if $opt{debug};
}



sub get_dcinside_address
{
	my $gallery_name = shift;

    my $html_url;
    $html_url = "http://gall.dcinside.com/board/view/?id=" . $gallery_name;

    return $html_url;
}

sub monitor_and_get
{
	my $gallery_name = shift;
	my $no = -2;
	my $prev_index = -1;
    my $curr_index = -1;
	my @prev_list = ();

	# to print in status subroutine
	$statistic{$gallery_name} = 0;
	my $image_count = 0;


	while(1)
	{
	    my $image_count = 0;
		my @new_list = get_recent_number_list($gallery_name); 
        #print "[$gallery_name] Article List : \n";
        #if (@new_list) { foreach my $i (@new_list[0..6]) { print " $i "; } print "\n"; }
        #if (@prev_list) { foreach my $i (@prev_list[0..6]) { print " $i "; } print "\n"; }

		$curr_index = determine_most_recent_page_number(\@new_list, \@prev_list);
		@prev_list = @new_list;

    	if ($curr_index != -1) 
		{
			print "[$gallery_name] New article : $new_list[$curr_index]\n" if $opt{debug};
		}
		else
        {
            my $sleep_time = 5 + int(rand(15));
            print "[$gallery_name] wait...($sleep_time)\n" if $opt{debug};
            my $sign = length($gallery_name);

            sleep($sleep_time);  # sleep time 5 ~ 20 sec
			next;
        } 


		if (($prev_index != $curr_index) and ($curr_index != -1))
		{
			print "[$gallery_name] get a web page : $new_list[$curr_index]\n" if $opt{debug}; 

            my $url = get_dcinside_address($gallery_name);
			$url =  $url . "&no=" . $new_list[$curr_index] . "&page=1";

			# save images and add to count
			$image_count = find_and_get_images($gallery_name, $url);

            # update index
			$prev_index = $curr_index; 
		}

        print "[$gallery_name] index = $curr_index,  no = $new_list[$curr_index]\n" if $opt{debug};
		my $sleep_time = sleep( 5 + int(rand(15)));  # sleep time 5 ~ 20 sec
		sleep($sleep_time); 
	}
}

sub get_recent_number_list
{
	my $gallery_name = shift;
    my $html_url;

    # dcinside는 페이지 이동이 잦음
    $html_url = get_dcinside_address($gallery_name);
    #print "[get_recent_number_list] $html_url" if $opt{debug};

    my $mech = WWW::Mechanize->new();

    $mech->agent_alias('Windows Mozilla');

    my $response = $mech->get($html_url);

    if ($mech->success()) {
        #print "[Mechanize] success\n";
    }
    else {
        print STDERR $response->status_line, "\n";
    }
	my $html_contents = get($html_url);
    #print $html_contents;

    # get article numbers
	my $pattern = "id=" . $gallery_name . "&no=(\\d+)&page=\\d+";#/.*?<\/a>";
	my @list = $response->decoded_content =~ /$pattern/gi;

	return @list;
}


sub determine_most_recent_page_number
{
	# reference of list
	my ($no_list, $prev_no_list) = @_;
	my $mru_index = -1;

    #print "MRU @{$no_list}, @{$prev_no_list}\n";
	if (@{$prev_no_list})
	{
		my $list_size = scalar(@{$no_list});
		foreach my $x (0 .. $list_size-1)
		{
            #print "comparing... $x: $no_list->[$x]:$prev_no_list->[$x]\n";
			if ($no_list->[$x] != $prev_no_list->[$x])
			{
				$mru_index = $x;
				#print "MRU index : $mru_index, MRU page : $no_list->[$mru_index]\n";
				last;
			}
		}
	}

	return $mru_index;
}
