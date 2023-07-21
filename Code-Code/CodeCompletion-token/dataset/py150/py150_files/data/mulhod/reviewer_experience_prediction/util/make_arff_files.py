"""
:author: Matt Mulholland
:date: April 15, 2015

Script used to generate ARFF files usable in Weka for the video game
review data-sets.
"""
import logging
from os import makedirs
from os.path import (join,
                     isdir,
                     dirname,
                     realpath,
                     splitext)
from argparse import (ArgumentParser,
                      ArgumentDefaultsHelpFormatter)

from src import (log_dir,
                 data_dir,
                 formatter)

# Initialize logging system
logging_info = logging.INFO
logger = logging.getLogger('util.make_arff_files')
logger.setLevel(logging_info)
sh = logging.StreamHandler()
sh.setLevel(logging_info)
sh.setFormatter(formatter)
logger.addHandler(sh)
loginfo = logger.info
logerr = logger.error
logwarn = logger.warning


def main():
    parser = ArgumentParser(usage='python make_arff_files.py --game_files '
                                  'GAME_FILE1,GAME_FILE2[ OPTIONS]',
                            description='Build .arff files for a specific '
                                        'game file, all game files combined, '
                                        'or for each game file separately.',
        formatter_class=ArgumentDefaultsHelpFormatter)
    _add_arg = parser.add_argument
    _add_arg('--game_files',
             help='Comma-separated list of file-names or "all" for all of the'
                  ' files (the game files should reside in the "data" '
                  'directory; the .jsonlines suffix is not necessary, but the'
                  ' file-names should be exact matches otherwise).',
             type=str,
             required=True)
    _add_arg('--output_dir', '-o',
             help='Destination directory for ARFF files.',
             type=str,
             required=True)
    _add_arg('--mode',
             help='Make .arff file for each game file separately ("separate")'
                  ' or for all game files combined ("combined").',
             choices=["separate", "combined"],
             default="combined")
    _add_arg('--combined_file_prefix',
             help='If the "combined" value was passed in via the --mode flag '
                  '(which happens by default unless specified otherwise), an '
                  'output file prefix must be passed in via this option '
                  'flag.',
             type=str,
             required=False)
    _add_arg('--use_original_hours_values',
             help='Use the unmodified hours played values; otherwise, use the'
                  ' collapsed values.',
             action='store_true',
             default=False)
    _add_arg('--use_mongodb',
             help='Search the MongoDB collection for training/test set '
                  'reviews and make ARFF files using them only (the file '
                  'suffix ".train"/".test" will be appended onto the end of '
                  'the output file name to distinguish the different files); '
                  'note that, by default, collapsed hours played values will '
                  'be used (if this is not desired, use the '
                  '--use_original_hours_values flag).',
             action='store_true',
             default=False)
    _add_arg('--nbins',
             help='Specify the number of bins in which to collapse hours '
                  'played values; to be used if the --make_train_test_sets '
                  'flag is not being used, in which case pre-computed hours '
                  'played values will not be read in from the database, but '
                  'you still want the values to be in the form of bins (i.e.,'
                  ' 1 for 0-100, 2 for 101-200, etc., depending on the '
                  'minimum and maximum values and the number of bins '
                  'specified).',
             type=int,
             required=False)
    _add_arg('--bin_factor',
             help='Factor by which to multiply the sizes of the bins, such '
                  'that the bins with lots of values will be smaller and the '
                  'more sparsely-populated bins will be smaller in terms of '
                  'range.',
             type=float,
             default=1.0)
    _add_arg('-dbhost', '--mongodb_host',
             help='Host that the MongoDB server is running on.',
             type=str,
             default='localhost')
    _add_arg('--mongodb_port', '-dbport',
             help='Port that the MongoDB server is running on.',
             type=int,
             default=27017)
    _add_arg('--log_file_path', '-log',
             help='Path for log file.',
             type=str,
             default=join(log_dir, 'replog_make_arff.txt'))
    args = parser.parse_args()

    # Imports
    import os
    from re import sub
    import numpy as np
    from src.mongodb import (connect_to_db,
                             get_game_files)
    from src.datasets import (get_bin_ranges,
                              write_arff_file,
                              get_and_describe_dataset)

    # Make local copies of arguments
    game_files = args.game_files
    output_dir = args.output_dir
    mode = args.mode
    combined_file_prefix = args.combined_file_prefix
    use_mongodb = args.use_mongodb
    nbins = args.nbins
    bins = not args.use_original_hours_values
    bin_factor = args.bin_factor
    mongodb_host = args.mongodb_host
    mongodb_port = args.mongodb_port

    # Make sure log file directory exists
    log_file_path = realpath(args.log_file_path)
    log_file_dir = dirname(log_file_path)
    if not exists(log_file_dir):
        makedirs(log_file_dir, exist_ok=True)

    # Make file handler
    fh = logging.FileHandler(log_file_path)
    fh.setLevel(logging_info)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Check if the output directory exists
    output_dir = realpath(output_dir)
    if not exists(output_dir) and isdir(output_dir):
        msg = ('The given output directory, {0}, for ARFF files does not '
               'exist or is not a directory.'.format(output_dir))
        logerr(msg)
        raise ValueError(msg)

    # Make sure --bins option flag makes sense
    if nbins:
        if use_mongodb:
            msg = ('If the --use_mongodb flag is used, a number of bins in '
                   'which to collapse the hours played values cannot be '
                   'specified (since the values in the database were '
                   'pre-computed).')
            logerr(msg)
            raise ValueError(msg)
        elif not bins:
            msg = ('Conflict between the --use_original_hours_values and '
                   '--nbins flags. Both cannot be used at the same time.')
            logerr(msg)
            raise ValueError(msg)
    elif bins and not use_mongodb:
        msg = ('If both the --use_original_hours_values and --use_mongodb '
               'flags are not used, then the number of bins in which to '
               'collapse the hours played values must be specified via the '
               '--nbins option argument.')
        loginfo(msg)
        raise ValueError(msg)

    # Exit if the --bin_factor argument was used despite the fact that
    # the original hours values are not being binned
    if not bins and bin_factor > 1.0:
        msg = ('The --bin_factor argument was specified despite the fact '
               'that the original hours values are being binned.')
        logerr(msg)
        raise ValueError(msg)

    # Get path to the data directory
    if bins:
        arff_files_dir = join(output_dir, 'arff_files_collapsed_values')
    else:
        arff_files_dir = join(output_dir, 'arff_files_original_values')
    loginfo('data directory: {0}'.format(data_dir))
    loginfo('arff files directory: {0}'.format(output_dir))

    # Make sure there is a combined output file prefix if "combine" is
    # the value passed in via --mode
    if mode == 'combined' and not combined_file_prefix:
        msg = ('A combined output file prefix must be specified in cases '
               'where the "combined" value was passed in via the --mode '
               'option flag (or --mode was not specified, in which case '
               '"combined" is the default value).')
        logerr(msg)
        raise ValueError(msg)

    """
    See if the --use_mongodb flag was used, in which case we have to
    make a connection to the MongoDB collection. And, if it wasn't
    used, then print out warning if the --mongodb_port flag was used
    (since it will be ignored) unless the value is equal to the default
    value (since it probably wasn't specified in that case).
    """
    if use_mongodb:
        loginfo('Connecting to MongoDB database on mongodb://{0}:{1}...'
                .format(mongodb_host, mongodb_port))
        reviewdb = connect_to_db(host=mongodb_host, port=mongodb_port)
    elif (mongodb_port
          and not mongodb_port == 27017):
        logwarn('Ignoring argument passed in via the --mongodb_port/-dbport '
                'option flag since the --use_mongodb flag was not also used, '
                'which means that the MongoDB database is not going to be '
                'used.')

    game_files = get_game_files(game_files)
    if len(game_files) == 1:

        # Print out warning message if --mode was set to "combined" and
        # there was only one file n the list of game files since only a
        # single ARFF file will be created
        if mode == 'combined':
            logwarn('The --mode flag was used with the value "combined" (or '
                    'was unspecified) even though only one game file was '
                    'passed in via the --game_files flag. Only one file will '
                    'be written and it will be named after the game.')
        mode = "separate"

    # Make a list of dicts corresponding to each review and write .arff
    # files
    loginfo('Reading in data from reviews files...')
    if mode == "combined":
        review_dicts_list = []
        if not use_mongodb:
            for game_file in game_files:
                loginfo('Getting review data from {0}...'.format(game_file))
                (review_dicts_list
                 .extend(get_and_describe_dataset(join(data_dir, game_file),
                                                  report=False)))

            # If the hours played values are to be divided into bins,
            # get the range that each bin maps to
            if bins:
                bin_ranges = get_bin_ranges(min([r['total_game_hours'] for r
                                                 in review_dicts_list]),
                                            max([r['total_game_hours'] for r
                                                 in review_dicts_list]),
                                            nbins,
                                            bin_factor)
            else:
                bin_ranges = False
        file_names = [splitext(game)[0] for game in game_files]
        arff_file = join(arff_files_dir, '{0}.arff'.format(combined_file_prefix))
        if use_mongodb:
            loginfo('Generating ARFF files for the combined training sets and'
                    ' the combined test sets, respectively, of the following '
                    'games:\n\n{0}'
                    .format(', '.join([sub(r'_', r' ', fname)
                                       for fname in file_names])))
            write_arff_file(arff_file, file_names, reviewdb=reviewdb,
                            make_train_test=True, bins=True)
        else:
            loginfo('Generating {0}...'.format(arff_file))
            write_arff_file(arff_file,
                            file_names,
                            reviews=review_dicts_list,
                            bins=bin_ranges)
    else:
        for game_file in game_files:
            loginfo('Getting review data from {0}...'.format(game_file))
            if not use_mongodb:
                review_dicts_list = get_and_describe_dataset(join(data_dir,
                                                                  game_file),
                                                             report=False)
                if bins:
                    bin_ranges = get_bin_ranges(min([r['total_game_hours'] for r
                                                     in review_dicts_list]),
                                                max([r['total_game_hours'] for r
                                                     in review_dicts_list]),
                                                nbins,
                                                bin_factor)
                else:
                    bin_ranges = False
            game = splitext(game_file)[0]
            arff_file = join(arff_files_dir, '{0}.arff'.format(game))
            if use_mongodb:
                loginfo('Generating ARFF file for the training and test sets '
                        'for {0}...'.format(game))
                write_arff_file(arff_file,
                                [game],
                                reviewdb=reviewdb,
                                make_train_test=True,
                                bins=bins)
            else:
                loginfo('Generating {0}...'.format(arff_file))
                write_arff_file(arff_file,
                                [game],
                                reviews=review_dicts_list,
                                bins=bin_ranges)
    loginfo('Complete.')


if __name__ == '__main__':
    main()
