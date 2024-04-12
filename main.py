# TODO Maybe make the auto caching on timesum command only cache until player argument is found

import requests
import datetime
import time as gettime
import os
import sys
import math
import json
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.messages = True
#client = discord.Client(intents=intents)
client = commands.Bot(command_prefix="!", intents=intents)
client.remove_command("help")

ownerID = 123456789 # YOUR DISCORD USER ID HERE

archiveFolder = "./archive"

# We ignore players who have cheated runs
blacklistedPlayers = ["xbyb", "iiTSTXx", "victorCHEATS", "WorksForMe", "V1t4m1nA"]

currentlyCaching = False
cachedParkourNameList = []
cachedParkourResponsesList = []
cachedParkourPlayerTimesDict = dict()
cachedPlayerRankings = dict()
maxParkourNameLength = 0

noCacheMsg = "No cache, do !reloadcache"

def calculate_player_rankings():
    for response in cachedParkourResponsesList:
        parkourName = response.json()["props"]["sortBy"]

        leaderboardPos = 0
        for entry in response.json()["props"]["stats"]:
            playerName = entry["name"]

            if playerName in blacklistedPlayers:
                continue
#            entryTime = entry[parkourName]

            try:
                if not cachedPlayerRankings[playerName]:
                    cachedPlayerRankings[playerName] = 0
            except:
                cachedPlayerRankings[playerName] = 0

            cachedPlayerRankings[playerName] += (100 - leaderboardPos) / len(cachedParkourNameList)

            leaderboardPos += 1

def arg_is_unsafe(arg):
    allowedChars = "abcdefghijklmnopqrstuvwxyz0123456789_"
    for c in arg:
        if c.lower() not in allowedChars:
            return True

    return False

def get_next_archive_filename():
    maxNum = 0

    for filename in os.listdir(archiveFolder):
        if not filename.endswith(".json"):
            continue

        num = int(filename[20:-5])
        if num > maxNum:
            maxNum = num

    return "leaderboard_archive_" + str(maxNum + 1) + ".json"

def write_cached_parkour_player_times(filename):
    global cachedParkourPlayerTimesDict

    f = open(archiveFolder + "/" + filename, "w+")

    f.write("{\n")
    f.write("\t\"stats\": [\n")

    consecutiveThing = False
    for playerName, times in cachedParkourPlayerTimesDict.items():
#        f.write("\t\t{\n")
        if consecutiveThing:
            f.write(",\n\t\t{")
        else:
            f.write("\t\t{")

#        f.write("\t\t\t\"name\": \"" + playerName + "\",\n")
        f.write("\n\t\t\t\"name\": \"" + playerName + "\"")
        for parkourName, time in times.items():
            if time is not None:
#                f.write("\t\t\t\"" + parkourName + "\": " + str(time) + ",\n")
                f.write(",\n\t\t\t\"" + parkourName + "\": " + str(time))
            else:
#                f.write("\t\t\t\"" + parkourName + "\": null,\n")
                f.write(",\n\t\t\t\"" + parkourName + "\": null")

#        f.write("\t\t},\n")
        f.write("\n\t\t}")
        consecutiveThing = True

#    f.write("\t],\n")
    f.write("\n\t],\n")
    f.write("\n")
    f.write("\t\"date\": \"" + datetime.datetime.now().strftime("%Y %m %d %H:%M:%S") + "\"\n")
    f.write("}")

    f.close()

def ms_to_timestr(num):
    mins = math.floor((num/1000 / 60) % 60)
    secs = (num/1000) - mins*60
    return str(mins) + ":" + str(secs)[:6]

def ms_to_timestr_with_hours(num):
    seconds = int((num/1000) % 60)
    minutes = int((num / (1000*60)) % 60)
    hours = int((num / (1000*60*60)))

    return str(hours) + "h" + str(minutes) + "m" + str(seconds) + "s"

def leaderboard_api_request(parkourName = "biomes"):
    parkourName = parkourName.lower()

    headers = {
        'Accept': 'text/html, application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.5',
        'X-Requested-With': 'XMLHttpRequest',
        'X-Inertia': 'true',
        'X-Inertia-Version': 'fcd6d6cb22ff08b4878d81f08aa9dd4d',
        'Content-Type': 'application/json',
    }

    params = {
        "sortBy": parkourName
    }

    response = requests.get("https://stats.happy-hg.com/parkour", params=params, headers=headers)

    if response.status_code != 200:
        return

    return response

def get_top10_for_parkour(parkourName):
    response = leaderboard_api_request(parkourName)

    entryList = []

    i = 0
    try:
        for entry in response.json()["props"]["stats"]:
            i += 1

            entryList.append([entry["name"], entry[parkourName.lower()]])

            if (i >= 10):
                break
    except KeyError:
        return entryList

    return entryList

def get_time_sum_for_player(playerName):
    global cachedParkourPlayerTimesDict

    if not cachedParkourPlayerTimesDict:
        return -1

    try:
        if not cachedParkourPlayerTimesDict[playerName.lower()]:
            return 0
    except KeyError:
        return 0

    timeSum = 0

    for parkour, time in cachedParkourPlayerTimesDict[playerName.lower()].items():
        if time is not None:
            timeSum += time

    return timeSum

def get_wr_count_for_player(playerName):
    wrCount = 0
    parkourNames = []
    for response in cachedParkourResponsesList:
        parkourName = response.json()["props"]["sortBy"]

        try:
            if response.json()["props"]["stats"][0]["name"].lower() == playerName.lower():
                wrCount += 1
                parkourNames.append(parkourName)
        except IndexError:
            continue

    return (wrCount, parkourNames)

def get_top_wr_count_holders():
    wrCounts = dict()

    for response in cachedParkourResponsesList:
        try:
            wrHolderName = response.json()["props"]["stats"][0]["name"]

            realWrOffset = 0
            while wrHolderName in blacklistedPlayers:
                realWrOffset += 1
                wrHolderName = response.json()["props"]["stats"][realWrOffset]["name"]

            try:
                if not wrCounts[wrHolderName]:
                    wrCounts[wrHolderName] = 0
            except KeyError: # bruh
                wrCounts[wrHolderName] = 0
            wrCounts[wrHolderName] += 1
        except IndexError:
            continue

    return dict(sorted(wrCounts.items(), key = lambda item: item[1], reverse=True))

@client.event
async def on_ready():
    print("\033[0;32mConnected\033[0m")

#@client.event
#async def on_message(msg):
#        if msg.author == client.user:
#            return

#        await client.process_commands(msg)

#        if "western" in msg.content.lower():
#            await msg.channel.send("its the painting in either corner")

@client.command()
async def reloadcache(ctx):
    global currentlyCaching

    if not currentlyCaching:
        await ctx.send("Now caching, this will take 2-4 minutes")

    start = gettime.time()
#    reloaded = reload_cache()

    if currentlyCaching:
        await ctx.send("Already caching...")
#        return False

    currentlyCaching = True

#    start = gettime.time()

    global cachedParkourNameList
    global cachedParkourResponsesList
    global cachedParkourPlayerTimesDict
    global maxParkourNameLength

    maxParkourNameLength = 0
    cachedParkourNameList = []

    sys.stdout.write("Caching parkour name list...")
    response = leaderboard_api_request()
    for num, pkName in response.json()["props"]["columns"].items():
        cachedParkourNameList.append(pkName)
        if len(pkName) > maxParkourNameLength:
            maxParkourNameLength = len(pkName)
    print(" \033[0;32mDone\033[0m")

    sys.stdout.write("Caching all parkour leaderboards...")

    cachedParkourResponsesList = []
    cachedParkourPlayerTimesDict = dict()

    i = 0
    for parkourName in cachedParkourNameList:
        response = leaderboard_api_request(parkourName)

        if not response:
            print("\nAPI Request failed for parkourName " + parkourName)
            continue

        cachedParkourResponsesList.append(response)

        for player in response.json()["props"]["stats"]:
            playerTimes = dict()

            for pkName, time in player.items():
                if pkName in ["uuid", "name"]:
                    continue

                if pkName not in playerTimes:
                    playerTimes[pkName] = time

            if player["name"].lower() not in cachedParkourPlayerTimesDict:
                cachedParkourPlayerTimesDict[player["name"].lower()] = playerTimes

        i += 1
        sys.stdout.write("\rCaching all parkour leaderboards... \033[0;34m[\033[0;32m" + str(i) + "\033[0m/\033[0;32m" + str(len(cachedParkourNameList)) + "\033[0;34m] \033[0;32m" + str(int(i / len(cachedParkourNameList) * 100)) + "\033[0m%\033[0;36m " + parkourName + "\033[0m" + ((maxParkourNameLength - len(parkourName)) * " "))
#        print("Cached " + parkourName + "\t[" + str(i) + "/" + str(len(cachedParkourNameList)) + "]")

    print("\nDone")


    filename = get_next_archive_filename()
    sys.stdout.write("Archiving to file: \033[0;36m" + filename + "\033[0m ...")
    write_cached_parkour_player_times(filename)
    print(" \033[0;32mDone\033[0m")

    print("Removing blacklisted players from cache...")
#    for i in range(len(cachedParkourResponsesList)):
#        delete = False
#        for entry in cachedParkourResponsesList[i].json()["props"]["stats"]:
#            if entry["name"] in blacklistedPlayers:
#                delete = True
#
#        if delete:
#            del cachedParkourResponsesList[i].json()["props"]["stats"]

    for playerName in blacklistedPlayers:
        try:
            del cachedParkourPlayerTimesDict[playerName]
        except:
            pass
    print("Done")

    calculate_player_rankings()

    currentlyCaching = False

    await ctx.send("Cache reload completed in `" + str(int(gettime.time() - start)) + "s`\nParkour count: `" + str(len(cachedParkourNameList)) + "`\nUnique players: `" + str(len(cachedParkourPlayerTimesDict)) + "`\n")

@client.command()
async def top10(ctx, parkourName):
    if len(parkourName) > 20:
        await ctx.send("Invalid parkour name")
        return

    if arg_is_unsafe(parkourName):
        await ctx.send("Invalid parkour name")
        return

    topTimes = get_top10_for_parkour(parkourName)
    if topTimes == []:
        await ctx.send("No times found for parkour " + parkourName)
        return

    maxNameLength = 0
    for name in topTimes:
        if len(name[0]) > maxNameLength:
            maxNameLength = len(name[0])

    msgToSend = ""
    for i in topTimes:
        msgToSend += i[0] + (maxNameLength - len(i[0])) * " " + " | " + ms_to_timestr(i[1]) + "\n"
    await ctx.send("```" + msgToSend + "```")

@client.command()
async def timesum(ctx, playerName):
    if len(playerName) > 24:
        await ctx.send("Invalid player name")
        return

    if arg_is_unsafe(playerName):
        await ctx.send("Invalid player name")
        return

    timeSum = get_time_sum_for_player(playerName)

    start = gettime.time()
    didCache = False

    if timeSum == -1:
        await ctx.send(noCacheMsg)
        return

    # No cache, need to cache
#    if timeSum == -1:
#        if not currentlyCaching:
#            await ctx.send("The leaderboard needs to be cached, this will take about 2-4 minutes")
#            start = gettime.time()
#            didCache = reload_cache()
#            timeSum = get_time_sum_for_player(playerName)
#        else:
#            await ctx.send("The leaderboard is being cached, try again in a few minutes")

    if timeSum == 0:
        await ctx.send("Player " + playerName + " not found on the leaderboard")
        return

#    if didCache:
#        await ctx.send("Cache reload completed in `" + str(int(gettime.time() - start)) + "s`")
#    await ctx.send("The sum of " + playerName + "'s parkour times is: `" + ms_to_timestr_with_hours(timeSum) + "`")

@client.command()
async def pb(ctx, playerName, parkourName):
    if len(playerName) > 30:
        await ctx.send("Invalid player name")
        return
    if len(parkourName) > 30:
        await ctx.send("Invalid parkour name")
        return

    if arg_is_unsafe(playerName):
        await ctx.send("Invalid player name")
        return
    if arg_is_unsafe(parkourName):
        await ctx.send("Invalid parkour name")
        return

    response = leaderboard_api_request(parkourName)

    if not response:
        await ctx.send("API call failed")
        return

    time = 0

    for player in response.json()["props"]["stats"]:
        if player["name"].lower() == playerName.lower():
            time = player[parkourName.lower()]
            break

    if time == 0:
        await ctx.send("No personal best found")
    else:
        await ctx.send(playerName + "'s personal best on " + parkourName + " is `" + ms_to_timestr(time) + "`")

#@client.command()
#async def top10sum(ctx):
#    

@client.command()
async def top10wr(ctx):
    if not cachedParkourResponsesList:
        await ctx.send(noCacheMsg)
        return

    wrCounts = get_top_wr_count_holders()

    maxNameLength = 0
    i = 0
    for name in wrCounts:
        i += 1
        if len(name) > maxNameLength:
            maxNameLength = len(name)
        if i >= 10:
            break

    msg = "```"
    j = 0
    for wrHolder in wrCounts:
        j += 1
        msg += wrHolder + (maxNameLength - len(wrHolder)) * " " + " | " + str(wrCounts[wrHolder]) + " wrs\n"
        if j >= 10:
            break

    await ctx.send(msg + "```")

@client.command()
async def wrcount(ctx, playerName):
    if len(playerName) > 30:
        await ctx.send("Invalid player name")
        return
    if arg_is_unsafe(playerName):
        await ctx.send("Invalid player name")
        return

    if not cachedParkourResponsesList:
        await ctx.send(noCacheMsg)
        return

    wrCount, pkNames = get_wr_count_for_player(playerName)

    if wrCount < 1:
        await ctx.send(playerName + " has no world records")
    else:
        msg = playerName + " has `" + str(wrCount) + "` world records:\n```"
        i = 0
        for pkName in pkNames:
            i += 1
            msg += pkName + "\n"

            if i > 3:
                msg += "..."
                break
        msg += "```"

        await ctx.send(msg)

@client.command()
async def completion(ctx, playerName):
    if not cachedParkourPlayerTimesDict:
        await ctx.send(noCacheMsg)
        return

    try:
        if not cachedParkourPlayerTimesDict[playerName]:
            await ctx.send("Could not find player")
            return
    except IndexError:
        await ctx.send("Could not find player")
        return

    completionCount = 0
    for parkourName, time in cachedParkourPlayerTimesDict[playerName].items():
        if time > 0:
            completionCount += 1

    await ctx.send(playerName + " has `[" + str(completionCount) + "/125]` parkours completed with top 100 times")

@client.command()
async def blacklist(ctx):
    msg = "Blacklisted players:\n```"
    for player in blacklistedPlayers:
        msg += '\n' + player

    await ctx.send(msg + "```")

#@client.command()
#async def blacklistadd(ctx, playerName):
#    global ownerID
#
#    if ctx.message.author != ownerID:
#        await ctx.send("You don't have permission to use this command")
#        return
#
#    if playerName:
#        blacklistedPlayers.append(playerName)
#        await ctx.send("Player `" + playerName + "` added to blacklist")
#        return
#
#    await ctx.send("epic fail")

@client.command()
async def ranking(ctx, pageNum=0):
    if not cachedPlayerRankings:
        await ctx.send(noCacheMsg)
        return

    sortedRanking = dict(sorted(cachedPlayerRankings.items(), key = lambda item: item[1], reverse=True))

    msgToSend = "```"

    # TODO change to for i in range with manual indexing to allow for pages

    i = 0
    for playerName, rankValue in sortedRanking.items():
        i += 1
        if i > 10:
            break

        msgToSend += "#" + str(i) + ": " + playerName + " - " + str(rankValue) + "\n"

    await ctx.send(msgToSend + "```")

@client.command()
async def stop(ctx):
    exit()

@client.command()
async def help(ctx):
    helpMsg = "```"
    helpMsg += "!ranking [Optional page #]  - Overall leaderboard approximation NOT FINISHED\n"
    helpMsg += "!top10   [Parkour]          - Top 10 times on a parkour\n"
    helpMsg += "!pb      [Player] [Parkour] - Players personal best on a parkour\n"
    helpMsg += "!top10wr                    - Players with most world records\n"
    helpMsg += "!wrcount [Player]           - Number of world records a player holds\n"
    helpMsg += "!completion [Player]        - Parkour completion count of a player\n"
    helpMsg += "!timesum [Player]           - Sum of a players times\n"
    helpMsg += "!reloadcache                - Re-download the leaderboard\n"
#    helpMsg += "!reloadcache            - Only for the owner of this bot\n"
#    helpMsg += "!stop                   - Only for the owner of this bot\n"
    helpMsg += "!blacklist                  - List all blacklisted players\n"
#    helpMsg += "!blacklistadd [player]       - Add player to blacklist\n"
    helpMsg += "!help                       - You're looking at it\n"
    helpMsg += "```"
    await ctx.send(helpMsg)

client.run("YOUR TOKEN HERE")
