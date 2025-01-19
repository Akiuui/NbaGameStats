from flask import Flask, jsonify, request
from nba_api.stats.endpoints import scoreboardv2, boxscoretraditionalv3
from nba_api.stats.static import teams
from flask_cors import CORS
# import time
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)  # This prints logs to the console
CORS(app)


def getTeamIdByAbbr(teamAbbr):
    team = teams.find_team_by_abbreviation(teamAbbr)
    if not team:
        raise ValueError(f"Invalid team abbreviation: {teamAbbr}")
    return team["id"]

def getGameIdByTeam(gamesIds, hometeamsIds, visitorTeamsIds, teamId):
    for i in range(len(gamesIds)):
        if(hometeamsIds[i] == teamId or visitorTeamsIds[i] == teamId):
            return gamesIds[i]
    return None

@app.route('/', methods=['GET'])
def getAll():
    logging.info("Endpoint called")
    #First we get the params we use to query for the games stats
    date = request.args.get('date')
    teamAbbr = request.args.get('teamAbbr')

    logging.info(f"PARAMS: date: {date}, teamAbbr: {teamAbbr}")

    if not date or not teamAbbr:
        logging.error("error: Missing required parameters: 'date' and 'teamAbbr'")
        return jsonify({"error": "Missing required parameters: 'date' and 'teamAbbr'"}), 400

    # start_time = time.time()

    header=  {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.nba.com",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive"
    }

    try:
        scoreboard = scoreboardv2.ScoreboardV2(game_date=date, headers=header)#First we get the games played based on the date
        print("The endpoint: ",scoreboard.get_request_url())
    except Exception as e:
        logging.error("error: Failed to fetch scoreboard")
        return jsonify({"error": f"Failed to fetch scoreboard: {str(e)}"}), 500
    # print("Scoreboard fetch time:", time.time() - start_time)

    #We convert our response to a data fram and get certain colums we need
    df = scoreboard.get_data_frames()[0][["GAME_ID", "HOME_TEAM_ID", "VISITOR_TEAM_ID"]]
    #We convert the data frame into three array for easier use
    gameId = list(df["GAME_ID"])
    visitorTeamId = list(df["HOME_TEAM_ID"])
    homeTeamId = list(df["VISITOR_TEAM_ID"])

    #We get the id of our inputed param teamAbbbr
    teamId=getTeamIdByAbbr(teamAbbr=teamAbbr)
    ourGameId = getGameIdByTeam(gamesIds=gameId, hometeamsIds=homeTeamId, visitorTeamsIds=visitorTeamId, teamId=teamId)

    logging.info(f"Our Game Id {ourGameId}")

    if not ourGameId:
        return jsonify({"error": "No game found for the specified team and date"}), 404
    # start_time = time.time()
    # ourGameId = "0021900737"
    try:
        boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=ourGameId)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch boxScore: {str(e)}"}), 500
    # print("Boxscore fetch time:", time.time() - start_time)


    playerStats = boxscore.get_data_frames()[0]

    filteredStats = playerStats[["minutes","reboundsTotal", "points", "turnovers", "blocks", "steals", "assists", "teamTricode", "playerSlug"]]

    filteredStatsDict=filteredStats.to_dict(orient="records")

    return jsonify(filteredStatsDict)

import os

if __name__ == '__main__':
    from waitress import serve

    port=int(os.environ.get("PORT", 8080))
    serve(app, host="0.0.0.0", port=port)
    # app.run(debug=False)