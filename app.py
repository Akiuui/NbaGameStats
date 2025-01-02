from flask import Flask, jsonify, request
from nba_api.stats.endpoints import scoreboardv2, boxscoretraditionalv3
from nba_api.stats.static import teams
# import time
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)  # This prints logs to the console


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
    try:
        scoreboard = scoreboardv2.ScoreboardV2(game_date=date)#First we get the games played based on the date
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
    try:
        boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=ourGameId)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch boxScore: {str(e)}"}), 500
    # print("Boxscore fetch time:", time.time() - start_time)


    playerStats = boxscore.get_data_frames()[0]

    filteredStats = playerStats[["minutes","reboundsTotal", "points", "turnovers", "blocks", "steals", "assists", "teamTricode", "playerSlug"]]

    filteredStatsDict=filteredStats.to_dict(orient="records")

    return jsonify(filteredStatsDict)


if __name__ == '__main__':
    app.run(debug=False)