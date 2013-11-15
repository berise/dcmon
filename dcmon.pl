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
#use WWW::Mechanize::Firefox;

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

# tests
test_1114();
exit;


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
    $url =  $url . "&no=218920&page=1";

    # save images and add to count
    $image_count = save_images($url);

    if ($image_count > 0)
    {
        $statistic{$gallery_name} += $image_count;
        print "|$gallery_name]\t\t" . "#" x $image_count . "\tTotal : $statistic{$gallery_name}\n";
        print " : $gallery_name/218920:" . "+" x $image_count . "\n";
    }


}



&show_usage;
&run_dcmon_with_cfg();

sub run_dcmon_with_cfg()
{



	open(CFG_IN, "<$CFG_DCMON");
	my @lines = <CFG_IN>;
	close(CFG_IN); 

	foreach my $gallery (@lines)
	{
        next if $gallery =~ /^#/;
		chomp $gallery;
		#print $gallery;
		&run_dcmon_with_list($gallery);
	}

}



sub run_dcmon_with_list()
{
	my $gallery_name = shift;
#	for my $i (@gall_list)
	{
		print "Monitoring $gallery_name\n"; 

		# run this script
		my $pid = fork(); 
		if ($pid == 0)
		{
			&run_dcmon_with_given_name($gallery_name);
			exit;
		} 
	}
}


# run dcmon with given name
sub run_dcmon_with_given_name()
{
	my $gallery_name = shift;

	#print $gallery_name;
	&setup_directory($gallery_name);

	# monitor and get
	&monitor_and_get($gallery_name);
}


sub run_dcmon()
{
	my $gallery_name = &process_arguments; 

	&setup_directory($gallery_name);

	# monitor and get
	&monitor_and_get($gallery_name);
}

sub doit()
{ 
	my ($gallery_name, $page_from, $page_to) = @_;
	foreach my $page ($page_from .. $page_to)
	{
		my $url = "http://gall.dcinside.com/list.php?id=" . $gallery_name . "&no=" . $page . "&page=1";

		print "$url\n";
		&save_images($url);
	} 
}

sub process_arguments()
{
	if ( $#ARGV == 0 )
	{
		$gallery_name = $ARGV[0];

		return $gallery_name;
#	print "$gallery_name, $page_from, $page_to";

#&doit($gallery_name, $page_from, $page_to);

	}
	else
	{
		&show_usage;
	}
}

sub show_usage()
{
	print "dcmon: A small utility to monitor your favorite galleries.\n";
	print "       Edit dcmon.cfg and run\n";
	print "       by behemoth\@beneath.bastion\n\n";
#	exit;
}




# crawl given page
# TI : size of array
sub save_images
{
	my $url = shift;
#$html_contents = &get_html_contents("http://gall.dcinside.com/list.php?id=game_classic&no=409129&page=1");
	my $html_contents = &get_html_contents($url);

	my @filenames =  extract_filenames($html_contents);
	my @links =  &extract_links($html_contents);

	my $file_count = @filenames;
	my $link_count = @links;
	my $image_count = 0;

	print "# of files : ($file_count), # of links : ($link_count)\n" if $opt{debug};
	foreach my $i (0 .. $#filenames)
	{
    	my $filename_p = encode('cp949', $filenames[$i]);
        print " - download $filename_p\n";
		$image_count +=  serialize($filenames[$i], $links[$i]);
	}

	return $image_count;
}
	

sub get_html_contents()
{
	my $url = shift;

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


sub extract_links()
{
	my $html_contents = shift;

    #my $pattern = "src='(http://dcimg1.dcinside.com/viewimage.php?.*?)'";
	my $pattern = "<li class=\"icon_pic\"><a href=\"(.*)\">.*?.*?<\/a>";
	my @links = $html_contents =~ /$pattern/gi;

	foreach my $link (@links) { print "extract_links : @links\n" if $opt{debug}; } # $links

	return @links;
}


#
# Windows XP������ cp949�� ��ȯ�ؾ� �ܼ�â���� �ѱ��� ���δ�.
# Vista/7������ utf-8�� �ᵵ ������ ��...
sub serialize
{
	my ($filename, $link) = @_;
	my $filename_p = encode('cp949', $filename);

	print "Save $filename_p in $directory_name\n" if $opt{debug};

	# ������ ��ġ ����
    $filename_p = $directory_name . "/" . $filename_p; 

    # ��ġ�� �����Ͽ� �����Ѵ�. .. ���� ���Ⱑ ���ؼ�...
	#$filename_p = "dcmon/temp/" . $filename_p; 

	my $image = &get_html_contents($link);

	if (defined $image)
	{
		open(OUT, ">$filename_p");
		binmode OUT;
		print OUT $image;
		close(OUT); 

		print "$filename_p(" . (length($image)) . ")is saved\n\n" if $opt{debug};
		return 1;
	}

	return 0;
}


sub setup_directory()
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

sub monitor_and_get()
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
		my @new_list = &get_recent_number_list($gallery_name); 

		if (@new_list){ foreach my $i (@new_list[0..6]) { print "$i "; } }
		print "\n";
		if (@prev_list){ foreach my $i (@prev_list[0..6]) { print "$i "; } }
		print "\n"; 

		# MRU �Ǵ�
		if ($no_index == -1)
		{ 
			print "[$gallery_name] compare article numbers to get MRU...\n" if $opt{debug};
			$no_index = &determine_most_recent_page_number(\@new_list, \@prev_list);
			@prev_list = @new_list;

			if ($no_index != -1) 
			{
				print "[$gallery_name] New article page no: $no_index\n" if $opt{debug};
			}
			else
			{
				print "[$gallery_name] No new article. wait more...\n" if $opt{debug};
                print "peeping at $gallery_name...\n" if $opt{debug};
				sleep(5);
			} 
			next;
		} 

		if (($prev_no != $new_list[$no_index]) and ($no_index != -1))
		{
			print "[$gallery_name] fetch a page : $new_list[$no_index]\n" if $opt{debug}; 

            my $url = get_dcinside_address($gallery_name);
			$url =  $url . "&no=" . $new_list[$no_index] . "&page=1";

			# save images and add to count
			$image_count = save_images($url);
			$prev_no = $new_list[$no_index]; 
		}

		# sleep between 3 ~ 11 seconds
		my $sleep_time = 3 + int(rand(8));
		
		if ($image_count > 0)
		{
			$statistic{$gallery_name} += $image_count;
			print "|$gallery_name]\t\t" . "#" x $image_count . "\tTotal : $statistic{$gallery_name}\n";
			print " : $gallery_name/$new_list[$no_index]:" . "+" x $image_count . "\n";
		}

        $image_count = 0;   # reset

		sleep($sleep_time); 
	}
}

sub get_recent_number_list()
{
	my $gallery_name = shift;
    my $html_url;

    # dcinside�� ������ �̵��� ����
    $html_url = get_dcinside_address($gallery_name);
    print $html_url if $opt{debug};

    my $mech = WWW::Mechanize->new();

    #$mech->agent_alias('Windows Mozilla');

    my $response = $mech->get($html_url);

    if ($mech->success()) {
        #print "[Mechanize] success\n";
    }
    else {
        print STDERR $response->status_line, "\n";
    }
	my $html_contents = &get_html_contents($html_url);
    #print $html_contents;

    #
	#$html_contents = "<a href=/board/view/?id=game_classic&no=412061&page=1&bbs=";
	# (jpg|~~~)*?�� Ȯ���ڰ� ��� �̸� ������ ������ "99aa0--a"
    # scrap�� ����ϴ� ���� �� �� �������� ��!
	my $pattern = "id=" . $gallery_name . "&no=(\\d+)&page=\\d+";#/.*?<\/a>";
	my @list = $response->decoded_content =~ /$pattern/gi;

    #print @list;
    #foreach my $i (@list) { print "$i " if $opt{debug}; } print "\n";

	return @list;
}



sub determine_most_recent_page_number()
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
