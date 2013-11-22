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

use URI;
use Web::Scraper;
use Data::Dumper;


#  print "This is libwww-perl-$LWP::VERSION\n";

my $CFG_DCMON = "dcmon.cfg"; # fixed
my $gallery_name;
my $page_from;
my $page_to;
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
    run_dcmon_with_cfg();
}

#http://gall.dcinside.com/board/view/?id=pad&no=227106&page=1
# page 228546
sub test_1114
{
	my $no = -2;
	my $prev_no = -1;
    my $no_index = -1;
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
    $image_count = find_and_get_images($url);
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
sub run_dcmon_with_cfg
{
	open(CFG_IN, "<$CFG_DCMON");
	my @lines = <CFG_IN>;
	close(CFG_IN); 

	foreach my $gallery (@lines)
	{
        next if $gallery =~ /^#/;
		chomp $gallery;
		#print $gallery;
		run_dcmon_with_list($gallery);
	}
}

sub run_dcmon_with_list
{
	my $gallery_name = shift;
#	for my $i (@gall_list)
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
	print "       by behemoth\@beneath.bastion\n\n";
#	exit;
}


# crawl given page
# TI : size of array
sub find_and_get_images
{
	my $url = shift;
	my $html_contents = get_html_contents($url);
    #print $html_contents;


	my $h_filenames =  scrape_href_links($html_contents);
	my $h_links =  scrape_links($html_contents);

    if (!defined($h_filenames))  # http://zzbang.dcinside.com/pad_temp.jpg is basic image for an article without any image attached
    {
        return ;
    }

	my $file_count = @{$h_filenames};
	my $link_count = @{$h_links};
	my $image_count = 0;

	print "# of files : ($file_count), # of links : ($link_count)\n" if $opt{debug};
	for(my $i = 0; $i < $file_count; $i++)
	{
    	my $filename_p;
        $filename_p = encode('cp949', $h_filenames->[$i]);
        #print " - download $filename_p\n";
        print "$h_filenames->[$i], $h_links->[$i]\n" if $opt{debug};
		download_and_save_as($h_filenames->[$i], $h_links->[$i]);
	}

	return $file_count;
}
	

sub get_html_contents
{
    my $url = shift;
    #print "[get_html_contents] $url\n";
	my $h_contents = get($url);

	return $h_contents;
}

sub extract_filenames
{
	my $html_contents = shift;

	my $pattern = "<li class=\"icon_pic\"><a href=.*>(.*?.*?)<\/a>";
	my @files = $html_contents =~ /$pattern/gi;

	foreach my $file (@files) { print "extract_filenames : $file\n" if $opt{debug}; } 
    #print "Attached Image filename : @files\n" if $opt{debug};
	return @files;
}


sub extract_links
{
	my $html_contents = shift;

    #my $pattern = "src='(http://dcimg1.dcinside.com/viewimage.php?.*?)'";
	my $pattern = "<li class=\"icon_pic\"><a href=\"(.*)\">.*?.*?<\/a>";
	my @links = $html_contents =~ /$pattern/gi;

	foreach my $link (@links) # $links
    {
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

    my $HAVE_WGET = 0;

	# 저장할 위치 지정
    $filename_p = $directory_name . "/" . $filename_p; 

    # 위치를 고정하여 저장한다. .. 파일 보기가 편해서...
	#$filename_p = "dcmon/temp/" . $filename_p; 

    if ($HAVE_WGET eq 1)
    {
        my $cmd_wget = "wget \"$link\"";
        print "Execute $cmd_wget\n";

        # download with wget
        system($cmd_wget);
    }
    else
    {
        #
        my $image = get($link);

        if (defined $image)
        {
            open(OUT, ">$filename_p");
            binmode OUT;
            print OUT $image;
            close(OUT); 
        }
    }

    my $filesize = -s $filename_p if -e $filename_p;
    print " + $directory_name/$filename_p($filesize Bytes)\n" if $opt{debug};
}


sub setup_directory
{
	my ($gallery_name, $end) = @_;
	my $dcmon_dir = "dcmon";
	$directory_name =  $dcmon_dir . "/" . $gallery_name;

	if (-d $dcmon_dir)
	{
		print "$gallery_name Directory already exists.\n" if $opt{debug};
	}
	else
	{
		print "Make directory $dcmon_dir.\n" if $opt{debug};
		mkdir($dcmon_dir);
	}

	unless (-d $directory_name)
	{
		print "Make directory $directory_name.\n" if $opt{debug};
		mkdir($directory_name);
	}
	else
	{
		print "$directory_name Directory already exists\n" if $opt{debug};
	}
	print "set up directory for $directory_name is finished.\n" if $opt{debug};
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
	my $prev_no = -1;
    my $no_index = -1;
	my @prev_list = ();

	# to print in status subroutine
	$statistic{$gallery_name} = 0;
	my $image_count = 0;


	while(1)
	{
	    my $image_count = 0;
		my @new_list = get_recent_number_list($gallery_name); 

		print "[$gallery_name] Article List : \n" if $opt{debug};

		if (@new_list){ foreach my $i (@new_list[0..6]) { print " $i "; } print "\n";}
		if (@prev_list){ foreach my $i (@prev_list[0..6]) { print " $i "; } print "\n";}

		# MRU 판단
		if ($no_index == -1)
		{ 
			$no_index = determine_most_recent_page_number(\@new_list, \@prev_list);
			@prev_list = @new_list;

			if ($no_index != -1) 
			{
				print "[$gallery_name] New article : $new_list[$no_index]\n" if $opt{debug};
			}
			else
			{
                #print "[$gallery_name] No new article. wait more...\n" if $opt{debug};
                #print "peeping at $gallery_name...\n" if $opt{debug};

				sleep( 5 + int(rand(15)));  # sleep time 5 ~ 20 sec
			} 
			next;
		} 

		if (($prev_no != $new_list[$no_index]) and ($no_index != -1))
		{
			print "[$gallery_name] get a web page : $new_list[$no_index]\n" if $opt{debug}; 

            my $url = get_dcinside_address($gallery_name);
			$url =  $url . "&no=" . $new_list[$no_index] . "&page=1";

			# save images and add to count
			$image_count = find_and_get_images($url);
			$prev_no = $new_list[$no_index]; 
		}

		# sleep between 3 ~ 11 seconds
		my $sleep_time = 3 + int(rand(8));
		
#	if ($image_count > 0)
#	{
#		$statistic{$gallery_name} += $image_count;
#		print "|$gallery_name]\t\t" . "#" x $image_count . "\tTotal : $statistic{$gallery_name}\n";
#		print " : $gallery_name/$new_list[$no_index]:" . "+" x $image_count . "\n";
#	}
#
#    $image_count = 0;   # reset

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
	my $html_contents = get_html_contents($html_url);
    #print $html_contents;

    #
	#$html_contents = "<a href=/board/view/?id=game_classic&no=412061&page=1&bbs=";
	# (jpg|~~~)*?은 확장자가 없어도 이름 추출이 가능함 "99aa0--a"
    # scrap을 사용하는 것이 좀 더 깨끗해질 것!
	my $pattern = "id=" . $gallery_name . "&no=(\\d+)&page=\\d+";#/.*?<\/a>";
	my @list = $response->decoded_content =~ /$pattern/gi;

    #print @list;
    #foreach my $i (@list) { print "$i " if $opt{debug}; } print "\n";

	return @list;
}



sub determine_most_recent_page_number
{
	# reference of list
	my ($no_list, $prev_no_list) = @_;
	my $mru_index = -1;

    #print "MRU @{$no_list}, @{$prev_no_list}\n";
	#print scalar(@{$prev_no_list});
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
