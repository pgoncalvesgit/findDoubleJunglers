from riotwatcher import LolWatcher, ApiError
import pandas as pd
import requests
import time

matches_checked_file_name = "matches_verified.txt"
summoner_names_to_check_file_name = "summoner_names.txt"
summoner_names_checked = "summoner_names_checked.txt"
summoner_names_to_initialize_file_name = "summoner_names_initialize.txt"
double_junglers_file_name = "double_junglers.txt"
four_junglers_matches_file_name = "four_junglers_matches.txt"
last_100_summoners_checked = "last_100_summoner_names_checked.txt"


def game_has_n_or_more_junglers(match_detail, number_of_junglers):
    counter = 0
    for row in match_detail['participants']:
        if row['spell1Id'] == 11 or row['spell2Id'] == 11:
            counter = counter + 1
    if counter >= number_of_junglers:
        return True
    else:
        return False


def was_match_already_checked(match_id):
    with open(matches_checked_file_name, "r") as file_reader:
        match_ids = file_reader.readlines()
        for match in match_ids:
            if match.strip() == match_id:
                return True
        return False


def return_list_lines_from_file(file_name):
    try:
        with open(file_name, "r") as file_reader:
            return file_reader.readlines()
    except FileNotFoundError:
        with open(file_name, "w"):
            return list()


def get_summoner_names_to_search():
    return return_list_lines_from_file(summoner_names_to_check_file_name)


def get_summoner_names_to_initialize():
    return return_list_lines_from_file(summoner_names_to_initialize_file_name)


def get_junglers(current_summoner_name, matches):
    junglers = list()
    for match in matches:
        for row in match['participants']:
            if (row['spell1Id'] == 11 or row['spell2Id'] == 11) and current_summoner_name != row:
                for summoner in match['participantIdentities']:
                    if summoner["participantId"] == row['participantId']:
                        junglers.append(summoner["player"]["summonerName"])
    return junglers


def remove_duplicate_summoners(summoners):
    filtred_summoners = list()
    try:
        with open(last_100_summoners_checked, "r") as file_reader:
            summoners = file_reader.readlines()
            for summoner in summoners:
                if summoner not in summoners:
                    filtred_summoners.append(summoner)
    except FileNotFoundError:
        open(last_100_summoners_checked, "w")
    return filtred_summoners


def add_junglers_to_summoner_list(summoners, junglers):
    for jungler in junglers:
        if jungler not in summoners:
            summoners.append(jungler)


def add_line_if_not_in_file(line, file_name):
    add = True
    try:
        with open(file_name, "r") as file_reader:
            for line_already_written in file_reader.readlines():
                if line_already_written.strip() == line:
                    add = False
                    break
    except FileNotFoundError:
        open(file_name, "w")

    if add:
        with open(file_name, "a") as file_writer:
            file_writer.write(line + "\n")


def add_special_game(match):
    add_line_if_not_in_file(match, four_junglers_matches_file_name)


def add_double_jungler_to_list(summoner):
    add_line_if_not_in_file(summoner, double_junglers_file_name)


def add_match_to_list(matchId):
    try:
        with open(matches_checked_file_name, "r") as file_reader:
            for line in file_reader.readlines():
                if line.strip() == str(matchId):
                    return
    except FileNotFoundError:
        open(matches_checked_file_name, "w")
    with open(matches_checked_file_name, "a") as file_writer:
        file_writer.write(str(matchId) + "\n")


def add_summoner_to_100_list(summoner):
    with open(last_100_summoners_checked, "r") as file_reader:
        summoner_names = file_reader.readlines()
        if len(summoner_names) >= 100:
            summoner_names = summoner_names[1::]
    with open(last_100_summoners_checked, "w") as file_writer:
        for summoner_name in summoner_names:
            if summoner_name != "" and summoner_name != "\n":
                file_writer.write(summoner_name)
        if summoner != "" and summoner != "\n":
            file_writer.write(str(summoner) + "\n")


def update_summoners_to_search(summoner_names_to_update):
    try:
        with open(summoner_names_to_check_file_name, "r") as file_reader:
            summoner_names = file_reader.readlines()
            summoner_names = summoner_names[1::]
    except FileNotFoundError:
        open(summoner_names_checked, "w")
        summoner_names = list()
    with open(summoner_names_to_check_file_name, "w") as file_writer:
        for summoner_id in summoner_names:
            if summoner_id != "" and summoner_id != "\n":
                file_writer.write(summoner_id)
        for summoner in summoner_names_to_update:
            add = True
            for summoner_saved in summoner_names:
                if summoner == summoner_saved.strip():
                    add = False
                    break
            if add:
                if summoner != "" and summoner != "\n":
                    file_writer.write(str(summoner.strip()) + "\n")


def update_lists(current_summoner, summoner_names_yet_to_search):
    summoner_names_yet_to_search.pop(0)
    add_summoner_to_100_list(current_summoner)
    update_summoners_to_search(summoner_names_yet_to_search)

def main():
    summoner_names_yet_to_search = get_summoner_names_to_search()
    if len(summoner_names_yet_to_search) == 0:
        summoner_names_yet_to_search = get_summoner_names_to_initialize()

    # api_key = "RGAPI-b47d9212-27c7-4d69-ae35-31418904a49e"
    api_key = "RGAPI-6b7e4ece-dd4c-49cc-8cef-01f24237459b"
    watcher = LolWatcher(api_key)
    my_region = 'euw1'

    counter = 0
    while len(summoner_names_yet_to_search) > 0 and counter < 100:
        counter = counter + 1
        try:
            summoner = watcher.summoner.by_name(my_region, summoner_names_yet_to_search[0].strip())
        except requests.exceptions.HTTPError as err:
            if err.errno == 429:
                print("too many requests... sleeping")
                time.sleep(1)
            else:
                print(err)
        print(summoner_names_yet_to_search[0].strip())
        current_matches = watcher.match.matchlist_by_account(
            my_region, summoner['accountId'],
            begin_index=0, end_index=50,
            queue={"440", "400"}
        )

        filtered_matches = list()
        filtered_matches_details = list()
        for match in current_matches['matches']:
            match_detail = watcher.match.by_id(my_region, match['gameId'])
            #erro 504 - Gateway Timeout

            add_match_to_list(match['gameId'])
            if game_has_n_or_more_junglers(match_detail, 3):
                if not was_match_already_checked(match_detail['gameId']):
                    filtered_matches.append(match)
                    filtered_matches_details.append(match_detail)
                elif game_has_n_or_more_junglers(match_detail, 4):
                    add_special_game(match)
                add_double_jungler_to_list(summoner['name'])

        junglers = get_junglers(summoner['name'], filtered_matches_details)
        remove_duplicate_summoners(junglers)
        add_junglers_to_summoner_list(summoner_names_yet_to_search, junglers)
        update_lists(summoner['name'], summoner_names_yet_to_search)

        '''
        participants = []
        for row in match_detail['participants']:
            row

        participants = []
        for row in match_detail['participants']:
            participants_row = {}
            participants_row['champion'] = row['championId']
            participants_row['spell1'] = row['spell1Id']
            participants_row['spell2'] = row['spell2Id']
            participants_row['win'] = row['stats']['win']
            participants_row['kills'] = row['stats']['kills']
            participants_row['deaths'] = row['stats']['deaths']
            participants_row['assists'] = row['stats']['assists']
            participants_row['totalDamageDealt'] = row['stats']['totalDamageDealt']
            participants_row['goldEarned'] = row['stats']['goldEarned']
            participants_row['champLevel'] = row['stats']['champLevel']
            participants_row['totalMinionsKilled'] = row['stats']['totalMinionsKilled']
            participants_row['item0'] = row['stats']['item0']
            participants_row['item1'] = row['stats']['item1']
            participants.append(participants_row)
        df = pd.DataFrame(participants)

        participants = []
        df = pd.DataFrame(participants)

        # check league's latest version
        latest = watcher.data_dragon.versions_for_region(my_region)['n']['champion']
        # Lets get some champions static information
        static_champ_list = watcher.data_dragon.champions(latest, False, 'en_US')

        # champ static list data to dict for looking up
        champ_dict = {}
        for key in static_champ_list['data']:
            row = static_champ_list['data'][key]
            champ_dict[row['key']] = row['id']
        for row in participants:
            print(str(row['champion']) + ' ' + champ_dict[str(row['champion'])])
            row['championName'] = champ_dict[str(row['champion'])]

        # print dataframe
        df = pd.DataFrame(participants)
        '''


main()
