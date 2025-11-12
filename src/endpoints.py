import requests
import pandas as pd

def get_app_list():    
    """
    Returns a list of all steam games and their steam appid
    
    Right now, saves the result as a picklefile
    """
    response = requests.get('https://api.steampowered.com/ISteamApps/GetAppList/v2/')
    if response.status_code != 200:
        print(f'{response.status_code} from GetAppList endpoint. Error: {response.text}')
        return None
        
    # response.json structure:
    # {applist: {apps: [{appid: <appid>, name: <name>}, {appid: <appid>, name: <name>}, ...]}}
    # 276777 apps
    df = pd.DataFrame(response.json()['applist']['apps'])
    
    pickle_filename = 'all_game_ids.pkl'
    df.to_pickle(pickle_filename)
    
    print(f"Saved all games ids as {pickle_filename}")

def get_appid(name, filename):
    """
    Searches steam games by name and returns the appid
    """
    all_games = pd.read_pickle(filename)
    
    return all_games[all_games['name'] == name]['appid'].item()

def get_glob_achievement_percentage(appid):
    """
    Gets percentage of all players to have completed achievements for the game
    """
    response = requests.get(f'http://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/?gameid={appid}&format=json')
    print(f'{response.text}')
    
if __name__=="__main__":
    # get_app_list()
    appid = get_appid('Age of Empires II: Definitive Edition', 'all_game_ids.pkl')
    get_glob_achievement_percentage(appid)
    
    