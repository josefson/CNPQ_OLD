"""This file is responsible for fixing the input file in case of software
errors. It will search which short_ids already were processed and had their
respective zml downloaded. Then it will remove them from the input file."""
import argparse
import glob


def downloaded_long_ids():
    """Returns a list of all xmls already dopwnloaded(longid)."""
    downloaded_files = glob.glob('xmls/*zip')
    long_ids = []
    for download in downloaded_files:
        long_ids.append(download[5:21])
    return long_ids


def downloaded_short_ids(long_ids_file):
    """Returns a list of tuples where 1st element is short_id and 2nd element
    is long_id."""
    long_ids_downloaded = downloaded_long_ids()
    matches = []
    with open(long_ids_file, 'r') as l_file:
        for line in l_file:
            for long_id in long_ids_downloaded:
                search = line.find(long_id)
                if search != -1:
                    temp = (line[:10], long_id)
                    matches.append(temp)
    l_file.close()
    return matches


def clean_short_ids_file(downloaded_tuples, short_ids_file):
    """This will clean the short_ids_file removing all short_id that already
    had its xml downloaded."""
    short_ids = []
    with open(short_ids_file, 'r') as s_file:
        for line in s_file:
            short_ids.append(line[:10])
    s_file.close()
    with open(short_ids_file, 'w') as s_file:
        for short_id in short_ids:
            search = [item for item in downloaded_tuples
                      if item[0] == short_id]
            if search == []:
                s_file.write(short_id + '\n')
    s_file.close()


def main(i_file, o_file):
    """This control the workflow."""
    downloaded_tuples = downloaded_short_ids(o_file)
    clean_short_ids_file(downloaded_tuples, i_file)


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('-i', '--input', dest='short_id_file', required=True,
                        type=str, help='Required: A input file filled with '
                        'short_ids separated by new-line-characters.')
    PARSER.add_argument('-o', '--output', dest='long_id_file', required=True,
                        type=str, help='Required: A output file writen '
                        'with long_ids.')
    ARGS = PARSER.parse_args()
    main(ARGS.short_id_file, ARGS.long_id_file)
